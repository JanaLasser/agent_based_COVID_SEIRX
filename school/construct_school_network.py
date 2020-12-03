import networkx as nx
import numpy as np
import pandas as pd

def get_floor_distribution(N_floors, N_classes):
    '''
    Distribute the number of classes evenly over the number of available floors.
    Returns a dictionary of the form {floor1:[class_1, class_2, ...], ...}
    '''
    floors = {i:[] for i in range(N_floors)} # starts with 0 (ground floor)
    classes = list(range(1, N_classes + 1))
    classes_per_floor = int(N_classes / N_floors) 
    
    # easiest case: the number of classes is divisible by the number of floors
    if N_classes % N_floors == 0:
        for i, floor in enumerate(range(N_floors)):
            floors[floor] = classes[i * classes_per_floor: \
                                    i * classes_per_floor + classes_per_floor]
        
    # if there are leftover classes: assign them one-by-one to the existing 
    # floors, starting with the lowest
    else:
        leftover_classes = N_classes % N_floors
        classes_per_floor += 1
        for i, floor in enumerate(range(N_floors)):
            if i < leftover_classes:
                floors[floor] = classes[i * classes_per_floor: \
                                      i * classes_per_floor + classes_per_floor]
            # hooray, index magic!
            else:
                floors[floor] = classes[leftover_classes * classes_per_floor + \
                		(i - leftover_classes) * (classes_per_floor - 1):
                        leftover_classes * (classes_per_floor) + \
                        (i - leftover_classes) * (classes_per_floor - 1) + \
                        classes_per_floor - 1]
                
    # invert dict for easier use
    floors_inv = {}
    for floor, classes in floors.items():
        for c in classes:
            floors_inv.update({c:floor})
    
    return floors, floors_inv


def get_neighbour_classes(N_classes, floors, floors_inv, N_close_classes):
    '''
    Given the distribution of classes over floors, for every class pick 
    N_close_classes classes that are considered "neighbours" of that class.
    Returns a dictionary of the form {class:[neighbour_1, ..., neighbour_N]}
	'''
    classes = list(range(1, N_classes + 1))
    N_floors = len(floors)
    classes_per_floor = int(N_classes / N_floors) 
    assert N_close_classes <= classes_per_floor - 1, \
     'not enough classes per floor to satisfy number of neighbouring classes!'
    
    # pick the neighbouring classes from the list of classes on the same floor
    # NOTE: this does NOT lead to a uniform distribution of neighbouring classes
    # for every class. There are more central classes that will have more 
    # neighbours than other classes
    class_neighbours = {i:[] for i in classes}
    for floor in floors.keys():
        circular_class_list = floors[floor] * 2
        # iterate over all classes on a given floor
        for i,c in enumerate(floors[floor]):
            neighbours = []
            for j in range(1, int(N_close_classes / 2) + 1):
                neighbours.append(circular_class_list[i - j])
                neighbours.append(circular_class_list[i + j])
            neighbours.sort()
            class_neighbours[c] = neighbours
            
    return class_neighbours


def get_age_distribution(school_type, school_types, N_classes):
    '''
    Given a school type (that sets the age-range of the students in the school),
    distributes the available age-brackets evenly over the number of classes.
    Returns a dictionary of the form {class:age}
	'''
    classes = list(range(1, N_classes + 1))
    age_brackets = school_types[school_type]
    N_age_brackets = len(age_brackets)
    classes_per_age_bracket = int(N_classes / N_age_brackets)
    
    assert N_age_brackets <= N_classes, 'not enough classes to accommodate all age brackets in this school type!'
    
    age_bracket_map = {i:[] for i in age_brackets}
    
    # easiest case: the number of classes is divisible by the number of floors
    if N_classes % N_age_brackets == 0:
        for i, age_bracket in enumerate(age_brackets):
            age_bracket_map[age_bracket] = classes[i * classes_per_age_bracket: \
                                    i * classes_per_age_bracket + classes_per_age_bracket]
        
    # if there are leftover classes: assign them one-by-one to the existing 
    # age brackets, starting with the lowest
    else:
        leftover_classes = N_classes % N_age_brackets
        classes_per_age_bracket += 1
        for i, age_bracket in enumerate(age_brackets):
            if i < leftover_classes:
                age_bracket_map[age_bracket] = classes[i * classes_per_age_bracket: \
                                        i * classes_per_age_bracket + classes_per_age_bracket]
            # hooray, index magic!
            else:
                age_bracket_map[age_bracket] = classes[leftover_classes * classes_per_age_bracket + (i - leftover_classes) * (classes_per_age_bracket - 1):
                                        leftover_classes * (classes_per_age_bracket) + (i - leftover_classes) * (classes_per_age_bracket - 1) + classes_per_age_bracket - 1]
    
    # invert dict for easier use
    age_bracket_map_inv = {}
    for age_bracket, classes in age_bracket_map.items():
        for c in classes:
            age_bracket_map_inv.update({c:age_bracket})            
                
    return age_bracket_map_inv



