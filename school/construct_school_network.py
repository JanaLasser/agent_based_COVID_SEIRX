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


def get_age_distribution(school_type, age_bracket, N_classes):
    '''
    Given a school type (that sets the age-range of the students in the school),
    distributes the available age-brackets evenly over the number of classes.
    Returns a dictionary of the form {class:age}
	'''

    classes = list(range(1, N_classes + 1))
    N_age_bracket = len(age_bracket)
    classes_per_age_bracket = int(N_classes / N_age_bracket)
    
    assert N_age_bracket <= N_classes, \
    'not enough classes to accommodate all age brackets in this school type!'
    
    age_bracket_map = {i:[] for i in age_bracket}
    
    # easiest case: the number of classes is divisible by the number of floors
    if N_classes % N_age_bracket == 0:
        for i, age_bracket in enumerate(age_bracket):
            age_bracket_map[age_bracket] = classes[i * classes_per_age_bracket: \
                                    i * classes_per_age_bracket + classes_per_age_bracket]
        
    # if there are leftover classes: assign them one-by-one to the existing 
    # age brackets, starting with the lowest
    else:
        leftover_classes = N_classes % N_age_bracket
        classes_per_age_bracket += 1
        for i, age_bracket in enumerate(age_bracket):
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



def generate_student_family(age_bracket, p_children, p_parents):
    '''
    Generates families with sizes approximating the Austrian household statistics
    2019 for families with at least one child for the purpose of creating families
    of pupils in schools generated for pandemic spread simulations.
    Families that have no children that are eligible to go to the school
    type that is being created (age_bracket) are discarded until a family with 
    at least one child with a suitable age is created. Ages of children are 
    drawn from a uniform distribution between 0 and 18 years. 
    
    Parameters:   * age_bracket (list) list of ages present in the school to be 
                    generated.
                  * p_children (dictionary) probabilities for the number of 
                    children in a family household, given that there is at least 
                    one child.
                  * p_parents (dictionary) given the number of children, 
                    probability that the family has 1 or 2 parents.
                     
    returns:      * ages (list), ages of the children in the generated family
                  * N_parents (integer), number of parents (1 or 2) in the family
    '''
    N_children = np.random.choice(list(p_children.keys()), p=list(p_children.values()))
    N_parents = np.random.choice(list(p_parents[N_children].keys()),
                                p=list(p_parents[N_children].values()))

    while True:
        # random ages of children from uniform distribution
        ages = np.random.randint(0, 17, N_children)
        # does at least one child qualify to go to the school?
        if len(set(age_bracket).intersection(set(ages))) > 0:
            return ages, N_parents



def generate_teacher_family(p_adults, p_children):
    '''
    Generates families with sizes approximating the Austrian household statistics
    2019 for the purpose of generating families of teachers in schools generated
    for pandemic spread simulations. Ages of children are drawn from a uniform 
    distribution between 0 and 18 years. 
    
    Parameters:   * p_adults (dictionary) probabilities for the number of 
                    adults in a family household.
                  * p_children (dictionary) given the number of adults, 
                    probability that the family has 1, 2 or 3 children.
                     
    returns:      * ages (list), ages of the children in the generated family
                  * N_adults (integer), number of adults (1, 2 and 3) in the family
    '''
    N_adults = np.random.choice(list(p_adults.keys()), p=list(p_adults.values()))
    N_children = np.random.choice(list(p_children[N_adults].keys()),
                                p=list(p_children[N_adults].values()))
    
    ages = np.random.randint(0, 17, N_children)
    return ages, N_adults


