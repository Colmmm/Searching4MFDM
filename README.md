# Searching4MFDM

# Summary
## Code repository used to search the parameter space of the Minimal Fermion Dark Matter (MFDM)

# Pipeline Overview
* The pipeline for checking LHC limits (collider_DM_checker.py) and DD,ID,RD (non_collider_DM_checker.py) work independently to each other and can be simply ran on the command line using "$python collider_DM_checker.py" for example if you have an already correct config_dict in the same directory as well as all the scripting_files in their correct places too
* The config_dict.py file contains a dictionary also called config_dict and contains all the settings (such as if code is being ran locally or not) and paths to the relevant scripting files such as a template of the calchep batch file which is altered after each iteration (for each parameter point).
* The inclusive_DM_checker.py then combines the collider_DM_checker.py and non_collider_DM_checker.py pipelines together, and can be ran in three different modes. For example, mode=1 means pipeline checks non_collider constraints first for all points in scan and then runs collider checks, while mode=2 checks both collider and non_collider constraints at the same time.

# Setting up
## Setting up the pipeline correctly is not straight forward, as of course you'll need the following programns already correctly installed:
1. Calchep
2. Micromegas
3. Checkmate
4. Pythia
5. Delphes
6. Hepmc
7. Madgraph

## And for the pipeline, there needs to be certain scripting files in certain directories, for example, the calchep template batch file needs to be in <your_calchep_dir>. Here is a complete list of what scripting files need to be in what directory:
1. An **input scan** containing the parameter points that will be checked in the **input_scans** dir
2. As already mentioned, a **calchep_batch_file** needs to be in the **calchep_dir**
3. A **.dat_card_file** needs to be in the **checkmate_dir** (bin dir)
4. A **.par_file** needs to be in the **micromegas_dis** (MFDM dir)
5. An already compiled **c_file** also in the **micromegas_dis** (MFDM dir)

### Examples of these formentioned scripting files can be found in the scripting sub directory
