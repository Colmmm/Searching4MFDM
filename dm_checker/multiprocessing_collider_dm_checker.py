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


def calchep_dir_cleaner(batch_file, calchep_results_dir, output_events):
    """remove the files we dont need from when we run the batch file"""    
    run(['rm ' + output_events + '.tgz'], cwd =calchep_results_dir, shell=True)
    run(['rm ' + output_events + '-single.distr'], cwd =calchep_results_dir, shell=True)
    return None


def events_generator(batch_file, calchep_dir, output_events, checkmate_dir, checkmate_output_name):
    """This takes the batch file editted using the above function, runs it in the calchep_dir,
    creating lhe files called output_events + '-single.lhe.gz', these files are then moved to the checkmate_dir.
    This func returns lhe events name, a tad pointless as its just name of events and not events themselves"""
    #next define what events are gunna be called, as well as the dir where lhe files are held
    calchep_results_dir = calchep_dir + 'batch_results'
    lhe_file = output_events + '-single.lhe'
    lhe_subdir = checkmate_dir + checkmate_output_name + '_lhe_subdir/'
    #first we need to remove the "lock.batch" file (if it exists) in order to do multiple scans in a row
    run(['rm lock.batch'], cwd =calchep_dir, shell=True)
    #next lets run the batch file and generate the lhe events
    run(['./calchep_batch ' + batch_file], cwd=calchep_dir, shell=True)
    #now we unzip the lhe files
    run(['gunzip '+ lhe_file + '.gz'], cwd=calchep_results_dir, shell=True)
    #now we move over the lhe files to the scripting_files folder within checkmate directory
    run(['mv '+ lhe_file + ' ' + lhe_subdir], cwd=calchep_results_dir, shell=True)
    #lets also clean the calchep dir of the other files we dont need that are generated along with the .lhe files
    calchep_dir_cleaner(batch_file, calchep_results_dir, output_events)
    return lhe_file

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
        lhe_file = events_generator(config_dict['calchep_batch_file'], config_dict['calchep_dir'], output_events, config_dict['checkmate_dir'], config_dict['checkmate_output_name'])
    print('\n\nDone generating all lhe events for all parameter points in scan!!!\n\n ')
    return None

def checkmate_card_generator(idx, checkmate_dir, card_file_template, checkmate_output_name, lhe_file, checkmate_result_file_name):
    """we need to create the checkmate card, so that it refers to right lhe_file, do this by editing a template card file.
     This outputs the name of the new_card_file which is then needed to run the actual ./Checkmate command"""
    with open(checkmate_dir + card_file_template, 'r') as template:
        # read a list of lines into data
        changes = template.readlines()
    #make changes to template 
    changes[3] = 'Name: ' + checkmate_result_file_name + '\n'
    changes[14] = 'Events: ' + checkmate_output_name+  '_lhe_subdir/' + lhe_file + '\n'
    #and then we write it to a new file!!!!
    new_card_file = 'scripting_card_' + str(int(idx)) + '.dat'
    with open(checkmate_dir + checkmate_output_name + '_card_subdir/' + new_card_file, 'w') as file:
        file.writelines(changes)
    return new_card_file

def clean_checkmate_dir(checkmate_dir, checkmate_output_name, lhe_file, new_card_file):
    #lets delete the card file and event file to keep things clean and save memory
    run(['rm ' + checkmate_output_name + '_card_subdir/' + new_card_file], cwd = checkmate_dir, shell=True)
    run(['rm ' + checkmate_output_name + '_lhe_subdir/' + lhe_file], cwd = checkmate_dir, shell=True)
    return None

def result_storer(row, result_dir, checkmate_dir, output_csv_file):
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

