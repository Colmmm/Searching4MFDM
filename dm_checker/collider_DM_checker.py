import csv
from tqdm import tqdm
import sys
import subprocess
from scan_utils import run, scan_reader, generate_output_scan_template_csv
from config_dict import config_dict


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

def collider_single_point_checker(MD1, MDP, MD3, config_dict):
	"""This function takes a single parameter point and makes a decision if its allowed by bringing the whole pipeline together:
		1) Creates batch file
		2) Creates lhe events (using Calchep)
		3) Makes a decision on those events (using CHECKmate)
	"""
	#print('\n\n\nParameter:')
	# 1)create the batch file (note variable batch_file is just the str of the name of the batch file)
	batch_file = batch_file_generator(MD1, MDP, MD3, config_dict['calchep_batch_file'], config_dict['calchep_dir'], config_dict['calchep_output_events'], config_dict['local'])
	# 2) Create the lhe files (note variable lhe_file is just the string of the lhe events file name)
	lhe_file = events_generator(config_dict['calchep_batch_file'], config_dict['calchep_dir'], config_dict['calchep_output_events'], config_dict['checkmate_dir'])
	# 3) Make a decision on those events, where result is 1 for being allowed, 0 for not allowed
	result = decision_generator(lhe_file, config_dict['checkmate_dir'], config_dict['checkmate_card_file'])
	return {'LHC': result}

def collider_parameter_space_checker(config_dict):
	"""This function searches multiple parameter points in the parameter space using the collider_single_point_checker function above,
	it takes the config_dict as the only input. Does not output anything directly but will update the output csv scan and fill it with
	values of whether each point is allowed or not."""
	#first lets generate the output csv file
	generate_output_scan_template_csv(output_csv= config_dict['output_csv_file'])
	#now lets loop over the different rows containing the parameter points in our input scan csv
	for row in tqdm(scan_reader(input_scan_csv= config_dict['input_csv_file']), total=float( config_dict['points_in_scan'] )):
		#define our masses from our input csv row
		MD1, MDP, MD3 = float(row[1]), float(row[2]), float(row[3])
		#for this single parameter point, calculate if its allowed or not. Result = 1 or allowed, 0 if not allowed
		result = collider_single_point_checker(MD1, MDP, MD3, config_dict)
		#time to store our result
        store_result(input_row=row, output_csv=config_dict['output_csv_file'], **result)
	return None


if __name__ == '__main__':
	collider_parameter_space_checker(config_dict)

