import numpy as np
import pandas as pd
import networkx as nx
import os
import json
import pickle
from os.path import join

import sys
sys.path.insert(0,'school')
import construct_school_network as csn

def get_agent(model, ID):
    for a in model.schedule.agents:
        if a.ID == ID:
            return a

def test_infection(a):
    if a.infectious or a.recovered or a.exposed:
        return 1
    else:
        return 0
    
def count_infected(model, agent_type):
    infected_agents = np.asarray([test_infection(a) for a in model.schedule.agents \
                         if a.type == agent_type]).sum()
    
    return infected_agents

def count_infection_endpoints(model):
    endpoints = [a for a in model.schedule.agents if a.recovered and \
         a.transmissions == 0]

    return len(endpoints)

def count_typed_transmissions(model, source_type, target_type):
    type_dict = {'t':'teacher', 's':'student', 'f':'family_member', \
        'r':'resident', 'e':'employee'}
    sources = [a for a in model.schedule.agents if a.type == source_type]
    transmissions = 0
    for source in sources:
        for target, step in source.transmission_targets.items():
            if type_dict[target[0]] == target_type:
                transmissions += 1
    return transmissions

    
def calculate_R0(model, agent_types):
    transmissions = [a.transmissions for a in model.schedule.agents]
    infected = [test_infection(a) for a in model.schedule.agents]
    IDs = [a.ID for a in model.schedule.agents]
    types = [a.type for a in model.schedule.agents]
    df = pd.DataFrame({'ID':IDs,
                       'type':types,
                       'was_infected':infected,
                       'transmissions':transmissions})
    df = df[df['was_infected'] == 1]
    overall_R0 = df['transmissions'].mean()


    R0 = {}
    for agent_type in agent_types:
        agent_R0 = df[df['type'] == agent_type]['transmissions'].mean()
        R0.update({agent_type:agent_R0})
    
    return R0

def calculate_finite_size_R0(model):
    df = pd.DataFrame(columns=['ID', 'agent_type', 't', 'target'])
    for a in model.schedule.agents:
        if a.transmissions > 0:
            for target in a.transmission_targets.keys():
                df = df.append({'ID':a.ID, 'agent_type':a.type,
                    't':a.transmission_targets[target], 'target':target},
                            ignore_index=True)
                
    # find first transmission(s)
    # NOTE: while it is very unlikely that two first transmissions occurred
    # in the same timestep, we have to account for the possibility nevertheless
    first_transmitters = df[df['t'] == df['t'].min()]['ID'].values
    N_transmissions = []
    for ft in first_transmitters:
        N_transmissions.append(len(df[df['ID'] == ft]))
    
    mean = np.mean(N_transmissions)
    if np.isnan(mean):
        return 0, df
    else:
        return mean, df

def count_infected_by_age(model, age_brackets):
	age_counts = {}
	for ab in age_brackets:
	    lower = int(ab.split('-')[0])
	    upper = int(ab.split('-')[1])
	    
	    infected = len([a for a in model.schedule.agents if a.type == 'student' and \
	               a.recovered == True and a.age >= lower and a.age <= upper])
	    
	    age_counts[ab] = infected

	return age_counts


def get_transmission_network(model):
    transmissions = []
    for a in model.schedule.agents:
        if a.transmissions > 0:
            for target in a.transmission_targets.keys():
                transmissions.append((a.ID, target))
                
    G = nx.Graph()
    G.add_edges_from(transmissions)
                
    return G

def get_statistics(df, col):
    return {
        '{}_mean'.format(col):df[col].mean(),
        '{}_median'.format(col):df[col].median(),
        '{}_0.025'.format(col):df[col].quantile(0.025),
        '{}_0.75'.format(col):df[col].quantile(0.75),
        '{}_0.25'.format(col):df[col].quantile(0.25),
        '{}_0.975'.format(col):df[col].quantile(0.975),
        '{}_std'.format(col):df[col].std(),
    }

