import csv
from tqdm import tqdm
import sys
import subprocess
from config_dict import config_dict

def run(*popenargs, **kwargs):
    """This is a backport version of subprocess.run() which is only available in python 3.5, but as this scripting pipeline
    needs to be ran in pyhton 2.7 due to checkmate, this version is defined and used instead"""
    input = kwargs.pop("input", None)
    check = kwargs.pop("handle", False)

    if input is not None:
        if 'stdin' in kwargs:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = PIPE

    process = subprocess.Popen(*popenargs, **kwargs)
    try:
        stdout, stderr = process.communicate(input)
    except:
        process.kill()
        process.wait()
        raise
    retcode = process.poll()
    if check and retcode:
        raise CalledProcessError(
            retcode, process.args, output=stdout, stderr=stderr)
    return retcode, stdout, stderr

def scan_reader(input_scan_csv):  
	"""This is the SCAN READER. Its is a generator which can be iterated over, each iteration it reads and outputs the row of the 
	input scan, which includes the values of MD1,MDP,MD3, delta values as well as the allowed values.
	Each row consists of [index, 'MD1', 'MDP', 'MD3', 'delta_MDP', 'delta_MD3', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD']
	"""
	with open(input_scan_csv) as file:
		reader = csv.reader(file)
		next(reader)
		for row in reader:
			yield row

def batch_file_generator(MD1, MDP, MD3, batch_file, calchep_dir, output_events, local=True):
	"""This edits the calchep batchfile (batch_file), ie changing for a specific parameter combo of MD1, MDP, MD3,
	ands about it. You need to specify the parameter values you want, the batch_file which is already created
	and the calchep directory where the batch file will be ran. The batch_file name is outputted which is kind of
	pointless but felt better than returning nothing. Also this way the batch_file name can be passed to next function"""
	path2file = calchep_dir + batch_file
	#asserting mass hierarchy of MFDM
	if MD1<MDP<MD3:
		#read in batch file first
		with open(path2file, 'r') as file:
			# read a list of lines into data
			changes = file.readlines()
		# Make changes to the parameter info, which starts at line 11, you also have to add \n at end for it to work
		changes[10] = 'Parameter: MD1 = ' + str(MD1) + '\n' 
		changes[11] = 'Parameter: MDP = ' + str(MDP) + '\n'  
		changes[12] = 'Parameter: MD3 = ' + str(MD3) + '\n'
		#set name for outgoing events file name
		changes[46] = 'Filename:                        ' + output_events + '\n'
		#if being ran not locally, ie, local = False then it is assumed that we can use a lot more cpus
		if local==False:
			changes[55] = 'Max number of cpus:   16' + '\n'
		else:
			changes[55] = 'Max number of cpus:   2' + '\n'
		# and write everything back
		with open(path2file, 'w') as file:
			file.writelines(changes)
		return batch_file

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
	#first we need to remove the "lock.batch" file (if it exists) in order to do multiple scans in a row
	run(['rm lock.batch'], cwd =calchep_dir, shell=True)
	#next lets run the batch file and generate the lhe events
	run(['./calchep_batch ' + batch_file], cwd=calchep_dir, shell=True)
	#now we unzip the lhe files
	run(['gunzip -k '+ lhe_file + '.gz'], cwd=calchep_results_dir, shell=True)
	#now we copy over the lhe files to the checkmate directory
	run(['cp '+ lhe_file + ' ' + checkmate_dir], cwd=calchep_results_dir, shell=True)
	return lhe_file


def decision_generator(lhe_file, checkmate_dir, card_file):
	"""This function takes the lhe events generated from the above function and runs them through
	checkmate and gets a decision if they're allowed or not. Outputs 1 if allowed, a zero if not allowed"""
	#first we need to edit the checkmate card, so it refers to right lhe_file name
	path2file = checkmate_dir + card_file
	with open(path2file, 'r') as file:
		# read a list of lines into data
		changes = file.readlines()
	#make changes
	changes[14] = 'Events: ' + lhe_file + '\n'
	# and write everything back
	with open(card_file, 'w') as file:
		file.writelines(changes)
	#time to run checkmate on the card_file which refers to our lhe_file
	run(['./CheckMATE ' + card_file], cwd = checkmate_dir, shell=True)
	#results are held in the followinh dir, assuming name is unchanged in checkmate card
	result_dir = checkmate_dir[:-4] + 'results/scripting_result/result.txt' #its [:-4] to get move out of bin dir
	#time to collect and output result from this result_dir
	with open(result_dir, 'r') as file:
		# just way data is formatted, the result is given by below line
		#result = file.readlines()[1].split()[-1]
		r_value = file.readlines()[2].split()[-1]
		return r_value
	#if result == 'Allowed':
	#	return 1
	#else:
	#	return 0

