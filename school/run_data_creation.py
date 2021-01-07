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
s_screen_range = [None, 7]
t_screen_range = [None, 7]
# test technologies (and test result turnover times) used in the
# different scenarios
test_types = ['same_day_antigen']
# specifies whether the index case will be introduced via an
# employee or a resident
index_cases = ['student', 'teacher']
# specifies whether teachers wear masks
student_masks = [True, False]
teacher_masks = [True, False]
half_classes = [True, False]
transmission_risk_ventilation_modifiers = [1, 0.36]

params = [(i, j, k, l, m, n, o, p)\
              for i in test_types \
              for j in index_cases \
              for k in s_screen_range \
              for l in t_screen_range \
              for m in student_masks \
              for n in teacher_masks \
              for o in half_classes \
              for p in transmission_risk_ventilation_modifiers]

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

def set_multiindex(df, agent_type):
    tuples = [(wd, a) for wd, a in zip(df['weekday'], df[agent_type])]
    index = pd.MultiIndex.from_tuples(tuples)
    df.index = index
    df = df.drop(columns=['weekday', agent_type])
    return df

def sample_prevention_strategies(screen_params, school, agent_types, measures, 
                                 model_params, res_path, runs):
    # maximum number of steps in a single run. A run automatically stops if the 
    # outbreak is contained, i.e. there are no more infected or exposed agents.
    N_steps = 1000 
    
    ## data I/O
    stype = school['type']
    # construct folder for results if not yet existing
    sname = '{}_classes-{}_students-{}'.format(\
        stype, school['classes'], school['students'])
    spath = join(res_path, join('results/{}/representative_runs'\
                      .format(stype), sname))
    spath_ensmbl = join(res_path,'results/{}/ensembles'.format(stype))

    try:
        os.mkdir(spath)
    except FileExistsError:
        pass   

    node_list = pd.read_csv(join(res_path + '/node_lists/{}'.format(stype),\
                                 '{}_node_list.csv'.format(sname)))

    ## scan of all possible parameter combinations of additional prevention measures
    observables = pd.DataFrame()
    k = 0
    for ttype, index_case, s_screen_interval, t_screen_interval, student_mask, \
                teacher_mask, half_classes, ventilation_mod in screen_params:
        print('{} / {}'.format(k, len(screen_params)))
        k += 1
        
        turnovers = {'same':0, 'one':1, 'two':2, 'three':3}
        turnover, _, test = ttype.split('_')
        turnover = turnovers[turnover]
        
        half = ''
        if half_classes:
            half = '_half'
            
        # load the contact network, schedule and node_list corresponding to the school
        G = nx.readwrite.gpickle.read_gpickle(\
                join(res_path + '/networks/{}'.format(stype),\
                '{}_network{}.gpickle'.format(sname, half)))
            
        student_schedule = pd.read_csv(\
                join(res_path + '/schedules/{}'.format(stype),\
                '{}_students_schedule{}.csv'.format(sname, half)))
        student_schedule = set_multiindex(student_schedule, 'student')
        
        teacher_schedule = pd.read_csv(\
                join(res_path + '/schedules/{}'.format(stype),\
                '{}_teachers_schedule.csv'.format(sname)))
        teacher_schedule = set_multiindex(teacher_schedule, 'teacher')

        agent_types['student']['screening_interval'] = s_screen_interval
        agent_types['teacher']['screening_interval'] = t_screen_interval
        agent_types['student']['mask'] = student_mask
        agent_types['teacher']['mask'] = teacher_mask

        # temporary folder for all runs in the ensemble, will be
        # deleted after a representative run is picked
        try:
            shutil.rmtree(join(spath, 'tmp'))
        except FileNotFoundError:
            pass
        os.mkdir(join(spath, 'tmp'))

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
            
            bool_dict = {True:'T', False:'F'}
            ensemble_results.to_csv(join(spath_ensmbl,  
                '{}_test-{}_turnover-{}_index-{}_tf-{}_sf-{}'\
                .format(stype, test, turnover,
                index_case[0], t_screen_interval, s_screen_interval) +\
                '_tmask-{}_smask-{}_half-{}_vent-{}.csv'.format(\
                bool_dict[teacher_mask], bool_dict[student_mask], 
                bool_dict[half_classes], ventilation_mod)))
            
            # dump the current model to later pick a representative run
            N_infected = row['infected_agents']
            with open(join(join(spath, 'tmp'),
                     'run_{}_N_{}.p'.format(r, int(N_infected))),'wb') as f:
                pickle.dump(model, f)

       # add ensemble statistics to the overall results
        row = {'test_type':test,
               'turnover':turnover,
               'index_case':index_case,
               'student_screen_interval':s_screen_interval,
               'teacher_screen_interval':t_screen_interval,
               'student_mask':student_mask,
               'teacher_mask':teacher_mask,
               'half_classes':half_classes,
               'ventilation_modification':ventilation_mod}
        
        ensemble_results = ensemble_results[ensemble_results['infected_agents'] > 0]
        for col in ensemble_results.columns:
            row.update(af.get_statistics(ensemble_results, col))
        observables = observables.append(row, ignore_index=True)
        
        # get the a representative model with the same number of infected
        # as the ensemble median
        rep_model = af.get_representative_run(row['infected_agents_median'],\
                            join(spath, 'tmp'))
        try:
            tm_events = af.get_transmission_chain(\
                        rep_model, stype, teacher_schedule, student_schedule)
        except (KeyError, IndexError) as e:
            print(e)
            return rep_model, teacher_schedule, student_schedule
        state_data = af.get_agent_states(rep_model, tm_events)
        
        duration = model.Nstep
        start_weekday = (0 + model.weekday_shift) % 7 + 1

        af.dump_JSON(spath, school, ttype, index_case, s_screen_interval, 
                     t_screen_interval, teacher_mask, student_mask, 
                     half_classes, ventilation_mod, node_list, teacher_schedule,
                     student_schedule, tm_events, state_data, start_weekday, 
                     duration)

        # save intermediate results
        screen_cols = ['test_type', 'turnover', 'index_case', 'student_screen_interval',
            'teacher_screen_interval', 'student_mask', 'teacher_mask',
            'half_classes', 'ventilation_modification']
        other_cols = [c for c in observables if c not in screen_cols]
        observables = observables[screen_cols + other_cols]
        observables.to_csv(join(join(res_path + '/results/{}/'\
                        .format(stype), 'observables'), 
                        '{}_N{}_curr.csv'.format(sname, runs)), index=False)
    
    # cleanup & save results to disk
    shutil.rmtree(join(spath, 'tmp'))
    observables.to_csv(join(join(res_path + '/results/{}/'\
                    .format(stype), 'observables'), 
                    '{}_N{}.csv'.format(sname, runs)), index=False)



    # cleanup & save results to disk
    screen_cols = ['test_type', 'turnover', 'index_case', 'student_screen_interval',
            'teacher_screen_interval', 'student_mask', 'teacher_mask',
            'half_classes', 'ventilation_modification']
    other_cols = [c for c in observables if c not in screen_cols]
    observables = observables[screen_cols + other_cols]
    observables.to_csv(join(join(res_path + '/results/{}/'\
                    .format(stype), 'observables'), 
                    '{}_N{}.csv'.format(sname, runs)), index=False)
    try:
        shutil.rmtree(join(spath, 'tmp'))
    except FileNotFoundError:
        pass


res_path = '../data/school'
school_type = sys.argv[1]
runs = int(sys.argv[2])
min_idx = int(sys.argv[3])
max_idx = int(sys.argv[4])

# school layouts
class_sizes = [10, 15, 20, 25, 30]
class_numbers = [4, 8, 12, 20, 30]
school_types = [school_type]

school_configs = [(i, j, k) for i in school_types \
                               for j in class_numbers \
                               for k in class_sizes]

school_configs = school_configs[min_idx:max_idx]

for school_type, N_classes, class_size in school_configs:
    school = {'type':school_type, 'classes':N_classes,
              'students':class_size}
    
    sample_prevention_strategies(params, 
                school, agent_types, measures, model_params, res_path, runs)
