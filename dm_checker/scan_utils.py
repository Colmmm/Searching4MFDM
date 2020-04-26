import itertools
import pandas as pd
import numpy as np
import csv
from numpy.random import rand
import subprocess

def grid_scan_generator(MDX_range, delta_MDP_range, delta_MD3_range, MDX='MD3', output_file_name='colm_input_scan.csv', apply_mass_rules=True):
    """This is the GRID SCAN GENERATOR. It creates a grid scan, which takes the desired ranges of the masses MD1,MDP,MD3 as inputs,
    in the format of [start_value,end_value,step], eg, MD1_range = [0,1000,100]. This function will then create all the possible
    combinations of MD1,MDP,MD3 allowed by the mass hierarchy (if mass_hierarch=True) and will output these combinations as a panadas
    df as well as saving it as a csv. The dataframe will also have columns for the delta mass values as well as 4 columns for each
    search type indicating if its allowed or not"""
    #define the range of values for MD1, MDP, MD3
    MDXs = np.arange(MDX_range[0], MDX_range[1], (MDX_range[1]- MDX_range[0])/MDX_range[2])
    delta_MDPs = np.arange(delta_MDP_range[0], delta_MDP_range[1], (delta_MDP_range[1]- delta_MDP_range[0])/delta_MDP_range[2])
    delta_MD3s = np.arange(delta_MD3_range[0], delta_MD3_range[1], (delta_MD3_range[1]- delta_MD3_range[0])/delta_MD3_range[2])
    #create a list of all the combinations
    grid_scan = list(itertools.product(*[MDXs, delta_MDPs, delta_MD3s]))
    #in our grid scan we still want 9 extra columns, which we add as nan values for now
    grid_scan = [row + tuple(np.full(9, np.nan)) for row in grid_scan]
    if MDX == 'MD3':
        #need to turn it into a df now
        grid_scan = pd.DataFrame(data=grid_scan, columns = ['MD3', 'delta_MDP', 'delta_MD3', 'MDP', 'MD1', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD', 'r_value', 'analysis', 'SR'])
        #we can now define the actual masses using our MD1 and the delta values
        grid_scan['MDP'] = grid_scan.apply(lambda x: x.MD3 - x.delta_MD3, axis=1)
        grid_scan['MD1'] = grid_scan.apply(lambda x: x.MDP - x.delta_MDP, axis=1)
        #just rearanging the columns
        grid_scan = grid_scan.loc[:, ['MD3', 'MDP', 'MD1', 'delta_MD3', 'delta_MDP', 'r_value', 'analysis', 'SR','allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD']]
    elif MDX == 'MD1':
        grid_scan = pd.DataFrame(data=grid_scan, columns = ['MD1', 'delta_MDP', 'delta_MD3', 'MDP', 'MD3', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD', 'r_value', 'analysis', 'SR'])
        #we can now define the actual masses using our MD1 and the delta values
        grid_scan['MDP'] = grid_scan.apply(lambda x: x.MD1 + x.delta_MDP, axis=1)
        grid_scan['MD3'] = grid_scan.apply(lambda x: x.MDP + x.delta_MD3, axis=1)
        grid_scan = grid_scan.loc[:, ['MD3', 'MDP', 'MD1', 'delta_MD3', 'delta_MDP', 'r_value', 'analysis', 'SR','allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD']]
    else:
        print('MDX needs to be either "MD3" or "MD1"!!!')
    #if input variable mass_hierarchy=True then we get rid of combinations that disobey mass hierarchy MD1<MDP<MD3
    if apply_mass_rules==True:
        grid_scan = grid_scan.query('MD1<MDP<MD3').query('MD1>0')
        grid_scan.index = range(grid_scan.shape[0])
    #export grid scan as a csv
    grid_scan.to_csv(output_file_name)
    return grid_scan

def random_scan_generator(MDX_range, delta_MDP_range, delta_MD3_range, MDX='MD3', output_file_name='colm_input_scan.csv', apply_mass_rules=True):
    """This is the RANDOM SCAN GENERATOR. It creates a random scan, which takes the desired ranges of the masses MD1,MDP,MD3 as inputs,
    in the format of [max_value,min_value,population_size], eg, MD1_range = [50,1000,100] will give you 100 MD1 values, from 50 to 1000.
    This function will then create all the possible combinations of MD1,MDP,MD3 allowed by the mass hierarchy (if mass_hierarch=True) 
    and will output these combinations as a panadas df as well as saving it as a csv. (But beware, the total number of combinations will
    vary due to the mass hierarchy) The dataframe will also have columns for the  delta mass values as well as 4 columns for each search
    type indicating if its allowed or not"""
    #define the range of values for MD1, MDP, MD3
    MDXs = MDX_range[0] + (MDX_range[1]-MDX_range[0])*rand(MDX_range[2])
    delta_MDPs = delta_MDP_range[0] + (delta_MDP_range[1]-delta_MDP_range[0])*rand(delta_MDP_range[2])
    delta_MD3s = delta_MD3_range[0] + (delta_MD3_range[1]-delta_MD3_range[0])*rand(delta_MD3_range[2])
    #create a list of all the combinations
    grid_scan = list(itertools.product(*[MDXs, delta_MDPs, delta_MD3s]))
    #in our grid scan we still want 9 extra columns, which we add as nan values for now
    grid_scan = [row + tuple(np.full(9, np.nan)) for row in grid_scan]
    if MDX == 'MD3':
        #need to turn it into a df now
        grid_scan = pd.DataFrame(data=grid_scan, columns = ['MD3', 'delta_MDP', 'delta_MD3', 'MDP', 'MD1', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD', 'r_value', 'analysis', 'SR'])
        #we can now define the actual masses using our MD1 and the delta values
        grid_scan['MDP'] = grid_scan.apply(lambda x: x.MD3 - x.delta_MD3, axis=1)
        grid_scan['MD1'] = grid_scan.apply(lambda x: x.MDP - x.delta_MDP, axis=1)
        grid_scan = grid_scan.loc[:, ['MD3', 'MDP', 'MD1', 'delta_MD3', 'delta_MDP', 'r_value', 'analysis', 'SR','allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD']]
    elif MDX == 'MD1':
        grid_scan = pd.DataFrame(data=grid_scan, columns = ['MD1', 'delta_MDP', 'delta_MD3', 'MDP', 'MD3', 'allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD', 'r_value', 'analysis', 'SR'])
        #we can now define the actual masses using our MD1 and the delta values
        grid_scan['MDP'] = grid_scan.apply(lambda x: x.MD1 + x.delta_MDP, axis=1)
        grid_scan['MD3'] = grid_scan.apply(lambda x: x.MDP + x.delta_MD3, axis=1)
        grid_scan = grid_scan.loc[:, ['MD3', 'MDP', 'MD1', 'delta_MD3', 'delta_MDP', 'r_value', 'analysis', 'SR','allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD']]
    else:
        print('MDX needs to be either "MD3" or "MD1"!!!')
    if apply_mass_rules==True:
        grid_scan = grid_scan.query('MD1<MDP<MD3').query('MD1>0')
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
            writer.writerow(['MD1', 'MDP', 'MD3', 'delta_MDP', 'delta_MD3', 'r_value', 'analysis', 'SR','allowed_by_LHC', 'allowed_by_DD', 'allowed_by_ID', 'allowed_by_RD'])
    else:
        with open(input_csv, 'rw') as input_file, open(output_csv, 'w') as output_file:
            completed_rows = input_file.readlines()[:starting_row]  
            output_file.writelines(completed_rows)
    return None

def store_result(input_row,  output_csv, allowed_dict = {'r_value':0,'analysis':1,'SR':2,'LHC': 3, 'DD': 4, 'ID': 5, 'RD':6}, **kwargs):
    """This takes function takes in a result the **kwargs, which is a dict, and would look something like {'DD': 0, 'ID': 1, 'RD':0} from non colliders,
    and {'r_value':1.6842, 'analysis':'cms_sus_16_025' , 'SR':'SR2_stop_1low_pt_1', 'LHC': 0}, and allowed_dict essentially tells where to 
    put each value in the df. This function thus stores a result (values for allowed or not + extra) in the output csv, we need input row to also
    store the masses in the output file.
    """
    #define the cols to do with if the actual result from checkmate, like SR,r_value as theyre the ones we will need to change
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
