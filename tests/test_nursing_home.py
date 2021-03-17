def test_nursing_home():
    import networkx as nx

    # need to add paths to the other agent classes, because the base model class
    # still wants to import them
    import sys
    sys.path.insert(0,'src/scseirx')
    sys.path.insert(0,'src/scseirx/school')
    sys.path.insert(0,'src/scseirx/nursing_home')
    from model_nursing_home import SEIRX_nursing_home

    agent_types = {
            'employee':{
                'screening_interval': None,
                'index_probability': 0,
                'mask':False},
            'resident':{
                'screening_interval': None,
                'index_probability': 0,
                'mask':False},
    }

    measures = {
        # enables testing and tracing actions (run with testing=False) to simulate
        # unhindered spread of the virus through the nursing home
        'testing':'preventive',
        # test technology and turnover time used for preventive screening
        'preventive_screening_test_type':'same_day_antigen',
        # test technology and turnover time used for diagnostic testing
        'diagnostic_test_type':'two_day_PCR',
        # definition of contact types that will be quarantined in case one
        # of the agents in contact had a positive test result
        'K1_contact_types':['close'],
        # duration (in days) that agents will stay quarantined
        'quarantine_duration':10,
        # interval of a potential follow-up background screen (in days)
        # after a background screen that was initiated by a positive test
        'follow_up_testing_interval':None,
        # whether or not a negative test result "frees" agents from quarantine
        'liberating_testing':False,
        # modification of the transmission risk by ventilation 
        # (1 = no modification, 0.5 = risk is reduced by 50%)
        'ventilation_modification':1
    }

    model_params = {
        # mean and variance of a Weibull distribution characterizing the
        # time between transmission and becoming infectious (in days)
        'exposure_duration':[5.0, 1.9], # literature values
        # mean and variance of a Weibull distribution characterizing the
        # time between transmission and showing symptoms in clinical courses
        # of the infection (in days)
        'time_until_symptoms':[6.4, 0.8], # literature values
        # mean and variance of a Weibull distribution characterizing the
        # time between transmission and ceasing to be infectious (in days)
        'infection_duration':[10.91, 3.95], # literature values
        # modification of the transmission risk in subclinical courses
        'subclinical_modifier':0.6, 
        # base transmission risk of a contact of type "close"
        'base_risk':0.07, # artificially high, so you can see stuff happening
        # efficiency of masks (surgical), reducing the transmission risk
        # (exhale) if the source wears a mask and/or the reception risk 
        # (inhale), if the target (also) wears a mask
        'mask_filter_efficiency':{'exhale':0.5, 'inhale':0.7}, # literature values
        # modifiers of the base_risk for transmissions of contact type close
        # if the contact type is "intermediate", "far" or "very var"
        'infection_risk_contact_type_weights':\
            {'very_far':0, 'far':0.75, 'intermediate':0.85,'close':1}, 
        # agent group from which the index case is drawn
        'index_case':'employee',
        # verbosity level (can be 0, 1, 2) that prints increasingly detailed 
        # information about the simulation
        'verbosity':0
    }

    N_steps = 100
    seed = 5

    G = nx.readwrite.gpickle.read_gpickle(\
            'data/nursing_home/interactions_single_quarter.bz2')

    model = SEIRX_nursing_home(G, model_params['verbosity'], 
          base_transmission_risk = model_params['base_risk'], 
          testing = measures['testing'],
          exposure_duration = model_params['exposure_duration'],
          time_until_symptoms = model_params['time_until_symptoms'],
          infection_duration = model_params['infection_duration'],
          quarantine_duration = measures['quarantine_duration'],
          subclinical_modifier = model_params['subclinical_modifier'], 
          infection_risk_contact_type_weights = \
                model_params['infection_risk_contact_type_weights'], 
          K1_contact_types = measures['K1_contact_types'],
          diagnostic_test_type = measures['diagnostic_test_type'],
          preventive_screening_test_type = \
                measures['preventive_screening_test_type'],
          follow_up_testing_interval = \
                measures['follow_up_testing_interval'],
          liberating_testing = measures['liberating_testing'],
          index_case = model_params['index_case'],
          agent_types = agent_types, 
          mask_filter_efficiency = model_params['mask_filter_efficiency'],
          transmission_risk_ventilation_modifier = \
                measures['ventilation_modification'],
          seed=seed)

    for i in range(N_steps):
        if model_params['verbosity'] > 0: 
            print()
            print('*** step {} ***'.format(i+1))
        # break if first outbreak is over
        if len([a for a in model.schedule.agents if \
            (a.exposed == True or a.infectious == True)]) == 0:
            break
        model.step()

    data = model.datacollector.get_model_vars_dataframe()

    assert data['R_resident'].values[-1] == 29