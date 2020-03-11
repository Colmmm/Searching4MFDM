import itertools
import pandas as pd
import numpy as np
import csv
from numpy.random import rand

def grid_scan_generator(MD1_range, MDP_range, MD3_range, output_file_name='colm_input_scan.csv', mass_hierarchy=True):
    """This is the GRID SCAN GENERATOR. It creates a grid scan, which takes the desired ranges of the masses MD1,MDP,MD3 as inputs,
    in the format of [start_value,end_value,step], eg, MD1_range = [0,1000,100]. This function will then create all the possible
    combinations of MD1,MDP,MD3 allowed by the mass hierarchy (if mass_hierarch=True) and will output these combinations as a panadas
    df as well as saving it as a csv. The dataframe will also have columns for the delta mass values as well as 4 columns for each
    search type indicating if its allowed or not"""
    #define the range of values for MD1, MDP, MD3
    MD1 = np.arange(MD1_range[0], MD1_range[1], (MD1_range[1]- MD1_range[0])/MD1_range[2])
    MDP = np.arange(MDP_range[0], MDP_range[1], (MDP_range[1]- MDP_range[0])/MDP_range[2])
    MD3 = np.arange(MD3_range[0], MD3_range[1], (MD3_range[1]- MD3_range[0])/MD3_range[2])
    #create a list of all the combinations
    grid_scan = list(itertools.product(*[MD1, MDP, MD3]))
    #in our grid scan we still want 6 extra columns, which we add as nan values for now
    grid_scan = [row + tuple(np.full(6, np.nan)) for row in grid_scan]
    #need to turn it into a df now
    grid_scan = pd.DataFrame(data=grid_scan, columns = ['MD1', 'MDP', 'MD3', 'delta_MDP', 'delta_MD3', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD'])
    #one of the extra 6 columns are the delta mass values which we can add now
    grid_scan['delta_MDP'] = grid_scan.apply(lambda x: x.MDP - x.MD1, axis=1)
    grid_scan['delta_MD3'] = grid_scan.apply(lambda x: x.MD3 - x.MD1, axis=1)
    #if input variable mass_hierarchy=True then we get rid of combinations that disobey mass hierarchy MD1<MDP<MD3
    if mass_hierarchy==True:
        grid_scan = grid_scan.query('MD1<MDP<MD3').query('MD1!=0')
        grid_scan.index = range(grid_scan.shape[0])
    #export grid scan as a csv
    grid_scan.to_csv(output_file_name)
    return grid_scan

    def random_scan_generator(MD1_range, MDP_range, MD3_range, output_file_name='colm_input_scan.csv', mass_hierarchy=True):
    """This is the RANDOM SCAN GENERATOR. It creates a random scan, which takes the desired ranges of the masses MD1,MDP,MD3 as inputs,
    in the format of [max_value,min_value,population_size], eg, MD1_range = [50,1000,100] will give you 100 MD1 values, from 50 to 1000.
    This function will then create all the possible combinations of MD1,MDP,MD3 allowed by the mass hierarchy (if mass_hierarch=True) 
    and will output these combinations as a panadas df as well as saving it as a csv. (But beware, the total number of combinations will
    vary due to the mass hierarchy) The dataframe will also have columns for the  delta mass values as well as 4 columns for each search
    type indicating if its allowed or not"""
    #define the range of values for MD1, MDP, MD3
    MD1 = MD1_range[0] + (MD1_range[1]-MD1_range[0])*rand(MD1_range[2])
    MDP = MDP_range[0] + (MDP_range[1]-MDP_range[0])*rand(MDP_range[2])
    MD3 = MD3_range[0] + (MD3_range[1]-MD3_range[0])*rand(MD3_range[2])
    #create a list of all the combinations
    grid_scan = list(itertools.product(*[MD1, MDP, MD3]))
    #in our grid scan we still want 6 extra columns, which we add as nan values for now
    grid_scan = [row + tuple(np.full(6, np.nan)) for row in grid_scan]
    #need to turn it into a df now
    grid_scan = pd.DataFrame(data=grid_scan, columns = ['MD1', 'MDP', 'MD3', 'delta_MDP', 'delta_MD3', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD'])
    #one of the extra 6 columns are the delta mass values which we can add now
    grid_scan['delta_MDP'] = grid_scan.apply(lambda x: x.MDP - x.MD1, axis=1)
    grid_scan['delta_MD3'] = grid_scan.apply(lambda x: x.MD3 - x.MD1, axis=1)
    #if input variable mass_hierarchy=True then we get rid of combinations that disobey mass hierarchy MD1<MDP<MD3
    if mass_hierarchy==True:
        grid_scan = grid_scan.query('MD1<MDP<MD3')
        grid_scan.index = range(grid_scan.shape[0])
    #export grid scan as a csv
    grid_scan.to_csv(output_file_name)
    return grid_scan

def scan_reader(input_scan_csv):  
    """This is the SCAN READER. Its is a generator which can be iterated over, each iteration it reads and outputs the row of the 
    input scan, which includes the values of MD1,MDP,MD3, delta values as well as the allowed values"""
    with open(input_scan_csv) as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            yield row

def generate_output_scan_template_csv(output_csv='colm_output_scan.csv', input_csv='colm_input_scan.csv', fresh_input=True, starting_row=0):
    """Write the output csv, with the columns, ready for rows to be added to it. If fresh_input=True then initial output scan will be empty csv
    if fresh_input=False then the initial output scan will be the rows of the input scan which are already complete."""
    if fresh_input == True:
        with open(output_csv, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(['MD1', 'MDP', 'MD3', 'delta_MDP', 'delta_MD3', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD'])
    else:
        with open(input_csv, 'rw') as input_file, open(output_csv) as output_file:
            completed_rows = input_file.readlines()[:starting_row]  
            output_file.writelines(completed_rows)
    return None

def store_result(input_row,  output_csv, allowed_dict = {'LHC': 0, 'DD': 1, 'ID': 2, 'RD':3}, **kwargs):
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