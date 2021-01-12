import networkx as nx
import pandas as pd
import numpy as np
from os.path import join
import os
import shutil
import pickle
import json

import sys
sys.path.insert(0,'../school')
sys.path.insert(0,'../nursing_home')
from model_school import SEIRX_school
import analysis_functions as af

# screening parameters
# student and teacher streening intervals (in days)
s_screen_range = [None, 3, 7]
t_screen_range = [None, 3, 7]
# test technologies (and test result turnover times) used in the
# different scenarios
test_types = ['same_day_antigen']
# specifies whether teachers wear masks
student_masks = [True, False]
teacher_masks = [True, False]
half_classes = [True, False]
transmission_risk_ventilation_modifiers = [1, 0.36]

params = [(i, j, k, l, m, n, o)\
              for i in test_types \
              for j in s_screen_range \
              for k in t_screen_range \
              for l in student_masks \
              for m in teacher_masks \
              for n in half_classes \
              for o in transmission_risk_ventilation_modifiers]

# agents
agent_types = {
        'student':{
                'screening_interval': None, # screening param
                'index_probability': 0, # running in single index case mode
                'mask':False}, # screening param
        'teacher':{
                'screening_interval': None, # screening param
                'index_probability': 0, # running in single index case mode
                'mask':False},
        'family_member':{
                'screening_interval': None, # fixed 
                'index_probability': 0, # fixed
                'mask':False} # screening param
}

# measures
measures = {
    'testing':'preventive',
    'diagnostic_test_type':'two_day_PCR',
    'K1_contact_types':['close'],
    'quarantine_duration':10,
    'follow_up_testing_interval':None,
    'liberating_testing':False,
}

# model parameters
model_params = {
    'exposure_duration':[5.0, 1.9], # literature values
    'time_until_symptoms':[6.4, 0.8], # literature values
    'infection_duration':[10.91, 3.95], # literature values
    'subclinical_modifier':0.6, 
    'base_risk':0.0737411844049918,
    'mask_filter_efficiency':{'exhale':0.5, 'inhale':0.7},
    'infection_risk_contact_type_weights':{'very_far': 0, 'far': 0.75, 'intermediate': 0.85,'close': 1},
    'age_transmission_discount':{'slope':-0.02, 'intercept':1},
    'age_symptom_discount':{'slope':-0.02868, 'intercept':0.7954411542069012},
    'verbosity':0
}

agent_index_ratios = {
    'primary':            {'teacher':0.939394, 'student':0.060606},
    'primary_dc':         {'teacher':0.939394, 'student':0.060606},
    'lower_secondary':    {'teacher':0.568, 'student':0.432},
    'lower_secondary_dc': {'teacher':0.568, 'student':0.432},
    'upper_secondary':    {'teacher':0.182796, 'student':0.817204},
    'secondary':          {'teacher':0.362319, 'student':0.637681},
    'secondary_dc':       {'teacher':0.362319, 'student':0.637681},
}

def set_multiindex(df, agent_type):
    tuples = [(wd, a) for wd, a in zip(df['weekday'], df[agent_type])]
    index = pd.MultiIndex.from_tuples(tuples)
    df.index = index
    df = df.drop(columns=['weekday', agent_type])
    return df

