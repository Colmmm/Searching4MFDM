from config_dict import config_dict
from LHC_searching_pipeline import run, scan_reader, generate_output_scan_template_csv, store_result, LHC_single_parameter_point_search
from RD_DD_ID_searching_pipeline import RD_DD_ID_single_parameter_point_checker
from tqdm import tqdm
from itertools import islice

def inclusive_DM_checker(config_dict, mode=3):
	# 1) Generate output csv
	generate_output_scan_template_csv(config_dict['output_csv_file'])
	#for row in tqdm(  islice(  scan_reader(input_scan_csv=config_dict['input_csv_file']), config_dict['starting_row']), total=float(config_dict['points_in_scan'])   ):
	for row in islice( tqdm(   scan_reader(input_scan_csv=config_dict['input_csv_file']), total=float(config_dict['points_in_scan'])) , config_dict['starting_row'], None)  :
		MD1, MDP, MD3 = float(row[1]), float(row[2]), float(row[3])
		result = RD_DD_ID_single_parameter_point_checker(MD1, MDP, MD3, config_dict)
		if mode==1:
			store_result(input_row=row, **result)
			continue
		if mode==2:
			LHC_result = LHC_single_parameter_point_search(MD1, MDP, MD3)
			result.update(LHC_result)
			store_result(input_row=row, **result)
			continue
		if mode==3:
			#check if any of RD, DD or ID doesnt allow particular parameter point
			if sum(result.values()) == 3:
				LHC_result = LHC_single_parameter_point_search(MD1, MDP, MD3)
				result.update(LHC_result)
			else:
				continue
	if mode==1:
		print('\n\nAll checks for RD, DD, ID now complete!!!\n\nNow checking the LHC conditions:\n')
		for row in islice( tqdm(   scan_reader(input_scan_csv=config_dict['input_csv_file']), total=float(config_dict['points_in_scan'])) , config_dict['starting_row'], None)  :
			MD1, MDP, MD3 = float(row[1]), float(row[2]), float(row[3])
			LHC_result = LHC_single_parameter_point_search(MD1, MDP, MD3)
			store_result(input_row, **LHC_result)
	return None


if __name__ == '__main__':
	inclusive_DM_checker(config_dict, mode=2)