def generate_class(G, class_size, student_counter, class_counter, floors, \
                   age_bracket_map):
    
    '''
    Generate the nodes for students in a class and contacts between all students
    (complete graph), given the class size. Node IDs are of the form 'si', where
    i is an incrementing global counter of students. Students have contacts of 
    'intermediate' strength to each other. Nodes get additional attributes:
        'type': is set to 'student'
        'unit': is set to the class, using the incrementing class_counter
        'floor': is the floor the class is situated on
        'age': is the age of the student

    Edges also get additional attributes indicating contact type and strength
        'link_type': 'student_student'
        'contact_type': intermediate

    Returns a graph object containing the class sub-graphs as well as the
    incremented student and class counters
    '''

    student_age = age_bracket_map[class_counter]
    class_floor = floors[class_counter]
    
    student_nodes = ['s{}'.format(i) for i in range(student_counter, \
                                student_counter + class_size )]
    G.add_nodes_from(student_nodes)
    nx.set_node_attributes(G, \
        {s:{'type':'student', 'unit':'class_{}'.format(class_counter), 
            'floor':class_floor, 'age':student_age} for s in student_nodes})
    
    for s1 in student_nodes:
        for s2 in student_nodes:
            if s1 != s2:
                G.add_edge(s1, s2, link_type='student_student',
                           contact_type='intermediate')
    return G, student_counter + class_size, class_counter + 1



def generate_family(G, student_ID, family_counter, family_sizes):
    '''
    Generate a random number of family members for every student, based on 
    household size distributions family_sizes. All family members have close 
    contacts to each other and the student. Node IDs of family members are of
    the form 'fi', where i is an incrementing global counter of family members.
    Nodes get additional attributes:
        'type': is set to 'family_member'
        'unit': is set to 'family'

    Edges also get additional attributes indicating contact type and strength:
        'link_type': 'family_family' or 'family_student', depending on relation
        'contact_type': 'close'

    Returns the graph with added family members for every student, as well as
    the incremented family member counter.
    '''

    # draw random number of family members
    N_family_members = np.random.choice(list(family_sizes.keys()), 1,
              p=[family_sizes[s] for s in family_sizes.keys()])[0]
    
    # create family nodes and add them to the graph, subtract 1 from the 
    # household size to account for the student
    family_nodes = ['f{}'.format(i) for i in \
                range(family_counter, family_counter + N_family_members - 1)]
    G.add_nodes_from(family_nodes)
    nx.set_node_attributes(G, \
        {f:{'type':'family_member', 'unit':'family'} for f in family_nodes})
    
    # all family members have contact to each other
    for f1 in family_nodes:
        for f2 in family_nodes: 
            if f1 != f2:
                G.add_edge(f1, f2, link_type='family_family', 
                           contact_type='close')
        # all family members also have contact to the student they belong to
        G.add_edge(f1, student_ID, link_type ='student_family',
                   contact_type='close')
        
    return G, family_counter + N_family_members

        
def generate_teachers(G, N_teachers, N_classes, N_classes_taught):
    '''
    Generate a number of teachers which each have contact of 'intermediate'
    strength to all other teachers and contact of 'intermediate' strength to all
    students in the classes they teach. Node IDs of teachers are of the form 
    'ti', where i is an incrementing gounter of teachers. Nodes get additional
    attributes:
        'type': 'teacher'
        'unit': 'faculty_room'

    Edges also get additional attributes indicating contact type and strength:
        'link_type': 'teacher_teacher' or 'student_teacher', depending on relation
        'contact_type': 'intermediate'

    Returns the graph with added teachers, as well as the teacher schedule 
 	'''
    teacher_nodes = ['t{}'.format(i) for i in range(1, N_teachers + 1)]
    G.add_nodes_from(teacher_nodes)
    nx.set_node_attributes(G, \
        {t:{'type':'teacher', 'unit':'faculty_room'} for t in teacher_nodes})
    
    # all teachers have contact to each other
    for t1 in teacher_nodes:
        for t2 in teacher_nodes:
            if t1 != t2:
                G.add_edge(t1, t2, link_type='teacher_teacher', 
                           contact_type='intermediate')
    
    # assign each teacher to a number of classes corresponding to the number of
    # classes taught by each teacher (N_classes_taught). 
    schedule = {t:[] for t in teacher_nodes}
    circular_class_list = list(range(1, N_classes + 1)) * 2
    for i, t in enumerate(teacher_nodes):
        schedule[t] = circular_class_list[i % N_classes:\
                                          i % N_classes + N_classes_taught]
        
    # generate the contact network between the teachers and the students in the
    # classes they teach
    for t in teacher_nodes:
        for c in schedule[t]:
            students_in_class = [x for x,y in G.nodes(data=True) if \
                                (y['type'] == 'student') and \
                                 y['unit'] == 'class_{}'.format(c)]
            
            for s in students_in_class:
                G.add_edge(t, s, link_type='student_teacher', 
                           contact_type='intermediate')
                
    return G, schedule