def sample_prevention_strategies(screen_params, school, agent_types, measures, 
                model_params, runs, min_measure_idx, max_measure_idx, src, dst):
    # maximum number of steps in a single run. A run automatically stops if the 
    # outbreak is contained, i.e. there are no more infected or exposed agents.
    N_steps = 1000 

    screen_params = screen_params[min_measure_idx:max_measure_idx]
    
    ## data I/O
    stype = school['type']
    # construct folder for results if not yet existing
    sname = '{}_classes-{}_students-{}'.format(\
        stype, school['classes'], school['students'])

    spath_ensmbl = join(dst, 'ensembles')
    try:
        os.mkdir(spath_ensmbl)
    except FileExistsError:
        pass     

    node_list = pd.read_csv(join(src, '{}_node_list.csv'.format(sname)))

    # the index case is picked randomly, according to the empirically observed
    # distribution of index cases for a given school type
    agent_index_ratio = agent_index_ratios[school_type]
    index_case = np.random.choice(list(agent_index_ratio.keys()),
                                          p=list(agent_index_ratio.values()))

    # scan of all possible parameter combinations of additional prevention 
    # measures
    for ttype, s_screen_interval, t_screen_interval, student_mask, \
                teacher_mask, half_classes, ventilation_mod in screen_params:
        
        turnovers = {'same':0, 'one':1, 'two':2, 'three':3}
        bmap = {True:'T', False:'F'}
        turnover, _, test = ttype.split('_')
        turnover = turnovers[turnover]
        
        measure_string = '{}_test-{}_turnover-{}_index-{}_tf-{}_sf-{}_tmask-{}'\
            .format(stype, test, turnover, index_case[0], t_screen_interval,
                    s_screen_interval, bmap[teacher_mask]) +\
                    '_smask-{}_half-{}_vent-{}'\
            .format(bmap[student_mask], bmap[half_classes], ventilation_mod)
        
        half = ''
        if half_classes:
            half = '_half'
            
        # load the contact network, schedule and node_list corresponding to the 
        # school
        G = nx.readwrite.gpickle.read_gpickle(join(src, '{}_network{}.bz2'\
        			.format(sname, half)))   
        student_schedule = pd.read_csv(join(src,'{}_students_schedule{}.csv'\
        			.format(sname, half)))
        student_schedule = set_multiindex(student_schedule, 'student')
        teacher_schedule = pd.read_csv(join(src,'{}_teachers_schedule.csv'\
        			.format(sname)))
        teacher_schedule = set_multiindex(teacher_schedule, 'teacher')

        # set agent specific parameters
        agent_types['student']['screening_interval'] = s_screen_interval
        agent_types['teacher']['screening_interval'] = t_screen_interval
        agent_types['student']['mask'] = student_mask
        agent_types['teacher']['mask'] = teacher_mask

        # results of one ensemble with the same parameters
        ensemble_results = pd.DataFrame()
        for r in range(runs):
            # instantiate model with current scenario settings
            model = SEIRX_school(G, model_params['verbosity'], 
              base_transmission_risk = model_params['base_risk'], 
              testing = measures['testing'],
              exposure_duration = model_params['exposure_duration'],
              time_until_symptoms = model_params['time_until_symptoms'],
              infection_duration = model_params['infection_duration'],
              quarantine_duration = measures['quarantine_duration'],
              subclinical_modifier = model_params['subclinical_modifier'], # literature
              infection_risk_contact_type_weights = \
                    model_params['infection_risk_contact_type_weights'], # calibrated
              K1_contact_types = measures['K1_contact_types'],
              diagnostic_test_type = measures['diagnostic_test_type'],
              preventive_screening_test_type = ttype,
              follow_up_testing_interval = \
                    measures['follow_up_testing_interval'],
              liberating_testing = measures['liberating_testing'],
              index_case = index_case,
              agent_types = agent_types, 
              age_transmission_risk_discount = \
                    model_params['age_transmission_discount'],
              age_symptom_discount = model_params['age_symptom_discount'],
              mask_filter_efficiency = model_params['mask_filter_efficiency'],
              transmission_risk_ventilation_modifier = ventilation_mod,
              seed=r)

            # run the model, end run if the outbreak is over
            for i in range(N_steps):
                model.step()
                if len([a for a in model.schedule.agents if \
                    (a.exposed == True or a.infectious == True)]) == 0:
                    break

            # collect the statistics of the single run
            row = af.get_ensemble_observables_school(model, r)
            row['seed'] = r
            # add run results to the ensemble results
            ensemble_results = ensemble_results.append(row,
                ignore_index=True)
            
            ensemble_results.to_csv(join(spath_ensmbl, measure_string + '.csv'))


dst = '../data/school/results_representative_schools'
src = '../data/school/representative_schools'
runs = int(sys.argv[1])
min_idx = int(sys.argv[2])
max_idx = int(sys.argv[3])
min_measure_idx = int(sys.argv[4])
max_measure_idx = int(sys.argv[5])

# school layouts

school_configs = [
    ('primary', 8, 19),
    ('primary_dc', 8, 19),
    ('lower_secondary', 8, 18),
    ('lower_secondary_dc', 8, 18),
    ('upper_secondary', 10, 23),
    ('secondary', 28, 24),
    ('secondary_dc', 28, 24)
    ]

school_configs = school_configs[min_idx:max_idx]

for school_type, N_classes, class_size in school_configs:
    school = {'type':school_type, 'classes':N_classes,
              'students':class_size}
    
    sample_prevention_strategies(params, school, agent_types, measures, 
        model_params, runs, min_measure_idx, max_measure_idx, src, dst)