def get_agent_states(model, tm_events):
    if type(tm_events) == type(None):
        return None
    # all agent states in all simulation steps. Agent states include the
    # "infection state" ["susceptible", "exposed", "infectious", "recovered"]
    # as well as the "quarantine state" [True, False]
    state_data = model.datacollector.get_agent_vars_dataframe()
    # remove susceptible states: these are the majority of states and since we
    # want to reduce the amoung of data stored, we will assume all agents that
    # do not have an explicit "exposed", "infectious" or "recovered" state, 
    # are susceptible.
    state_data = state_data[state_data['infection_state'] != 'susceptible']

    # we only care about state changes here, that's why we only keep the first
    # new entry in the state data table for each (agent, infection_state,
    # quarantine_state) triple. We need to reset the index once before we can
    # apply the drop_duplicates() operation, since "step" and "AgentID" are in
    # the index
    state_data = state_data.reset_index()
    state_data = state_data.drop_duplicates(subset=['AgentID',\
        'infection_state', 'quarantine_state'])

    # cleanup of index and column names to match other data output formats
    state_data = state_data.rename(columns={'AgentID':'node_ID',
                                            'Step':'day'})
    state_data = state_data.reset_index(drop=True)

    # for the visualization we need more fine-grained information (hours) on when 
    # exactly a transmission happened. This information is already stored in the
    # transmission events table (tm_events) and we can take it from there and
    # add it to the state table. We set all state changes to hour = 0 by default
    # since most of them happen at the beginning of the day (becoming infectious,
    # changing quarantine state or recovering). 
    state_data['hour'] = 1
    exp = state_data[(state_data['infection_state'] == 'exposed')]\
        .sort_values(by='day')

    # we iterate over all state changes that correspond to an exposure, ignoring
    # the first agent, since that one is the index case, whose exposure happens
    # in hour 0. We only add the hour information for the transmission events. 
    # For these events, we also subtract one from the event "day", to account 
    # for the fact that agents have to appear "exposed" in the visualization 
    # from the point in time they had contact with an infectious agent onwards. 
    for ID in exp['node_ID'][1:]:
        ID_data = exp[exp['node_ID'] == ID]
        idx = ID_data.index[0]
        hour = tm_events[tm_events['target_ID'] == ID]['hour'].values[0]
        state_data.loc[idx, 'hour'] = hour
        state_data.loc[idx, 'day'] -= 1

    # re-order columns to a more sensible order and fix data types
    state_data['hour'] = state_data['hour'].astype(int)
    state_data = state_data[['day', 'hour', 'node_ID', 'infection_state',
                                'quarantine_state']]

    return state_data


