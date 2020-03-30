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


# HOW TO DOWNLOAD CHECKMATE

# 1) GET THE PROPER MINICONDA ENVIRONMENT

## 1a) If you don't already have miniconda then download it via:
wget -nv http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
source $HOME/miniconda/etc/profile.d/conda.sh # Add to bashrc or similar or else you will have to run this everytime you wanna use your env
## 1b) Create the conda env we will need
conda create -n checkmate_env root pythia8 hepmc2 pandas numpy python=2 scipy tqdm -c conda-forge

# Now lets download the rest of the stuff, assuming youre on iridis, lets setup this pipeline in your scatch dir, so run (but for your username):
cd /scratch/cwks1g16

# 2) Download Delphes
git clone https://github.com/delphes/delphes.git
cd delphes
./configure
make

# 3) Download Madgraph
wget https://launchpad.net/mg5amcnlo/2.0/2.7.x/+download/MG5_aMC_v2.7.2.tar.gz
tar -xzf  MG5_aMC_v2.7.2.tar.gz

# 4) Download Checkmate
wget https://checkmate.hepforge.org/downloads?f=CheckMATE-Current.tar.gz
tar -xzf CheckMATE-Current.tar.gz
cd CheckMATE-Current
autoconf
./configure --with-rootsys=/lyceum/cwks1g16/miniconda/envs/checkmate_env --with-delphes=/scratch/cwks1g16/delphes --with-pythia=/lyceum/cwks1g16/miniconda/envs/checkmate_env --with-hepmc=/lyceum/cwks1g16/miniconda/envs/checkmate_env --with-madgraph=/scratch/cwks1g16/MG5_aMC_v2.7.2
make

# 5) Getting my pipeline
