config_dict = {
    #input and output scan paths
    'input_csv_file': '../input_scans/multi_test_in.csv',
    'output_csv_file': '../output_scans/multi_test_out.csv',
    

    #calchep paths and filenames
    'calchep_dir': '/home/colmsam/MASTERS_project/CalcHEPwork/',
    'calchep_batch_file': 'multiprocessing_test_batch_file',
    'calchep_output_events': 'scripting_events',
    
    #checkmate paths and filnames
    'checkmate_dir': '/home/colmsam/checkmate2/bin/',
    'card_file_template': 'SCRIPTING_CHECKMATE_CARD_TEMPLATE.dat',
    'checkmate_output_name': 'iridis_batch_0',
    
    #micromegas paths and filenames
    'micromegas_dir': '/home/colmsam/micromegas/MFDM/',
    'par_file_name': 'data.par',
    'c_file_name': 'the_one_sasha_sent_me',
    'micromegas_output_file': 'micromegas_output_parameters.csv',
    
    #other stuff
    'local': True,
    'num_events': 1,
    'fresh_input': True,
    'starting_row': 0,
    'points_in_scan': 4,
    'mode': 2
    }