def get_transmission_chain(model, school_type, teacher_schedule, student_schedule):

    max_hours = 9
    teaching_hours = csn.get_teaching_hours(school_type)
    daycare_hours = list(range(teaching_hours + 1, max_hours + 1))
    teaching_hours = list(range(1, teaching_hours + 1))

    weekday_map = {1:'monday', 2:'tuesday', 3:'wednesday', 4:'thursday',
                   5:'friday', 6:'saturday', 7:'sunday'}
    
    if 5 in daycare_hours:
        daycare_hours.remove(5)


    tm_events = pd.DataFrame(columns=['day', 'weekday', 'hour',
        'source_ID', 'source_type', 'target_ID', 'target_type'])

    for a in model.schedule.agents:
        if a.transmissions > 0:
            for target, step in a.transmission_targets.items():
                location = ''
                hour = np.nan
                weekday =  (step + model.weekday_shift) % 7 + 1
                G = model.weekday_connections[weekday]
                target = get_agent(model, target)
                n1 = a.ID
                n2 = target.ID
                tmp = [n1, n2]
                tmp.sort()
                n1, n2 = tmp
                key = n1 + n2 + 'd{}'.format(weekday)

                s_schedule = student_schedule.loc[weekday]
                t_schedule = teacher_schedule.loc[weekday]

                ## determine transmission locations and times
                # transmissions from students to other students, teachers or family
                # members
                if a.type == 'student':
                    student_class = G.nodes(data=True)[a.ID]['unit']
                    
                    if target.type == 'student':
                        # transmussions during daycare
                        if G[a.ID][target.ID][key]['link_type'] == 'student_student_daycare':
                            location = 'class_{}'.format(s_schedule.loc[a.ID]['hour_8'])
                            hour = np.random.choice(daycare_hours)
                        # transmission during morning teaching
                        elif G[a.ID][target.ID][key]['link_type'] in \
                            ['student_student_intra_class', 'student_student_table_neighbour']:
                            hour = np.random.choice(teaching_hours)
                            location = 'class_{}'.format(s_schedule.loc[a.ID]['hour_1'])  
                        elif G[a.ID][target.ID][key]['link_type'] == 'student_household':
                            hour = 10
                            location = 'home'                     
                        else:
                            print('unknown student <-> student link type ',\
                            G[a.ID][target.ID][key]['link_type'])
                        
                    # transmissions between students and teachers occur in the student's
                    # classroom at a time when the teacher is in that classroom
                    # according to the schedule
                    elif target.type == 'teacher':
                        # transmissions during daycare
                        if G[a.ID][target.ID][key]['link_type'] == 'daycare_supervision_teacher_student':
                            location = 'class_{}'.format(s_schedule.loc[a.ID]['hour_8'])
                            hour = np.random.choice(daycare_hours)
                        elif G[a.ID][target.ID][key]['link_type'] == 'teaching_teacher_student':
                            classroom = s_schedule.loc[a.ID]['hour_1']
                            location = 'class_{}'.format(classroom)
                            # get the hour in which the teacher is teaching in the given location
                            hour = int(t_schedule.loc[target.ID][t_schedule.loc[target.ID] == classroom]\
                                .index[0].split('_')[1])                          
                        else:
                            print('unknown student <-> teacher link type', \
                                G[a.ID][target.ID][key]['link_type'])
                    
                    # transmissions to family members occur at home after schoole
                    elif target.type == 'family_member':
                        location = 'home'
                        hour = 10
                        
                    else:
                        print('agent type not supported')

                # transmissions from teachers to other teachers or students
                elif a.type == 'teacher':
                    # transmissions from teachers to students occur in the student's
                    # classroom at a time when the teacher is in that classroom
                    # according to the schedule
                    if target.type == 'student':
                        # transmissions during daycare
                        if G[a.ID][target.ID][key]['link_type'] == 'daycare_supervision_teacher_student':
                            location = 'class_{}'.format(s_schedule.loc[target.ID]['hour_8'])
                            hour = np.random.choice(daycare_hours)
                        elif G[a.ID][target.ID][key]['link_type'] == 'teaching_teacher_student':
                            classroom = s_schedule.loc[target.ID]['hour_1']
                            location = 'class_{}'.format(classroom)
                            # get the hour in which the teacher is teaching in the given location
                            hour = int(t_schedule.loc[a.ID][t_schedule.loc[a.ID] == classroom]\
                                .index[0].split('_')[1])     
                        else:
                            print('unknown teacher <-> student link type', \
                                G[a.ID][target.ID][key]['link_type'])
                        
                    # transmissions between teachers occur during the lunch break
                    # in the faculty room
                    elif target.type == 'teacher':
                        location = 'faculty_room'
                        hour = 5
                        
                    elif target.type == 'family_member':
                        location = 'home'
                        hour = 10
                        
                    else:
                        print('agent type not supported')

                # transmissions from family members to other family members
                elif a.type == 'family_member':
                    if target.type == 'student':
                        location = 'home'
                        hour = 10
                        
                    elif target.type == 'teacher':
                        print('this should not happen!')
                        
                    # transmissions between family members occur at home after school
                    elif target.type == 'family_member':
                        location = 'home'
                        hour = 10
                        
                    else:
                        print('agent type not supported')

                else:
                    print('agent type not supported')
                
                assert not np.isnan(hour), 'schedule messup!'
                assert len(location) > 0, 'location messup!'
                tm_events = tm_events.append({
                    'day':step,
                    'weekday':weekday_map[weekday], 
                    'hour':hour,
                    'location':location,
                    'source_ID':a.ID,
                    'source_type':a.type,
                    'target_ID':target.ID,
                    'target_type':target.type},
                ignore_index=True)


    if len(tm_events) > 0:            
        tm_events['day'] = tm_events['day'].astype(int)
        tm_events = tm_events.sort_values(by=['day', 'hour']).reset_index(drop=True)
        tm_events = tm_events[['day', 'hour', 'location', 'source_ID', 'source_type',
                              'target_ID', 'target_type']]
        return tm_events
    else:
        return None

