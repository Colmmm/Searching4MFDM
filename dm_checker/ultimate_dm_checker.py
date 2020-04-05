import csv
import numpy as np
from tqdm import tqdm
import os
import pandas as pd
import sys
import subprocess
from scan_utils import *
# -*- coding: utf-8 -*-
import json

# Make it work for Python 2+3 and with Unicode
import io
try:
    to_unicode = unicode
except NameError:
    to_unicode = str

def config_dict_editor(node, input_file, output_file, points_in_scan=16, num_events=300000):
    """Needs to be ran in dm_checker"""
    # Read JSON file
    with open('jsons/CONFIG_DICT_' + str(node) + '.json') as infile:
        config_dict = json.load(infile)
    #first lets the make changes 
    config_dict["input_csv_file"] = input_file
    config_dict["output_csv_file"] = output_file
    config_dict["num_events"] = num_events
    config_dict["points_in_scan"] = points_in_scan
    #lets write out changes to the file now
    with io.open('jsons/CONFIG_DICT_' + str(node) + '.json', 'w', encoding='utf8') as outfile:
        str_ = json.dumps(config_dict,
                      indent=4, sort_keys=True,
                      separators=(',', ': '), ensure_ascii=False)
        outfile.write(to_unicode(str_))
    return None

def ultimate_multiprocessing_pipeline(input_file, output_file, iridis_batch_dir, nodes=[0,1,2,3]):
    """This is assumed to be ran in the dm_checker dir of Searching4MFDM"""
    #mkdir for our new subset scans
    subsets_dir = input_file[:-4] + '/'
    run(['mkdir ' + subsets_dir], shell=True)
    #now we need to edit the config_dicts and run the qsub files
    total_points = pd.read_csv(input_file).shape[0]
    for i, subset in enumerate(pd.read_csv(input_file, index_col=0, chunksize=int(total_points/len(nodes)) )):
        #first define name of our subset scans path
        subset_path = subsets_dir + 'SUBSET_' + str(i) + '.csv'
        subset.to_csv(subset_path)
        #now we edit the correspoinding config dict
        config_dict_editor(i, subset_path, output_file, points_in_scan=subset.shape[0], num_events=350000)
        #now we submit our barch file to iridis
        run(['qsub qsub.dat'], cwd=iridis_batch_dir+'batch_'+str(i), shell=True)

if __name__=='__main__':
    iridis_batch_dir = '/scratch/cwks1g16/Iridis_batch_files/'
    input_file = '../input_scans/delta_MD3_1_INPUT.csv'
    output_file = '../output_scans/delta_MD3_1_OUTPUT.csv'
    ultimate_multiprocessing_pipeline(input_file, output_file, iridis_batch_dir, nodes=[0,1,2,3])