def generate_students(G, school_type, age_bracket, N_classes, class_size,\
                      p_children, p_parents):

    '''
    Generates students and their families and adds them and their household
    connections to the graph. 
    
    Parameters:   * G (networkx graph) graph with all agents (nodes) and 
                    contacts between agents (edges).
                  * school_type (str) type of the school for which students
                    will be generated.
                  * age_bracket (list) list of ages that are taught in the given
                    school type
                  * N_classes (int) number of classes in the school
                  * class_size (int) number of students per class
                  * p_children (dictionary), probabilities for families to have
                    a number of children, given they have at least one.
                  * p_parents (dictionary), probabilities for families to have
                    one or two parents, given the number of children.
                    
    returns:      * family_member_counter (int), counter of family members 
                    generated.
                  * family_counter (int), counter of families created
    '''

    # mapping of classes to ages
    age_bracket_map = get_age_distribution(school_type, age_bracket, N_classes)

    # number of students of every age group required to fill all classes of the school
    N_target_students = {age:0 for age in age_bracket_map.values()}
    for age in age_bracket_map.values():
        N_target_students[age] += class_size 

    N_current_students = {i:0 for i in age_bracket}
    student_counter = 1
    family_counter = 1
    family_member_counter = 1

    while (np.asarray([N_target_students[age] for age in age_bracket]) - \
          np.asarray([N_current_students[age] for age in age_bracket])).sum() > 0:


        ages, N_parents = generate_student_family(age_bracket, p_children, p_parents)
        # children
        # set a flat if at least one of the children fits into the school. Else the
        # family has to be discarded and a new one created
        fits_in_school = []
        doesnt_fit = []
        student_nodes = []
        family_nodes = []
        for age in ages:
            # there is room for a student with the given age in the school ->
            # add the node to the graph as student
            if age in age_bracket and N_current_students[age] < N_target_students[age]:
                student_ID = 'S{}'.format(student_counter)
                G.add_node(student_ID)
                nx.set_node_attributes(G, \
                        {student_ID:{'type':'student',
                                     'age':age,
                                     'family':family_counter}})
                student_counter += 1
                fits_in_school.append(age)
                student_nodes.append(student_ID)
                N_current_students[age] += 1
            else:
                doesnt_fit.append(age)

        # at least one of the children did fit into the school:
        if len(fits_in_school) > 0:
            # add the students that didn't fit into the school as family members
            for age in doesnt_fit:
                family_member_ID = 'f{}'.format(family_member_counter)
                G.add_node(family_member_ID)
                nx.set_node_attributes(G, \
                        {family_member_ID:{'type':'family_member',
                                           'age':age,
                                           'family':family_counter}})
                family_nodes.append(family_member_ID)
                family_member_counter += 1

            # parents
            for parent in range(N_parents):
                family_member_ID = 'f{}'.format(family_member_counter)
                G.add_node(family_member_ID)
                nx.set_node_attributes(G, \
                        {family_member_ID:{'type':'family_member',
                         				   'age':30,
                                           'family':family_counter}})
                family_member_counter += 1
                family_nodes.append(family_member_ID)

            # increase the family counter by one
            family_counter += 1

        # add intra-family contacts (network connections)
        all_nodes = []
        all_nodes.extend(student_nodes)
        all_nodes.extend(family_nodes)

        for n1 in all_nodes:
            for n2 in all_nodes:
                if n1 != n2:
                    G.add_edge(n1, n2, link_type='student_household')
                    
    return family_member_counter, family_counter



def generate_classes(G, age_bracket, class_size, floor_map):
    
    '''
    Assigns students to classes based on their age. 
    
    Parameters:   * G (networkx graph) graph with all agents (nodes) and 
                    contacts between agents (edges).
                  * age_bracket (list) list of ages that are taught in the given
                    school type
                  * class_size (int) number of students per class
                  * floor_map (dictionary), mapping of classes to floors in the
                    school building.
    '''

    all_students = {age:[] for age in age_bracket}
    class_counter = 1
    sequential_students = []

    for age in age_bracket:
        # get all student nodes with one age
        all_students[age] = [n[0] for n in G.nodes(data=True) if \
                             n[1]['type'] == 'student' and n[1]['age'] == age]
        sequential_students.extend(all_students[age])

        # split the students of the same ages into classes of size class_size
        for i in range(int(len(all_students[age]) / class_size)):
            students_in_class = all_students[age][i * class_size: (i + 1) * class_size]

            for s1 in students_in_class:
                # add class information to student node in graph
                nx.set_node_attributes(G, {s1:{
                                'unit':'class_{}'.format(class_counter),
                                'floor':floor_map[class_counter]}})

                # add intra_class links between all students in the same class
                for s2 in students_in_class:
                    if s1 != s2:
                        G.add_edge(s1, s2, link_type='student_student_intra_class')

            # add table neighbour relations to students in a ring
            for i, n in enumerate(students_in_class[0:-1]):
                G[students_in_class[i - 1]][n]['link_type'] = \
                                'student_student_table_neighbour'
                G[students_in_class[i + 1]][n]['link_type'] = \
                                'student_student_table_neighbour'
            # add the contacts for the last student separately, since this would
            # exceed the list indexing otherwise
            G[students_in_class[0]][students_in_class[-1]]['link_type'] = \
                            'student_student_table_neighbour'

            class_counter += 1

    # relabel nodes, making sure the student node label increases sequentially
    # from class 1 to class N
    new_student_IDs = {s:'s{}'.format(i + 1) for i, s in enumerate(sequential_students)}
    nx.relabel_nodes(G, new_student_IDs, copy=False)