def generate_output_scan_template_csv(output_csv='colm_output_scan.csv', input_csv='colm_input_scan.csv', fresh_input=True, starting_row=0):
	"""Write the output csv, with the columns, ready for rows to be added to it"""
	if fresh_input == True:
		with open(output_csv, 'w') as file:
			writer = csv.writer(file)
			writer.writerow(['MD1', 'MDP', 'MD3', 'delta_MDP', 'delta_MD3', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD'])
	else:
		with open(input_csv, 'rw') as input_file, open(output_csv) as output_file:
			completed_rows = input_file.readlines()[:starting_row]	
			output_file.writelines(completed_rows)
	return None

def store_result(input_row,  output_csv=config_dict['output_csv_file'],allowed_dict = {'LHC': 0, 'DD': 1, 'ID': 2, 'RD':3}, **kwargs):
    """This takes the result of whether the parameter space is allowed or not,
    and stores it in the csv scan output file. Result parameter input should be a 1 for allowed and 0
    for not allowed. Search type should be either: 'LHC', 'DD', 'ID', 'RD'
    """
    #define the cols to do with if a result is allowed or not, as theyre the ones which could potentially change
    allowed_cols = input_row[6:]
    # exact col of allowed_cols depends on search_type, and needs to be changed depending on the result
    #kwargs is our result and should be a dict, containing the search type and result, eg, {'RD': 0}
    for key, value in kwargs.items():
        allowed_cols[allowed_dict[key]] = value
    #time to add our data
    with open(output_csv, 'a') as file:
        writer = csv.writer(file)
        writer.writerow(input_row[:6] + allowed_cols)
    return None


def LHC_single_parameter_point_search(MD1, MDP, MD3, batch_file = config_dict['calchep_batch_file'], calchep_dir = config_dict['calchep_dir'], 
	output_events = config_dict['calchep_output_events'], local = config_dict['local'], checkmate_dir = config_dict['checkmate_dir'], card_file = config_dict['checkmate_card_file']):
	"""This function takes a single parameter point and makes a decision if its allowed by bringing the whole pipeline together:
		1) Creates batch file
		2) Creates lhe events (using Calchep)
		3) Makes a decision on those events (using CHECKmate)
	"""
	#print('\n\n\nParameter:')
	# 1)create the batch file (note variable batch_file is just the str of the name of the batch file)
	batch_file = batch_file_generator(MD1, MDP, MD3, batch_file, calchep_dir, output_events, local)
	# 2) Create the lhe files (note variable lhe_file is just the string of the lhe events file name)
	lhe_file = events_generator(batch_file, calchep_dir, output_events, checkmate_dir)
	# 3) Make a decision on those events, where result is 1 for being allowed, 0 for not allowed
	result = decision_generator(lhe_file, checkmate_dir, card_file)
	return {'LHC': result}

def parameter_space_scan(input_csv_file, output_csv_file, points_in_scan=None):
	"""This function searches multiple parameter points in the parameter space using the single_parameter_point_search function above,
	it takes a csv file as an input"""
	#first lets generate the output csv file
	generate_output_scan_template_csv(output_csv=output_csv_file)
	#now lets loop over the different rows containing the parameter points in our input scan csv
	for row in tqdm(scan_reader(input_scan_csv=input_csv_file), total=float(points_in_scan)):
		#define our masses from our input csv row
		MD1, MDP, MD3 = float(row[1]), float(row[2]), float(row[3])
		#for this single parameter point, calculate if its allowed or not. Result = 1 or allowed, 0 if not allowed
		result = single_parameter_point_search(MD1, MDP, MD3)
		#time to store our result
		store_result(row, result, 'LHC', output_csv_file)
	return None


if __name__ == '__main__':
	LHC_single_parameter_point_search(60, 100, 200)
	#parameter_space_scan(input_csv_file=sys.argv[1],
						 #output_csv_file=sys.argv[2],
						 #points_in_scan=sys.argv[3])