def get_ensemble_observables_school(model, run):
    R0, _ = calculate_finite_size_R0(model)
    N_school_agents = len([a for a in model.schedule.agents if \
        a.type == 'teacher' or a.type == 'student'])
    N_family_members = len([a for a in model.schedule.agents if a.type == 'family_member'])
    infected_students = count_infected(model, 'student')
    infected_teachers = count_infected(model, 'teacher')
    infected_family_members = count_infected(model, 'family_member')
    infected_agents = infected_students + infected_teachers + infected_family_members
    data = model.datacollector.get_model_vars_dataframe()
    N_diagnostic_tests = data['N_diagnostic_tests'].max()
    N_preventive_screening_tests = data['N_preventive_screening_tests'].max()
    transmissions = sum([a.transmissions for a in model.schedule.agents])
    infected_without_transmissions = count_infection_endpoints(model)
    student_student_transmissions = count_typed_transmissions(model, 'student', 'student')
    teacher_student_transmissions = count_typed_transmissions(model, 'teacher', 'student')
    student_teacher_transmissions = count_typed_transmissions(model, 'student', 'teacher')
    teacher_teacher_transmissions = count_typed_transmissions(model, 'teacher', 'teacher')
    student_family_member_transmissions = count_typed_transmissions(model, 'student', 'family_member')
    family_member_family_member_transmissions = count_typed_transmissions(model, 'family_member', 'family_member')
    quarantine_days_student = model.quarantine_counters['student']
    quarantine_days_teacher = model.quarantine_counters['teacher']
    quarantine_days_family_member = model.quarantine_counters['family_member']
    pending_test_infections = data['pending_test_infections'].max()
    undetected_infections = data['undetected_infections'].max()
    predetected_infections = data['predetected_infections'].max()
    duration = len(data)
    diagnostic_tests_per_day_per_agent = N_diagnostic_tests / duration / N_school_agents
    preventive_tests_per_day_per_agent = N_preventive_screening_tests / duration / N_school_agents
    tests_per_day_per_agent = (N_diagnostic_tests + N_preventive_screening_tests) / duration / N_school_agents

    row = {'run':run, 
          'R0':R0,
          'N_school_agents':N_school_agents,
          'N_family_members':N_family_members,
          'infected_students':infected_students,
          'infected_teachers':infected_teachers,
          'infected_family_members':infected_family_members,
          'infected_agents':infected_agents,
          'N_diagnostic_tests':N_diagnostic_tests,
          'N_preventive_tests':N_preventive_screening_tests,
          'transmissions':transmissions,
          'infected_without_transmissions':infected_without_transmissions,
          'student_student_transmissions':student_student_transmissions,
          'teacher_student_transmissions':teacher_student_transmissions,
          'student_teacher_transmissions':student_teacher_transmissions,
          'teacher_teacher_transmissions':teacher_teacher_transmissions,
          'student_family_member_transmissions':student_family_member_transmissions,
          'family_member_family_member_transmissions':family_member_family_member_transmissions,
          'quarantine_days_student':quarantine_days_student,
          'quarantine_days_teacher':quarantine_days_teacher,
          'quarantine_days_family_member':quarantine_days_family_member,
          'pending_test_infections':pending_test_infections,
          'undetected_infections':undetected_infections,
          'predetected_infections':predetected_infections,
          'duration':duration,
          'diagnostic_tests_per_day_per_agent':diagnostic_tests_per_day_per_agent,
          'preventive_tests_per_day_per_agent':preventive_tests_per_day_per_agent,
          'tests_per_day_per_agent':tests_per_day_per_agent}

    return row

def get_representative_run(N_infected, path):
    filenames = os.listdir(path)
    medians = {int(f.split('_')[1]):int(f.split('_')[3].split('.')[0]) \
               for f in filenames}
    dist = np.inf
    closest_run = None
    
    for run, median in medians.items():
        if np.abs(N_infected - median) < dist:
            closest_run = run
            
    return pickle.load(open(join(path, \
                       'run_{}_N_{}.p'.format(run, medians[run])), 'rb'))

def dump_JSON(path, school,
              test_type, index_case, screen_frequency_student, 
              screen_frequency_teacher, teacher_mask, student_mask, half_classes,
              node_list, teacher_schedule, student_schedule, rep_transmission_events,
              state_data, start_weekday, duration):

    student_schedule = student_schedule.reset_index()
    teacher_schedule = teacher_schedule.reset_index()

    school_type = school['type']
    classes = school['classes']
    students = school['students']

    turnover, _, ttype = test_type.split('_')
    turnovers = {'same':0, 'one':1, 'two':2, 'three':3}
    turnover = turnovers[turnover]
    bool_dict = {True:'T', False:'F'}
    
    node_list = json.loads(node_list.to_json(orient='split'))
    del node_list['index']
    teacher_schedule = json.loads(teacher_schedule.to_json(orient='split'))
    del teacher_schedule['index']
    student_schedule = json.loads(student_schedule.to_json(orient='split'))
    del student_schedule['index']

    # can be empty, if there are no transmission events in the simulation
    try:
        rep_transmission_events = json.loads(rep_transmission_events\
            .to_json(orient='split'))
        del rep_transmission_events['index']
        state_data = json.loads(state_data.to_json(orient='split'))
        del state_data['index']
    except AttributeError:
        pass

    
    data = {'school_type':school_type,
            'classes':classes,
            'students':students,
            'test_type':ttype,
            'test_turnover':turnover,
            'indexcase':index_case,
            'screen_frequency_teacher':screen_frequency_teacher,
            'screen_frequency_student':screen_frequency_student,
            'teacher_mask':teacher_mask,
            'student_mask':student_mask,
            'half_classes':half_classes,
            'node_list':node_list,
            'teacher_schedule':teacher_schedule,
            'student_schedule':student_schedule,
            'rep_trans_events':rep_transmission_events,
            'agent_states':state_data,
            'start_weekday':start_weekday,
            'duration':duration}
    
    with open(join(path, 'test-{}_'.format(ttype) + \
                   'turnover-{}_index-{}_tf-{}_'
                   .format(turnover, index_case[0], screen_frequency_teacher) +\
                   'sf-{}_tmask-{}_smask-{}_half-{}.txt'\
                   .format(screen_frequency_student, bool_dict[teacher_mask],\
                    bool_dict[student_mask], bool_dict[half_classes])),'w')\
                   as outfile:
        json.dump(data, outfile)