def generate_teachers(G, teacher_nodes, family_member_counter, family_counter,
					  teacher_p_adults, teacher_p_children):
    
    '''
    Generates a family for every teacher and adds the family nodes and household
    connections to the graph. NOTE: we do not use the children of teacher's 
    families as pupils for the school we create. This has two reasons: 
    (a) teachers are discouraged to send their own children to the same school
    they work at, to prevent a conflict of interest. (b) the simulation becomes
    a little less complex this way.
    
    Parameters:   * G (networkx graph) school contact network
                  * teacher_nodes (list of strings), labels of the teacher nodes
                  * family_member_counter (int) counter for the number of family 
                    members already in the graph. Used to create unique labels
                    for family members.
                  * family_counter (int) counter for the number of families in
                    the graph. Used to create a unique label for every family.
                  * teacher_p_adults (dictionary) probabilites of a teacher
                    household having a number of adults
                  * teacher_p_children (dictionary) probabilities of a teacher
                    household having a number of children given the numebr of
                    adults.
                     
    '''
    G.add_nodes_from(teacher_nodes)
    
    for t in teacher_nodes:
        family_nodes = [t]
        # draw a random number of children and adults for the family
        ages, N_adults = generate_teacher_family(teacher_p_adults, teacher_p_children)
        
        ages = list(ages)
        for adult in range(N_adults - 1):
            ages.append(30) # default age for adults
        
        # add the family member nodes and their attributes to the graph
        for age in ages:
            family_member_ID = 'f{}'.format(family_member_counter)
            family_nodes.append(family_member_ID)
            G.add_node(family_member_ID)
            family_member_counter += 1
            nx.set_node_attributes(G, \
                        {family_member_ID:{'type':'family_member',
                                           'age':age,
                                           'family':family_counter}})

        # create household connections between all family members
        for f1 in family_nodes:
            for f2 in family_nodes:
                if f1 != f2:
                    G.add_edge(f1, f2, link_type='teacher_household')
                    
        # finally, also set the teacher's node attributes
        nx.set_node_attributes(G, \
                    {t:{'type':'teacher', 
                        'age':30,
                        'unit':'faculty_room',
                        'family':family_counter}})
        family_counter += 1



def generate_teacher_contacts(G, teacher_nodes, N_teacher_contacts_far, \
                              N_teacher_contacts_intermediate):
    # total number of unique far contacts that will be generated
    N_teachers = len(teacher_nodes)
    N_teacher_contacts_far = (N_teacher_contacts_far * N_teachers) / 2
    contacts_created = 0
    while contacts_created < N_teacher_contacts_far:
        t1 = np.random.choice(teacher_nodes)
        t2 = np.random.choice(teacher_nodes)
        if t1 == t2:
            continue

        if not G.has_edge(t1, t2):
            G.add_edge(t1, t2, link_type='teacher_teacher_short')
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
            G.add_edge(t1, t2, link_type='teacher_teacher_long')
            contacts_created += 1


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

	schedule_df = schedule_df.drop(columns=['teacher'])

	return schedule_df