def decision_generator(idx, row, lhe_file,  checkmate_dir, card_file_template, output_csv_file, checkmate_output_name):
    """This function takes the lhe events generated from the above function and runs them through
    checkmate and gets a decision if they're allowed or not. Outputs 1 if allowed, a zero if not allowed"""
    #lets define some paths our path to our card.dat template and the name of the result file
    checkmate_result_file_name = checkmate_output_name + '_checkmate_output_' + str(int(idx))
    #generate our checkmate card file
    new_card_file = checkmate_card_generator(idx, checkmate_dir, card_file_template, checkmate_output_name, lhe_file, checkmate_result_file_name)
    #time to run checkmate on our new_card_file which refers to our lhe_file
    run(['./CheckMATE ' + checkmate_output_name + '_card_subdir/' + new_card_file], cwd = checkmate_dir, shell=True)
    #clean checkmate dir by removing lhe and card files
    clean_checkmate_dir(checkmate_dir, checkmate_output_name, lhe_file, new_card_file)
    #results are held in the following dir, assuming name is unchanged in checkmate card
    result_dir = checkmate_dir[:-4] + 'results/' + checkmate_result_file_name + '/result.txt' #its [:-4] to get move out of bin dir
    print(result_dir)
    #now lets store the result
    result_storer(row, result_dir, checkmate_dir, output_csv_file)
    return None


def multiprocessing_decision_generator(config_dict):
    print('\n\nLets start the parallel processing of the lhe events using checkmate!!!\n\n')
    #difne our scan_reader, which is a generator we can iterate over to produce each  point in the scan
    input_scan = scan_reader(config_dict['input_csv_file'])
    #now define the list of lhe files generated from our scan
    lhe_files = os.listdir(config_dict['checkmate_dir'] + config_dict['checkmate_output_name']+ '_lhe_subdir/')
    #raise error if we dont generate all the lhe files
    if len(lhe_files)!= config_dict['points_in_scan']:
        raise ValueError('Number of lhe files produced does not match number of points in scan!!!')
    #the actual parallel processing...
    pool = mp.Pool(mp.cpu_count())
    for idx, lhe_file in tqdm(enumerate(lhe_files), total=float( config_dict['points_in_scan'])):
        row = next(input_scan)
        pool.apply_async(decision_generator, args=(idx, row, lhe_file,  config_dict['checkmate_dir'], config_dict['card_file_template'], config_dict['output_csv_file'], config_dict['checkmate_output_name']) )
    pool.close()
    pool.join()
    print('\n\nFINISHED!!!\n\n')
    return None

def generate_checkmate_subdirs(config_dict):
    #first generate the lhe_subdir
    run(['mkdir ' + config_dict['checkmate_output_name'] + '_lhe_subdir/'], cwd = config_dict['checkmate_dir'], shell=True)
    #then generate the card_subdir
    run(['mkdir ' + config_dict['checkmate_output_name'] + '_card_subdir/'], cwd = config_dict['checkmate_dir'], shell=True)
    return None

def remove_checkmate_subdirs(config_dict):
    #first remove the lhe_subdir
    run(['rm -rf ' + config_dict['checkmate_output_name'] + '_lhe_subdir/'], cwd = config_dict['checkmate_dir'], shell=True)
    #then remove the card_subdir
    run(['rm -rf ' + config_dict['checkmate_output_name'] + '_card_subdir/'], cwd = config_dict['checkmate_dir'], shell=True)
    return None

def complete_multiprocessing_pipeline(config_dict):
    #first lets generate the output csv file
    generate_output_scan_template_csv(output_csv= config_dict['output_csv_file'], input_csv=config_dict['input_csv_file'], fresh_input=config_dict['fresh_input'], starting_row=config_dict['starting_row'])
    #second lets generate the lhe_subdir and card_subdir, that we will need to store our checkmate related files
    generate_checkmate_subdirs(config_dict)
    #now lets generate the lhe files for all the points in the scan
    all_lhe_events_generator(config_dict)
    #lets start the parallel processing of the lhe events using checkmate!!!
    multiprocessing_decision_generator(config_dict)
    #once were done, we can remove the checkmate subdirs
    remove_checkmate_subdirs(config_dict)
    return None

if __name__ == '__main__':
    #all_lhe_events_generator(config_dict)
    complete_multiprocessing_pipeline(config_dict)