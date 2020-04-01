from scan_utils import run, scan_reader, generate_output_scan_template_csv, store_result
import csv
import numpy as np
from config_dict import config_dict
from tqdm import tqdm
import multiprocessing as mp
import os


def batch_file_generator(idx, MD1, MDP, MD3, batch_file, calchep_dir, output_events_basis, num_events, local=True):
    """This edits the calchep batchfile (batch_file), ie changing for a specific parameter combo of MD1, MDP, MD3,
    ands about it. You need to specify the parameter values you want, the batch_file which is already created
    and the calchep directory where the batch file will be ran. The batch_file name is outputted which is kind of
    pointless but felt better than returning nothing. Also this way the batch_file name can be passed to next function"""
    path2file = calchep_dir + batch_file
    output_events = output_events_basis + '_' + str(int(idx))
    print(output_events)
    #asserting mass hierarchy of MFDM
    if MD1<MDP<MD3:
        #read in batch file first
        with open(path2file, 'r') as file:
            # read a list of lines into data
            changes = file.readlines()
        # Make changes to the parameter info, which starts at line 11, you also have to add \n at end for it to work
        changes[10] = 'Parameter: MD1 = ' + str(MD1) + '        #line 11' + '\n'
        changes[11] = 'Parameter: MDP = ' + str(MDP) + '        #line 12' + '\n'
        changes[12] = 'Parameter: MD3 = ' + str(MD3) + '        #line 13' + '\n'
        #lets set the number of different events to be generated
        changes[45] = 'Number of events (per run step):  ' + str(num_events) + '      #line 46' + '\n'
        #set name for outgoing events file name
        changes[46] = 'Filename:                        ' + output_events + '       #line 47' +'\n'
        #if being ran not locally, ie, local = False then it is assumed that we can use a lot more cpus
        if local==False:
            changes[55] = 'Max number of cpus:   16' + '        #line 56'+'\n'
        else:
            changes[55] = 'Max number of cpus:   4' + '     #line 56' + '\n'
        # and write everything back
        with open(path2file, 'w') as file:
            file.writelines(changes)
        return output_events, batch_file

    else:
        print('Parameters dont satisfy mass hierarchy, try again!')
        return None


def events_generator(batch_file, calchep_dir, output_events, checkmate_dir):
    """This takes the batch file editted using the above function, runs it in the calchep_dir,
    creating lhe files called output_events + '-single.lhe.gz', these files are then moved to the checkmate_dir.
    This func returns lhe events name, a tad pointless as its just name of events and not events themselves"""
    #next define what events are gunna be called, as well as the dir where lhe files are held
    calchep_results_dir = calchep_dir + 'batch_results'
    lhe_file = output_events + '-single.lhe'
    print('\n\n'+lhe_file+'\n\n')
    #first we need to remove the "lock.batch" file (if it exists) in order to do multiple scans in a row
    run(['rm lock.batch'], cwd =calchep_dir, shell=True)
    #next lets run the batch file and generate the lhe events
    run(['./calchep_batch ' + batch_file], cwd=calchep_dir, shell=True)
    print('\n\nbatch done!!!\n\n')
    #now we unzip the lhe files
    run(['gunzip '+ lhe_file + '.gz'], cwd=calchep_results_dir, shell=True)
    #now we move over the lhe files to the scripting_files folder within checkmate directory
    run(['cp '+ lhe_file + ' ' + checkmate_dir + 'scripting_lhe_events_folder/.'], cwd=calchep_results_dir, shell=True)
    #print('done')
    return lhe_file

    

def collider_single_point_checker(MD1, MDP, MD3, config_dict):
    """This function takes a single parameter point and makes a decision if its allowed by bringing the whole pipeline together:
        1) Creates batch file
        2) Creates lhe events (using Calchep)
        3) Makes a decision on those events (using CHECKmate)
    """
    #0.5) calchep doesnt like it when the deltas are exactly the same as we get tan(2_theta) = 1/0, so we have to add a slight offset
    MDP = MDP + 0.0000001
    MD3 = MD3 + 0.0000002
    # 1)create the batch file (note variable batch_file is just the str of the name of the batch file)
    batch_file = batch_file_generator(MD1, MDP, MD3, config_dict['calchep_batch_file'], config_dict['calchep_dir'], config_dict['calchep_output_events'], config_dict['num_events'], config_dict['local'])
    # 2) Create the lhe files (note variable lhe_file is just the string of the lhe events file name)
    lhe_file = events_generator(config_dict['calchep_batch_file'], config_dict['calchep_dir'], config_dict['calchep_output_events'], config_dict['checkmate_dir'])
    # 3) Make a decision on those events, where result is 1 for being allowed, 0 for not allowed
    result = decision_generator(lhe_file, config_dict['checkmate_dir'], config_dict['checkmate_card_file'])
    return result

def collider_parameter_space_checker(config_dict):
    """This function searches multiple parameter points in the parameter space using the collider_single_point_checker function above,
    it takes the config_dict as the only input. Does not output anything directly but will update the output csv scan and fill it with
    values of whether each point is allowed or not."""
    #first lets generate the output csv file
    generate_output_scan_template_csv(output_csv= config_dict['output_csv_file'], input_csv=config_dict['input_csv_file'], fresh_input=config_dict['fresh_input'], starting_row=config_dict['starting_row'])
    #now lets loop over the different rows containing the parameter points in our input scan csv
    for row in tqdm(scan_reader(input_scan_csv= config_dict['input_csv_file']), total=float( config_dict['points_in_scan'] )):
        #define our masses from our input csv row
        MD1, MDP, MD3 = float(row[1]), float(row[2]), float(row[3])
        #for this single parameter point, calculate if its allowed or not. Result = 1 or allowed, 0 if not allowed
        result = collider_single_point_checker(MD1, MDP, MD3, config_dict)
        #time to store our result
        store_result(input_row=row, output_csv=config_dict['output_csv_file'], **result)
    return None

