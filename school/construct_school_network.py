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


def get_age_distribution(school_type, age_brackets, N_classes):
    '''
    Given a school type (that sets the age-range of the students in the school),
    distributes the available age-brackets evenly over the number of classes.
    Returns a dictionary of the form {class:age}
	'''
    classes = list(range(1, N_classes + 1))
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
                   age_bracket_map, time_period):
    
    '''
    Generate the nodes for students in a class and contacts between all students
    (complete graph), given the class size. Node IDs are of the form 'si', where
    i is an incrementing global counter of students. Students have contacts of 
    'far' (low risk) strength to all other students, except for their two 
    closest neighbours, with whom they have 'intermediate' contacts (high risk).
    Therefore, the student network is a superposition of a ring with intermediate
    contacts and a complete graph with far contacts.

    Nodes get additional attributes:
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


    if time_period == 'calibration':
        # add contacts of type "intermediate" between all students (complete graph)
        for s1 in student_nodes:
            for s2 in student_nodes:
                if s1 != s2:
                    G.add_edge(s1, s2, link_type='student_student',
                               contact_type='intermediate')

    elif time_period == 'post_lockdown':
        # add contacts of type "far" between all students (complete graph)
        for s1 in student_nodes:
            for s2 in student_nodes:
                if s1 != s2:
                    G.add_edge(s1, s2, link_type='student_student',
                               contact_type='far')


        # generate intermediate contacts in a ring
        for i, n in enumerate(student_nodes[0:-1]):
            G[student_nodes[i-1]][n]['contact_type'] ='intermediate'
            G[student_nodes[i+1]][n]['contact_type'] ='intermediate'
        # add the contacts for the last student separately, since this would
        # exceed the list indexing otherwise
        G[student_nodes[0]][student_nodes[-1]]['contact_type'] ='intermediate'

    else:
        print('unknown time period!')


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


def generate_schedule_primary(N_classes):

	assert N_classes % 2 == 0, 'number of classes must be even'
	N_teachers = N_classes + int(N_classes / 2)
	teacher_nodes = ['t{}'.format(i) for i in range(1, N_teachers + 1)]

	schedule = {t:[] for t in teacher_nodes}

	# the first two hours are taught by teachers 1 to N_classes:
	for i in range(1, N_classes + 1):
	    schedule['t{}'.format(i)].extend([i] * 2)
	# the rest of the teachers take a break in the faculty room
	for i in range(N_classes + 1, N_teachers + 1):
	    schedule['t{}'.format(i)].extend([pd.NA] * 2)
	# the next two hours are shared between the teachers of the primary subjects
	# and additional teachers for the secondary subject, such that every teacher
	# sees a total of two different classes every day
	for i, j in enumerate(range(N_classes + 1, N_teachers + 1)):
	    schedule['t{}'.format(j)].append(i + 1)
	    schedule['t{}'.format(j)].append(i + int(N_classes / 2) + 1)
	for i,j in enumerate(range(1, int(N_classes / 2) + 1)):
	    schedule['t{}'.format(j)].append(i + int(N_classes / 2) + 1)
	    schedule['t{}'.format(j)].append(pd.NA)
	for i,j in enumerate(range(int(N_classes / 2) + 1, N_classes + 1)):
	    schedule['t{}'.format(j)].append(pd.NA)
	    schedule['t{}'.format(j)].append(i + 1)

	# convert the schedule to a data frame
	schedule_df = pd.DataFrame(columns=['teacher'] + ['hour_{}'.format(i) for i in range(1, 5)])
	schedule_df['teacher'] = teacher_nodes
	schedule_df.index = teacher_nodes
	for t in teacher_nodes:
	    for hour, c in enumerate(schedule[t]):
	        schedule_df.loc[t, 'hour_{}'.format(hour + 1)] = c

	return schedule_df


def generate_schedule_primary_daycare(N_classes):
	N_teachers = N_classes * 2
	teacher_nodes = ['t{}'.format(i) for i in range(1, N_teachers + 1)]

	schedule = {t:[] for t in teacher_nodes}

	# the first two hours are taught by teachers 1 to N_classes:
	for i in range(1, N_classes + 1):
		schedule['t{}'.format(i)].extend([i] * 2)
	for i in range(N_classes + 1, N_classes * 2 + 1):
		schedule['t{}'.format(i)].extend([pd.NA] * 2)
	# the third hour is also taught by teachers 1 to N_classes, but classes
	# are shifted:
	for i in range(1, N_classes + 1):
		schedule['t{}'.format(i)].append(i % N_classes + 1)
	for i in range(N_classes + 1, N_classes * 2 + 1):
		schedule['t{}'.format(i)].append(pd.NA)
	    
	# the fourth hour is taught by teachers N_classes + 1 to N_classes * 2
	for i, j in enumerate(range(N_classes + 1, N_classes * 2 + 1)):
		schedule['t{}'.format(j)].append(i + 1)
	for i in range(1, N_classes + 1):
		schedule['t{}'.format(i)].append(pd.NA)
	    
	# the afternoon supervision is done by teachers N_classes + 1 to N_classes * 2
	# and every two teachers supervise a group
	for i, j in enumerate(range(N_classes + 1, N_classes * 2 + 1)):
		schedule['t{}'.format(j)].append(int(i / 2 + 1))
	for i in range(1, N_classes + 1):
		schedule['t{}'.format(i)].append(pd.NA)
	    
	schedule_df = pd.DataFrame(columns=['teacher'] + ['hour_{}'.format(i) for i in range(1, 5)])
	schedule_df['teacher'] = teacher_nodes
	schedule_df.index = teacher_nodes
	for t in teacher_nodes:
		for hour, c in enumerate(schedule[t]):
			schedule_df.loc[t, 'hour_{}'.format(hour + 1)] = c
	        
	schedule_df = schedule_df.rename(columns={'hour_5':'afternoon'})

	return schedule_df


def generate_schedule_lower_secondary(N_classes):
	pass
def generate_schedule_lower_secondary_daycare(N_classes):
	pass
def generate_schedule_upper_secondary(N_classes):
	pass
def generate_schedule_secondary(N_classes):
	pass


def set_teacher_student_contacts(G, school_type):
	schedulers = {
		'primary':generate_schedule_primary,
		'primary_dc':generate_schedule_primary_daycare,
		'lower_secondary':generate_schedule_lower_secondary,
		'lower_secondary_dc':generate_schedule_lower_secondary_daycare,
		'upper_secondary':generate_schedule_upper_secondary,
		'secondary':generate_schedule_secondary
	}

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
	                       contact_type='far')
	            
	return G, schedule


	

        
def generate_teachers(G, N_classes, school_type, N_teacher_contacts_far, 
    N_teacher_contacts_intermediate):
    '''
    Generate a number of teachers which each have contact of intensity 'far'
    to N_teacher_contacts_far other teachers and contact of intensity 
    'intermediate' to N_teacher_contacts_intermediate other teachers. Node IDs 
    of teachers are of the form  'ti', where i is an incrementing gounter of 
    teachers. Nodes get additional attributes:
        'type': 'teacher'
        'unit': 'faculty_room'

    Edges also get additional attributes indicating contact type and strength:
        'link_type': 'teacher_teacher'
        'contact_strength': 'far' or 'intermediate'

    Returns the graph with added teachers
 	'''
    teacher_nodes = ['t{}'.format(i) for i in range(1, N_teachers + 1)]
    G.add_nodes_from(teacher_nodes)
    nx.set_node_attributes(G, \
        {t:{'type':'teacher', 'unit':'faculty_room'} for t in teacher_nodes})

    # total number of unique far contacts that will be generated
    N_teacher_contacts_far = (N_teacher_contacts_far * N_teachers) / 2
    contacts_created = 0
    while contacts_created < N_teacher_contacts_far:
        t1 = np.random.choice(teacher_nodes)
        t2 = np.random.choice(teacher_nodes)
        if t1 == t2:
            continue

        if not G.has_edge(t1, t2):
            G.add_edge(t1, t2, link_type='teacher_teacher', 
                           contact_type='far')
            contacts_created += 1

    # total number of unique intermediate contacts that will be generated
    N_teacher_contacts_intermediate = ( N_teacher_contacts_intermediate * N_teachers) / 2
    contacts_created = 0
    while contacts_created < N_teacher_contacts_intermediate:
        t1 = np.random.choice(teacher_nodes)
        t2 = np.random.choice(teacher_nodes)
        if t1 == t2:
            continue

        if not G.has_edge(t1, t2):
            G.add_edge(t1, t2, link_type='teacher_teacher', 
                           contact_type='intermediate')
            contacts_created += 1    

    return G
    

    

# add a number of random contacs between students of neighboring classes
def add_cross_class_contacts(G, N_classes, N_cross_class_contacts, class_neighbours):
    
    for c in range(1, N_classes + 1):
        students_in_class = [x for x,y in G.nodes(data=True) if \
                    (y['type'] == 'student') \
                             and y['unit'] == 'class_{}'.format(c)]
        
        for neighbour_class in class_neighbours[c]:
            students_in_neighbour_class = [x for x,y in G.nodes(data=True) if \
                    (y['type'] == 'student') and \
                     y['unit'] == 'class_{}'.format(neighbour_class)]

            neighbour_contacts = np.random.choice(students_in_neighbour_class,
                                        N_cross_class_contacts, replace=False)
            class_contacts = np.random.choice(students_in_class, 
                                        N_cross_class_contacts, replace=False)

            for i in range(N_cross_class_contacts):
                if not G.has_edge(neighbour_contacts[i], class_contacts[i]):
                    G.add_edge(neighbour_contacts[i], class_contacts[i], 
                           link_type='student_student', contact_type='far')
            
    return G


def compose_school_graph(school_type, N_classes, class_size, N_floors, 
		age_brackets, family_sizes, N_hours, N_cross_class_contacts, 
        N_teacher_contacts_far, N_teacher_contacts_intermediate, time_period):
    # number of teachers in a school
    N_teachers = N_classes * 2
    # number of classes a teacher is in contact with
    N_classes_taught = int(N_hours / 2)
    # number of neighbouring classes for each class
    N_close_classes = 2 # needs to be even
    
    # distribution of classes over the available floors and neighborhood 
    # relations of classes based on spatial proximity
    floors, floors_inv = get_floor_distribution(N_floors, N_classes)
    age_bracket_map = get_age_distribution(school_type, age_brackets, N_classes)
    
    # compose the graph
    G = nx.Graph()
    
    # add students
    student_counter = 1
    for c in range(1, N_classes + 1):
        G, student_counter, class_counter = generate_class(G, class_size, \
                        student_counter, c, floors_inv, age_bracket_map, time_period)

    # add teachers
    G, schedule = generate_teachers(G, N_teachers, N_classes, N_classes_taught,
        N_teacher_contacts_far, N_teacher_contacts_intermediate)

    # add family members
    if family_sizes != None:
        family_counter = 1
        students = ['s{}'.format(i) for i in range(1, N_classes * class_size + 1)]
        for s in students:
            G, family_counter = generate_family(G, s, family_counter, family_sizes)

    # create inter-class contacts
    if N_cross_class_contacts > 0:
        class_neighbours = get_neighbour_classes(N_classes, floors, floors_inv, N_close_classes)
        G = add_cross_class_contacts(G, N_classes, N_cross_class_contacts, class_neighbours)
    
    return G, schedule

def get_node_list(G):
	node_list = pd.DataFrame()
	for n in G.nodes(data=True):
	    if n[1]['type'] == 'student':
	        location = n[1]['unit']
	    elif n[1]['type'] == 'teacher':
	        location = 'faculty_room'
	    else:
	        student = [item for sublist in G.edges(n[0]) for item in sublist \
	                   if item.startswith('s')][0]
	        location = 'home_{}'.format(student)
	    node_list = node_list.append({'ID':n[0],
	                                  'type':n[1]['type'],
	                                  'location':location}, ignore_index=True)

	return node_list