def generate_schedule_primary_daycare(N_classes, class_size):

	## teacher schedule
	N_teachers = N_classes * 2
	teacher_nodes = ['t{}'.format(i) for i in range(1, N_teachers + 1)]

	teacher_schedule = {t:[] for t in teacher_nodes}

	# the first two hours are taught by teachers 1 to N_classes:
	for i in range(1, N_classes + 1):
		teacher_schedule['t{}'.format(i)].extend([i] * 2)
	for i in range(N_classes + 1, N_classes * 2 + 1):
		teacher_schedule['t{}'.format(i)].extend([pd.NA] * 2)
	# the third hour is also taught by teachers 1 to N_classes, but classes
	# are shifted:
	for i in range(1, N_classes + 1):
		teacher_schedule['t{}'.format(i)].append(i % N_classes + 1)
	for i in range(N_classes + 1, N_classes * 2 + 1):
		teacher_schedule['t{}'.format(i)].append(pd.NA)
	    
	# the fourth hour is taught by teachers N_classes + 1 to N_classes * 2
	for i, j in enumerate(range(N_classes + 1, N_classes * 2 + 1)):
		teacher_schedule['t{}'.format(j)].append(i + 1)
	for i in range(1, N_classes + 1):
		teacher_schedule['t{}'.format(i)].append(pd.NA)
	    
	# the afternoon supervision is done by teachers N_classes + 1 to N_classes * 2
	# and every two teachers supervise a group
	for i, j in enumerate(range(N_classes + 1, N_classes * 2 + 1)):
		teacher_schedule['t{}'.format(j)].append(int(i / 2 + 1))
	for i in range(1, N_classes + 1):
		teacher_schedule['t{}'.format(i)].append(pd.NA)
	    
	teacher_schedule_df = pd.DataFrame(columns=['teacher'] + \
								['hour_{}'.format(i) for i in range(1, 5)])
	teacher_schedule_df['teacher'] = teacher_nodes
	teacher_schedule_df.index = teacher_nodes
	for t in teacher_nodes:
		for hour, c in enumerate(teacher_schedule[t]):
			teacher_schedule_df.loc[t, 'hour_{}'.format(hour + 1)] = c
	        
	teacher_schedule_df = teacher_schedule_df.rename(columns={'hour_5':'afternoon'})
	teacher_schedule_df = teacher_schedule_df.drop(columns=['teacher'])

	## student schedule
	# pick half of the students at random to participate in full daycare
	student_nodes = ['s{}'.format(i) for i in range(1, N_classes * class_size + 1)]
	full_day_care_students = np.random.choice(student_nodes, \
	                            int((N_classes * class_size) / 2), replace=False)
	non_day_care_students = [s for s in student_nodes if s not in full_day_care_students]

	student_schedule = {s:[] for s in student_nodes}
	daycare_counter = 0
	for i, s in enumerate(student_nodes):
		student_schedule[s].append(int(i/class_size) + 1)
	for i, s in enumerate(full_day_care_students):
		student_schedule[s].append(int(i/class_size) + 1)
	for s in non_day_care_students:
		student_schedule[s].append(pd.NA)

	student_schedule_df = pd.DataFrame(columns=['student', 'morning', 'afternoon'])
	student_schedule_df['student'] = student_nodes
	student_schedule_df.index = student_nodes
	for s in student_nodes:
	    for i, daytime in enumerate(['morning', 'afternoon']):
	        student_schedule_df.loc[s, daytime] = student_schedule[s][i]

	return teacher_schedule_df, student_schedule_df


def generate_schedule_lower_secondary(N_classes):
	pass
def generate_schedule_lower_secondary_daycare(N_classes, class_size):
	pass
def generate_schedule_upper_secondary(N_classes):
	pass
def generate_schedule_secondary(N_classes):
	pass


def get_N_teachers(school_type, N_classes):
	teachers = {
	'primary':N_classes + int(N_classes / 2),
	'primary_dc':N_classes * 2,
	'lower_secondary':N_classes * 2,
	'lower_secondary_dc':N_classes * 2,
	'upper_secondary':N_classes * 2,
	'secondary':N_classes * 2
	}
	return teachers[school_type]


def set_teacher_student_contacts(G, school_type, N_classes, class_size):
	schedulers = {
		'primary':generate_schedule_primary,
		'primary_dc':generate_schedule_primary_daycare,
		'lower_secondary':generate_schedule_lower_secondary,
		'lower_secondary_dc':generate_schedule_lower_secondary_daycare,
		'upper_secondary':generate_schedule_upper_secondary,
		'secondary':generate_schedule_secondary
	}

	N_teachers = get_N_teachers(school_type, N_classes)
	teacher_nodes = ['t{}'.format(i) for i in range(1, N_teachers + 1)]

	# school types with daycare are handled separately, because they need an
	# additional schedule for students in the afternoon
	if school_type.endswith('_dc'):
		teacher_schedule_df, student_schedule_df = \
			schedulers[school_type](N_teachers, class_size)

		# morning classes: create links between the teachers and all students
		# in the classes taught by the teachers
		for t in teacher_nodes:
			classes_taught = teacher_schedule_df\
				.drop(columns=['afternoon'])\
				.loc[t]\
				.dropna()\
				.unique()
			for c in classes_taught:
				students_in_class = [x for x,y in G.nodes(data=True) if \
		                            (y['type'] == 'student') and \
		                             y['unit'] == 'class_{}'.format(c)]
				for s in students_in_class:
					G.add_edge(t, s, link_type='teaching_teacher_student')

		# afternoon supervision: create links between the teachers supervising
		# the afternoon groups and all students in the afternoon groups. Note:
		# the information about which students are in which afternoon group are
		# taken from the student schedule, because students are assigned to
		# afternoon groups at random.
		for t in teacher_nodes:
			supervised_group = teacher_schedule_df.loc[t, 'afternoon']
			if not pd.isna(supervised_group):
				students_in_group = [s for s in student_schedule_df.index if \
	    			not pd.isna(student_schedule_df.loc[s, 'afternoon']) and \
	                student_schedule_df.loc[s, 'afternoon'] == supervised_group]

				for s in students_in_group:
					G.add_edge(t, s, link_type='supervision_teacher_student')

		return teacher_schedule_df, student_schedule_df

	else:    
		return teacher_schedule_df