def all_lhe_events_generator(config_dict):
    print('\n\nGenerating the lhe events using Calchep for all parameter points in scan!!!\n\n')
    for row in tqdm(scan_reader(input_scan_csv= config_dict['input_csv_file']), total=float( config_dict['points_in_scan'] )):
        #define our masses from our input csv row (order of MD3, MDP and MD1 in scan matters!!!!)
        idx, MD3, MDP, MD1 = float(row[0]), float(row[1]), float(row[2]), float(row[3])
        #0.5) calchep doesnt like it when the deltas are exactly the same as we get tan(2_theta) = 1/0, so we have to add a slight offset
        MDP = MDP + 0.0000001
        MD3 = MD3 + 0.0000002
        # 1)create the batch file (note variable batch_file is just the str of the name of the batch file)
        output_events, batch_file = batch_file_generator(idx, MD1, MDP, MD3, config_dict['calchep_batch_file'], config_dict['calchep_dir'], config_dict['calchep_output_events'], config_dict['num_events'], config_dict['local'])
        # 2) Create the lhe files (note variable lhe_file is just the string of the lhe events file name)
        lhe_file = events_generator(config_dict['calchep_batch_file'], config_dict['calchep_dir'], output_events, config_dict['checkmate_dir'])
    print('\n\nDone generating all lhe events for all parameter points in scan!!!\n\n ')
    return None

def decision_generator(idx, row, lhe_file,  checkmate_dir, card_file_template, output_csv_file):
    """This function takes the lhe events generated from the above function and runs them through
    checkmate and gets a decision if they're allowed or not. Outputs 1 if allowed, a zero if not allowed"""
    #lets define some paths our path to our card.dat template and the name of the result file
    path_2_card_template = checkmate_dir + card_file_template
    result_name = 'scripting_checkmate_output' + '_' + str(int(idx))
    #first we need to create the checkmate card, so it refers to right lhe_file name
    with open(path_2_card_template, 'r') as template:
        # read a list of lines into data
        changes = template.readlines()
    #make changes to template 
    changes[3] = 'Name: ' + result_name + '\n'
    changes[14] = 'Events: ' + 'scripting_lhe_events_folder/' + lhe_file + '\n'
    #and then we write it to a new file!!!!
    new_card_file = 'scripting_card_' + str(int(idx)) + '.dat'
    with open(checkmate_dir + 'scripting_card_files_folder/' + new_card_file, 'w') as file:
        file.writelines(changes)
    #time to run checkmate on our new_card_file which refers to our lhe_file
    run(['./CheckMATE ' + 'scripting_card_files_folder/' + new_card_file], cwd = checkmate_dir, shell=True)
    #lets delete the card file and event file to keep things clean
    #run(['rm ' + 'scripting_card_files_folder/' + new_card_file], cwd = checkmate_dir, shell=True)
    #run(['rm ' + 'scripting_lhe_events_folder/' + lhe_file], cwd = checkmate_dir, shell=True)
    #results are held in the following dir, assuming name is unchanged in checkmate card
    result_dir = checkmate_dir[:-4] + 'results/' + result_name + '/result.txt' #its [:-4] to get move out of bin dir
    #time to collect and output result from this result_dir
    with open(result_dir, 'r') as file:
        # just way data is formatted, the result is given by below line
        file = file.readlines()
        r_value = float(file[2].split()[-1])
        analysis = file[3].split()[-1]
        SR = file[4].split()[-1]
        #result is if allowed or not
        if r_value >1:
            result = 0
        else:
            result = 1
    output = {'r_value': r_value, 'analysis': analysis, 'SR': SR, 'LHC': result}
    store_result(input_row=row, output_csv=output_csv_file, **output)   
    return None

def multiprocessing_decision_generator(config_dict):
    print('\n\nLets start the parallel processing of the lhe events using checkmate!!!\n\n')
    pool = mp.Pool(mp.cpu_count())
    lhe_files = os.listdir(config_dict['checkmate_dir'] + 'scripting_lhe_events_folder/.')
    input_scan = scan_reader(config_dict['input_csv_file'])
    checkmate_dir = config_dict['checkmate_dir']
    card_file_template = config_dict['checkmate_card_file']
    output_csv_file = config_dict['output_csv_file']
    #raise error if we dont generate all the lhe files
    if len(lhe_files)!=config_dict['points_in_scan']:
        raise ValueError('Number of lhe files produced does not match number of points in scan!!!')
    #the actual parallel processing...
    for idx, lhe_file in tqdm(enumerate(lhe_files), total=float( config_dict['points_in_scan'])):
        row = next(input_scan)
        pool.apply_async(decision_generator, args=(idx, row, lhe_file,  checkmate_dir, card_file_template, output_csv_file) )
    pool.close()
    pool.join()
    print('\n\nFINISHED!!!\n\n')
    return None

def complete_multiprocessing_pipeline(config_dict):
    #first lets generate the output csv file
    generate_output_scan_template_csv(output_csv= config_dict['output_csv_file'], input_csv=config_dict['input_csv_file'], fresh_input=config_dict['fresh_input'], starting_row=config_dict['starting_row'])
    #now lets generate the lhe files for all the points in the scan
    all_lhe_events_generator(config_dict)
    #lets start the parallel processing of the lhe events using checkmate!!!
    multiprocessing_decision_generator(config_dict)
    return None

if __name__ == '__main__':
    #all_lhe_events_generator(config_dict)
    complete_multiprocessing_pipeline(config_dict)