# add a number of random contacs between students of neighboring classes
def add_cross_class_contacts(G, N_classes, cross_class_contacts, class_neighbours):
    
    for c in range(1, N_classes + 1):
        students_in_class = [x for x,y in G.nodes(data=True) if \
                    (y['type'] == 'student') \
                             and y['unit'] == 'class_{}'.format(c)]
        
        for neighbour_class in class_neighbours[c]:
            students_in_neighbour_class = [x for x,y in G.nodes(data=True) if \
                    (y['type'] == 'student') and \
                     y['unit'] == 'class_{}'.format(neighbour_class)]

            neighbour_contacts = np.random.choice(students_in_neighbour_class,
                                        cross_class_contacts, replace=False)
            class_contacts = np.random.choice(students_in_class, 
                                        cross_class_contacts, replace=False)

            for i in range(cross_class_contacts):
                if not G.has_edge(neighbour_contacts[i], class_contacts[i]):
                    G.add_edge(neighbour_contacts[i], class_contacts[i], 
                           link_type='student_student', contact_type='far')
            
    return G


def compose_school_graph(school_type, N_classes, class_size, N_floors, 
		school_types, family_sizes):
    # number of teachers in a school
    N_teachers = N_classes * 2
    # number of teaching units / day
    N_hours = 8
    # number of classes a teacher is in contact with
    N_classes_taught = int(N_hours / 2)
    # number of neighbouring classes for each class
    N_close_classes = 2 # needs to be even
    # number of inter-class contacts for neighboring classes:
    # as each class has cross_class_contacts to each of it's N_close_classes 
    # neighbours, the total number of inter-class contacts between each pair of 
    # neighboring classes is X*Y
    cross_class_contacts = 2
    
    # distribution of classes over the available floors and neighborhood 
    # relations of classes based on spatial proximity
    floors, floors_inv = get_floor_distribution(N_floors, N_classes)
    class_neighbours = get_neighbour_classes(N_classes, floors, floors_inv, N_close_classes)
    age_bracket_map = get_age_distribution('volksschule', school_types, N_classes)
    
    # compose the graph
    G = nx.Graph()
    
    # add students
    student_counter = 1
    for c in range(1, N_classes + 1):
        G, student_counter, class_counter = generate_class(G, class_size, \
                                student_counter, c, floors_inv, age_bracket_map)

    # add teachers
    G, schedule = generate_teachers(G, N_teachers, N_classes, N_classes_taught)

    # add family members
    family_counter = 1
    students = ['s{}'.format(i) for i in range(1, N_classes * class_size + 1)]
    for s in students:
        G, family_counter = generate_family(G, s, family_counter, family_sizes)

    # create inter-class contacts
    G = add_cross_class_contacts(G, N_classes, cross_class_contacts, class_neighbours)
    
    return G, schedule

def get_node_list(G):
	node_list = pd.DataFrame()
	for n in G.nodes(data=True):
	    if n[1]['type'] == 'student':
	        location = n[1]['unit']
	    elif n[1]['type'] == 'teacher':
	        location = 'faculty_room'
	    else:
	        student = [item for sublist in G.edges('f1') for item in sublist \
	                   if item.startswith('s')][0]
	        location = 'home_{}'.format(student)
	    node_list = node_list.append({'ID':n[0],
	                                  'type':n[1]['type'],
	                                  'location':location}, ignore_index=True)

	return node_list

def get_schedule(schedule):
	teachers = list(schedule.keys())
	N_teachers = len(teachers)
	classes = list(set([i for val in schedule.values() for i in val]))
	classes.sort()
	cols = ['teacher']
	cols.extend(['class_{}'.format(i) for i in classes])
	schedule_df = pd.DataFrame(columns=cols)
	schedule_df['teacher'] = teachers
	schedule_df.index = schedule_df['teacher']
	schedule_df = schedule_df.drop(columns=['teacher'])

	# every teacher teachers a class every second hour. The first half of teachers
	# starts in the first hour, the second half of teachers starts in the second hour
	for t in teachers[0:int(N_teachers/2)]:
	    for i in range(0, 4):
	        schedule_df.loc[t, 'class_{}'.format(schedule[t][i])] = i * 2 + 1
	        
	for t in teachers[int(N_teachers/2):]:
	    for i in range(0, 4):
	        schedule_df.loc[t, 'class_{}'.format(schedule[t][i])] = i * 2 + 2

	# increment all hours after 4 by one to make room for the lunch break in the 
	# 5th hour
	for c in schedule_df.columns:
	    schedule_df[c] = schedule_df[c].apply(lambda x: x + 1 if x > 4 else x)

	return schedule_df