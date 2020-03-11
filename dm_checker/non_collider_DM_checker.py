from scan_utils import run, scan_reader, generate_output_scan_template_csv, store_result
import csv
import numpy as np
from config_dict import config_dict

def XENON1T_limit(DM_mass):
    '''This function takes in a value for the mass of DM and outputs the corresponding maximum limit of that the 
    proton-DM spin independent cross section (sigma_max) would have according to a 7th order polynomial fit
    of the limits observed at XENON1T. Graph which was used to fit was log(MD1) against log(sigma_max), so to
    get actual values we need to transfer to logs then back again.'''
    #transform to log space
    x = np.log10(DM_mass)
    #define the parameters from our fit to the XENON data
    a0, a1, a2, a3, a4, a5, a6, a7 = [-6.12758156e+01, -3.49707877e+01,  6.86347267e+00,  1.15941164e+00,
       -6.77983966e-01,  1.11362682e-01, -8.22699735e-03,  2.33673270e-04]
    log_sigma_max = a0 + a1*x + a2*x**2 + a3*x**3 + a4*x**4 + a5*x**5 +a6*x**6 +a7*x**7
    #return the unlogged sigma_max now
    return np.power(10, log_sigma_max)

def CTA_limit(DM_mass):
    '''This function takes in a value for the mass of DM and outputs the corresponding maximum limit that the 
     DM self-annihilation velocity weighted cros section via W+W- (W_contrib_sigV) would be according to a 7th 
     order polynomial fit of the limits observed at CTA. The graph which was used to fit contained log(MD1) against 
     log(W_contrib_sigV), so to get actual values we need to transfer to logs then back again.'''
    #transform to log space
    x = np.log10(DM_mass)
    #define the parameters from our fit to the XENON data
    a0, a1, a2, a3, a4, a5, a6, a7 = [-5.55723108e+01,  1.53306173e+01, -8.83774457e+00,  1.82880636e+00,
       -1.64487235e-01,  3.94884412e-03,  2.95702006e-04, -1.47865839e-05]
    log_sigma_max = a0 + a1*x + a2*x**2 + a3*x**3 + a4*x**4 + a5*x**5 +a6*x**6 +a7*x**7
    #return the unlogged sigma_max now
    return np.power(10, log_sigma_max)

def generate_micromegas_output(MD1, MDP, MD3, config_dict):
    # 1) Generate the data.par file to be inputted into micromegas
    with open(config_dict['micromegas_dir']+config_dict['par_file_name'], 'w') as file:
        file.write('MD1 '+ str(MD1) + '\n' + 'MDP ' + str(MDP) + '\n' + 'MD3 ' + str(MD3) )
    # 2) Run micromegas to generate output variables which are stored in a csv file 
    run(['./'+ config_dict['c_file_name'] + ' ' + config_dict['par_file_name']], cwd=config_dict['micromegas_dir'], shell=True)
    # 3) Read in those outputted variables and return them in python
    with open(config_dict['micromegas_dir'] + config_dict['micromegas_output_file']) as file:
        reader = csv.reader(file)
        #this skips the headers
        next(reader)
        #output the variables var as floats not string
        return [float(var) for var in next(reader)]

def non_collider_decision_generator(MD1, RD, pSI, W_contrib_sigV):
    """This function takes in the values of the Relic Density (RD), DM-proton spin independent cross section 
    (pSI) and DM self annihilation cross section in W+W- (W_contrib_sigV) against their corresponding limits being
    1) Planck density for RD
    2) XENON1T for DD
    3) CTA for ID
    and this function then outputs a 1 if such values are acceptable relative to the these experimentally observed
    limits or this function outputs a 0 if the values are not allowed"""
    #apply condition for relic density
    if 0.115<RD<0.121:
        RD_result = 1
    else:
        RD_result = 0
    #apply condition for direct detection
    #but first we have to scale pSI, as micromegas assumes a RD of planck when it calculates pSI
    scaled_pSI = (RD/0.1188)*pSI
    if scaled_pSI < XENON1T_limit(MD1):
        DD_result = 1
    else:
        DD_result = 0
    #apply condition for indirect detection
    if W_contrib_sigV < CTA_limit(MD1):
        ID_result = 1
    else:
        ID_result = 0
    #output results
    return {'RD': RD_result, 'DD': DD_result, 'ID': ID_result}


def non_collider_single_point_checker(MD1, MDP, MD3, config_dict):
    # 1) Run microgmegas to generate RD (for RD searches), pSI (for DD searches) and W_contrib_sigV (for ID searches)
    MD1, MDP, MD3, RD, pSI, W_contrib_sigV = generate_micromegas_output(MD1, MDP, MD3, config_dict)
    # 2) Check values generated by step 1) against observed limits to see if parmaeter point is allowed or not
    result = RD_DD_ID_decision_generator(MD1, RD, pSI, W_contrib_sigV)
    return result


def non_collider_paramter_space_checker(config_dict):
    """This function searches multiple parameter points in the parameter space using the non_collider_single_point_checker function above,
    it takes the config_dict as the only input. Does not output anything directly but will update the output csv scan and fill it with
    values of whether each point is allowed or not."""
    #first lets generate the output csv file
    generate_output_scan_template_csv(output_csv= config_dict['output_csv_file'])
    #now lets loop over the different rows containing the parameter points in our input scan csv
    for row in tqdm(scan_reader(input_scan_csv= config_dict['input_csv_file']), total=float( config_dict['points_in_scan'] )):
        #define our masses from our input csv row
        MD1, MDP, MD3 = float(row[1]), float(row[2]), float(row[3])
        #for this single parameter point, calculate if its allowed or not. Result = 1 or allowed, 0 if not allowed
        result = non_collider_single_point_checker(MD1, MDP, MD3, config_dict)
        #time to store our result
        store_result(input_row=row, output_csv=config_dict['output_csv_file'], **result)
    return None

if __name__ == '__main__':
    non_collider_parameter_space_checker(config_dict)