def compose_school_graph(school_type, N_classes, class_size, N_floors, 
		age_bracket, student_p_children, student_p_parents,
		teacher_p_adults, teacher_p_children, 
        r_teacher_conversation, r_teacher_friend):
    # number of teachers in a school
    N_teachers = get_N_teachers(school_type, N_classes)
    N_teacher_contacts_far = round(N_teachers * r_teacher_conversation)
    N_teacher_contacts_intermediate = round(N_teachers * r_teacher_friend)
    
    # distribution of classes over the available floors and neighborhood 
    # relations of classes based on spatial proximity
    floors, floors_inv = get_floor_distribution(N_floors, N_classes)
    age_bracket_map = get_age_distribution(school_type, age_bracket, N_classes)
    
    # compose the graph
    G = nx.Graph()

    # add students, their families and household contacts in student families
    family_member_counter, family_counter = generate_students(G, school_type, 
	                    age_bracket, N_classes, class_size, student_p_children, 
	                    student_p_parents)
    
    # assign students to classes and generate intra-class contacts
    generate_classes(G, age_bracket, class_size, floors_inv)

    # add teachers, teacher families and household contacts in teacher families
    teacher_nodes = ['t{}'.format(i) for i in range(1, N_teachers + 1)]
    generate_teachers(G, teacher_nodes, family_member_counter, family_counter, 
    					teacher_p_adults, teacher_p_children)

    # add contacts between teachers and other teachers
    schedules = generate_teacher_contacts(G, teacher_nodes, N_teacher_contacts_far,
                         N_teacher_contacts_intermediate)

    # add contacts between teachers and students
    set_teacher_student_contacts(G, school_type, N_classes, class_size)


    
    return G, schedules


def map_contacts(G, student_mask, teacher_mask, contact_map):
    '''
    Maps the different link types between agents to contact types None, far, 
    intermediate and close, depending on link type and mask wearing. Contact
    types are added to the graph as additional edge attributes, next to link
    types.

    Parameters:   * G (networkx graph) school contact network
    			  * student_mask (bool) indicator if students are wearing masks
    			  * teacher_mask (bool) indicator if teachers are wearing masks
                  * contact_map (dict of dicts) dictionary that contains a
                    dictionary with two entries (mask, no mask) for every link
                    type, specifying the contact type in the given link type + 
                    mask wearing scenario.
                     
    '''

    # links for which purely student mask wearing is important to determine the
    # contact type
    student_links = [c for c in contact_map.keys() if c.startswith('student_')]
    # links for which purely teacher mask wearing is important to determine the
    # contact type
    teacher_links = [c for c in contact_map.keys() if c.startswith('teacher_')]
    # links for which mask wearing behavuour of both students and teachers is
    # important to determine the contact type
    student_teacher_links = ['teaching_teacher_student', 'supervision_teacher_student']

    for n1, n2 in G.edges():
        link_type = G[n1][n2]['link_type']
        if link_type in student_links:
            mask = student_mask
        elif link_type in teacher_links:
            mask = teacher_mask
        # only if BOTH students and teachers are wearing masks, the contact type
        # is considered to be less close
        elif link_type in student_teacher_links:
            if student_mask and teacher_mask:
                mask = True
            else:
                mask = False
        else:
            print('unknown link type')
            
        G[n1][n2]['contact_type'] = contact_map[link_type][mask]



def get_node_list(G):
	node_list = pd.DataFrame()
	for n in G.nodes(data=True):
	    if n[1]['type'] == 'student':
	        l = n[1]['unit']
	        f = n[1]['family']

	    elif n[1]['type'] == 'teacher':
	        l = 'faculty_room'
	        f = n[1]['family']
	    else:
	        l = 'home'
	        f = n[1]['family']

	    node_list = node_list.append({'ID':n[0],
	                                  'type':n[1]['type'],
	                                  'location':l,
	                                  'family':f}, ignore_index=True)

	node_list['family'] = node_list['family'].astype(int)

	return node_list



### deprecated
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


def generate_teachers_(G, N_classes, school_type, N_teacher_contacts_far, 
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
	N_teachers = get_N_teachers(school_type, N_classes)
	assert N_teachers > N_teacher_contacts_far + N_teacher_contacts_intermediate,\
	'total number of teachers needs to be larger than the total number of contacts every teacher has to other teachers'

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
    