import numpy as np
import pandas as pd
import networkx as nx

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
        
    return np.mean(N_transmissions), df

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

def get_transmission_chain(model, schedule):
    tm_events = pd.DataFrame()
    location_types = {'student_student_same_class':'class',
                      'student_student_other_class':'hallway',
                      'student_teacher':'class',
                      'teacher_teacher':'faculty_room',
                      'student_family':'home',
                      'family_family':'home'}

    for a in model.schedule.agents:
        if a.transmissions > 0:
            for target, day in a.transmission_targets.items():
                location = ''
                hour = np.nan
                target = get_agent(model, target)
                
                ## determine transmission locations and times
                # transmissions from students to other students, teachers or family
                # members
                if a.type == 'student':
                    student_class = model.G.nodes(data=True)[a.ID]['unit']
                    
                    if target.type == 'student':
                        target_class = model.G.nodes(data=True)[target.ID]['unit']
                        
                        # transmission between students in the same class
                        if student_class == target_class:
                            location = 'class_{}'.format(student_class)
                            # pick an hour in which the students are in the same
                            # room at random
                            hour = np.random.choice([1, 2, 3, 4, 6, 7, 8, 9], 1)[0]
                            
                        # transmission between students in different classes:
                        # transmission occurs in the hallway during lunch
                        else:
                            location = 'hallway'
                            hour = 5
                        
                    # transmissions from students to teachers occur in the student's
                    # classroom at a time when the teacher is in that classroom
                    # according to the schedule
                    elif target.type == 'teacher':
                        location = 'class_{}'.format(student_class)
                        hour = schedule.loc[target.ID, '{}'.format(student_class)]
                    
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
                        student_class = model.G.nodes(data=True)[target.ID]['unit']
                        location = 'class_{}'.format(student_class)
                        hour = schedule.loc[a.ID, '{}'.format(student_class)]
                        
                    # transmissions between teachers occur during the lunch break
                    # in the faculty room
                    elif target.type == 'teacher':
                        location = 'faculty_room'
                        hour = 5
                        
                    elif target.type == 'family_member':
                        print('this should not happen!')
                        
                    else:
                        print('agent type not supported')

                # transmissions from family members to other family members
                elif a.type == 'family_member':
                    if target.type == 'student':
                        print('this should not happen!')
                        
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
                    'day':day,
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
        return tm_events
    else:
        return None

def get_ensemble_observables_school(model, run):
    R0, _ = calculate_finite_size_R0(model)
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

    row = {'run':run, 
          'R0':R0,
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
          'duration':duration}

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
            
    return pickle.load(open(join(res_path + '/tmp', \
                       'run_{}_N_{}.p'.format(run, medians[run])), 'rb'))

def dump_JSON(path, classes, students, floors,
              test_type, test_turnover, index_case, screen_frequency_student, 
              screen_frequency_teacher, mask, half_classes,
              network, node_list, schedule, observables, rep_transmission_events):
    
    node_list = node_list.to_json()
    schedule = schedule.to_json()
    try:
        rep_transmission_events = rep_transmission_events.to_json()
    except AttributeError:
        pass
    network = nx.node_link_data(network, attrs=None)
    
    data = {'classes':classes,
            'students':students,
            'floors':floors,
            'testtype':test_type,
            'testturnover':test_turnover,
            'indexcase':index_case,
            'screenfrequencyteacher':screen_frequency_teacher,
            'screenfrequencystudent':screen_frequency_student,
            'mask':mask,
            'halfclasses':half_classes,
            'network':network,
            'nodelist':node_list,
            'schedule':schedule,
            'observables':observables,
            'reptransevents':rep_transmission_events}
    
    with open(join(path, 'classes-{}_students-{}_floors-{}_testtype-{}'
                   .format(classes, students, floors, test_type) + \
                   '_testturnover-{}_indexcase-{}_screenfrequencyteacher-{}'
                   .format(test_turnover, index_case, screen_frequency_teacher) +\
                   '_screenfrequencystudent-{}_mask-{}_halfclasses-{}.txt'\
                   .format(screen_frequency_student, mask, half_classes)),'w')\
                   as outfile:
        json.dump(data, outfile)