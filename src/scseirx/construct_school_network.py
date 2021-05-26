import networkx as nx
import numpy as np
import pandas as pd

def get_N_teachers(school_type, N_classes):
	"""Return the number of teachers / class for different school types."""
	teachers = {
		'primary':N_classes + int(N_classes / 2),
		'primary_dc':N_classes * 2,
		'lower_secondary':int(N_classes * 2.5),
		'lower_secondary_dc':N_classes * 3,
		'upper_secondary':int(N_classes * 2.85),
		'secondary':int(N_classes * 2.5),
		'secondary_dc':int(N_classes * 2.5)
	}
	return teachers[school_type]


def get_daycare_ratio(school_type):
	"""Return the ratio of children in daycare in different school types."""
	daycare_ratios = {
		'primary':0,
		'primary_dc':0.5,
		'lower_secondary':0,
		'lower_secondary_dc':0.38,
		'upper_secondary':0,
		'secondary':0,
		'secondary_dc':0.36
	}
	return daycare_ratios[school_type]


def get_age_bracket(school_type):
	"""Return the age structure for different school types."""
	age_brackets = {
		'primary':[6, 7, 8, 9],
		'primary_dc':[6, 7, 8, 9],
		'lower_secondary':[10, 11, 12, 13],
		'lower_secondary_dc':[10, 11, 12, 13],
		'upper_secondary':[14, 15, 16, 17],
		'secondary':[10, 11, 12, 13, 14, 15, 16, 17],
		'secondary_dc':[10, 11, 12, 13, 14, 15, 16, 17]
	}
	return age_brackets[school_type]


def get_teaching_hours(school_type):
	"""Return the number of teaching hours / day for different school types."""
	teaching_hours = {
		'primary':4,
		'primary_dc':4,
		'lower_secondary':6,
		'lower_secondary_dc':6,
		'upper_secondary':8,
		'secondary':8,
		'secondary_dc':8
	}
	return teaching_hours[school_type]


def get_scheduler(school_type):
	"""Return the function to make the teacher schedule for different schule types."""
	schedulers = {
		'primary':generate_teacher_schedule_primary,
		'primary_dc':generate_teacher_schedule_primary_daycare,
		'lower_secondary':generate_teacher_schedule_lower_secondary,
		'lower_secondary_dc':generate_teacher_schedule_lower_secondary_daycare,
		'upper_secondary':generate_teacher_schedule_upper_secondary,
		'secondary':generate_teacher_schedule_secondary,
		'secondary_dc':generate_teacher_schedule_secondary_daycare,
	}
	return schedulers[school_type]


def get_teaching_framework():
	"""Return the parameters that structure a teaching week in Austria"""
	# maximum number of hours students spend at the school, including lunch
	# break and daycare
	max_hours = 9
	# number of days in the week
	N_weekdays = 7
	# days on which no teaching takes place
	weekend_days = [6, 7]

	return max_hours, N_weekdays, weekend_days

def get_floor_distribution(N_floors, N_classes):
	"""
	Distribute the number of classes evenly over the number of available floors.

	Parameters
	----------
	N_floors : int
		Number of available floors.
	N_classes : int
		Number of classes in the school.


	Returns
	-------
	floors : dictionary
		Dictionary of the form {floor1:[class_1, class_2, ...], ...}
	floors_inv : dictionary
		Dictionary of the form {class1:floor1, ..., class_N:floor_N}
	"""
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


def get_age_distribution(school_type, N_classes):
	"""
	Given a school type (that sets the age-range of the students in the school),
	distribute the available age-brackets evenly over the number of classes.
	Note: the number of classes needs to be >= the number of different ages
	that are taught in the given school type, such that every age is at least
	taught in one class.

	Parameters
	----------
	school_type : str
		Type of the school. Needs to be a type supported by the function
		get_age_bracket().
	N_classes : int
		Number of classes in the school.

	Returns
	-------
	age_bracket_map_inv : dict
		Dictionary of the form {class:age}.
	"""
	age_bracket = get_age_bracket(school_type)
	classes = list(range(1, N_classes + 1))
	N_age_bracket = len(age_bracket)
	classes_per_age_bracket = int(N_classes / N_age_bracket)
	
	assert N_age_bracket <= N_classes, \
	'not enough classes to accommodate all age brackets in this school type!'
	
	age_bracket_map = {i:[] for i in age_bracket}
	
	# easiest case: the number of classes is divisible by the number of floors
	if N_classes % N_age_bracket == 0:
		for i, age_bracket in enumerate(age_bracket):
			age_bracket_map[age_bracket] = classes[i * classes_per_age_bracket:\
					   i * classes_per_age_bracket + classes_per_age_bracket]
		
	# if there are leftover classes: assign them one-by-one to the existing 
	# age brackets, starting with the lowest
	else:
		leftover_classes = N_classes % N_age_bracket
		classes_per_age_bracket += 1
		for i, age_bracket in enumerate(age_bracket):
			if i < leftover_classes:
				age_bracket_map[age_bracket] = \
						classes[i * classes_per_age_bracket: \
						i * classes_per_age_bracket + classes_per_age_bracket]
			# hooray, index magic!
			else:
				age_bracket_map[age_bracket] = \
					classes[leftover_classes * classes_per_age_bracket + \
					  (i - leftover_classes) * (classes_per_age_bracket - 1):
					leftover_classes * (classes_per_age_bracket) + \
					  (i - leftover_classes) * (classes_per_age_bracket - 1) + \
					  classes_per_age_bracket - 1]
	
	# invert dict for easier use
	age_bracket_map_inv = {}
	for age_bracket, classes in age_bracket_map.items():
		for c in classes:
			age_bracket_map_inv.update({c:age_bracket})            
				
	return age_bracket_map_inv



###############################
###							###
###		agent creation 		###
###							###
###############################


def generate_student_family(school_type, p_children, p_parents):
	"""
	Generate families with sizes approximating the Austrian household statistics
	2019 for families with at least one child for the purpose of creating 
	families of pupils in schools generated for pandemic spread simulations.
	Families that have no children that are eligible to go to the school
	type that is being created (age_bracket) are discarded until a family with 
	at least one child with a suitable age is created. Ages of children are 
	drawn from a uniform distribution between 0 and 18 years. 
	
	Parameters
	----------
	school_type : str
		Type of the school. Needs to be a type supported by the function
		get_age_bracket().
	p_children : dictionary
		Probabilities for the number of children in a family household, given 
		that there is at least one child.
	p_parents : dictionary
		Given the number of children, probability that the family has 1 or 2 
		parents.
					 
	Returns
	-------
	ages : list
		Ages of the children in the generated family.
	N_parents : int
		Number of parents (1 or 2) in the family. Sorry for the approximation to
		families that have a maximum of two parents.
	"""
	age_bracket = get_age_bracket(school_type)
	N_children = np.random.choice(list(p_children.keys()), 
								  p=list(p_children.values()))
	N_parents = np.random.choice(list(p_parents[N_children].keys()),
								p=list(p_parents[N_children].values()))

	while True:
		# random ages of children from uniform distribution
		ages = np.random.randint(0, 18, N_children)
		# does at least one child qualify to go to the school?
		if len(set(age_bracket).intersection(set(ages))) > 0:
			return ages, N_parents


def generate_teacher_family(p_adults, p_children):
	"""
	Generate families with sizes approximating the Austrian household statistics
	2019 for the purpose of generating families of teachers in schools generated
	for pandemic spread simulations. Ages of children are drawn from a uniform 
	distribution between 0 and 18 years. 
	
	Parameters
	----------
	p_adults : dictionary
		Probabilities for the number of adults in a family household.
	p_children : dictionary
		Hiven the number of adults, probability that the family has 1, 2 or 3 
		children.
					 
	Returns
	-------
	ages : list
		Ages of the children in the generated family.
	N_adults : int
		Number of adults (1, 2 and 3) in the family.
	"""
	N_adults = np.random.choice(list(p_adults.keys()), p=list(p_adults.values()))
	N_children = np.random.choice(list(p_children[N_adults].keys()),
								p=list(p_children[N_adults].values()))
	
	ages = np.random.randint(0, 18, N_children)
	return ages, N_adults


def generate_students(G, school_type,N_classes,class_size,p_children,p_parents):
	"""
	Generate students and their families and add them as nodes to the graph. 
	
	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph which stores agents in the school (students, teachers, household
		members) as nodes and their contacts as edges.
	school_type : str
		Type of the school for which students will be generated. Needs to be
		supported by the function get_age_bracket().
	N_classes : int
		Number of classes in the school.
	class_size : int
		Number of students per class.
	p_children : dict
		Probabilities for families to have a number of children, given the
		precondition that they have at least one child.
	p_parents : dict
		Probabilities for families to have one or two parents, given the number 
		of children. Excuse the approximation to families with a maximum of two
		parents. 
					
	Returns
	-------
	family_member_counter : int
		Global counter of the number of family (household) members generated.
	family_counter : int
		Global counter of tne number of families (households) created.
	"""
	age_bracket = get_age_bracket(school_type)
	# mapping of classes to ages
	age_bracket_map = get_age_distribution(school_type, N_classes)

	# number of students of every age group required to fill all classes of 
	# the school
	N_target_students = {age:0 for age in age_bracket_map.values()}
	for age in age_bracket_map.values():
		N_target_students[age] += class_size 

	N_current_students = {i:0 for i in age_bracket}
	student_counter = 1
	family_counter = 1
	family_member_counter = 1

	# generate students and their families until the school is full
	while (np.asarray([N_target_students[age] for age in age_bracket]) - \
		np.asarray([N_current_students[age] for age in age_bracket])).sum() > 0:


		ages, N_parents = generate_student_family(school_type, p_children,
												  p_parents)

		# Keep the family if at least one of the children fits into the school. 
		# Else the family has to be discarded and a new one created.
		fits_in_school = []
		doesnt_fit = []
		student_nodes = []
		family_nodes = []
		for age in ages:
			# there is room for a student with the given age in the school ->
			# add the node to the graph as student
			if age in age_bracket and \
			  N_current_students[age] < N_target_students[age]:

				# Note: student IDs are created here with a big "S" at first.
				# Later on (in the function assign_classes()), students will
				# be assigned to classes and student node IDs relabelled with
				# the final small "s" such that s1 is the first student of the
				# first class and sN is the last student in the last class.
				student_ID = 'S{:04d}'.format(student_counter)
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
				family_member_ID = 'f{:04d}'.format(family_member_counter)
				G.add_node(family_member_ID)
				nx.set_node_attributes(G, \
						{family_member_ID:{'type':'family_member',
										   'age':age,
										   'family':family_counter,
										   'unit':'family'}})
				family_nodes.append(family_member_ID)
				family_member_counter += 1

			# parents
			for parent in range(N_parents):
				family_member_ID = 'f{:04d}'.format(family_member_counter)
				G.add_node(family_member_ID)
				nx.set_node_attributes(G, \
						{family_member_ID:{'type':'family_member',
											# Note: 20.5 is the age at which
											# the symptom and transmission risk
											# is that of an adult
										   'age':20.5,
										   'family':family_counter,
										   'unit':'family'}})
				family_member_counter += 1
				family_nodes.append(family_member_ID)

			# increase the family counter by one
			family_counter += 1

	return family_member_counter, family_counter


def generate_teachers(G, school_type, N_classes, family_member_counter, 
					  family_counter, teacher_p_adults, teacher_p_children):
	"""
	Generate a family for every teacher and adds the family nodes to the graph.
	NOTE: we do not use the children of teacher's families as pupils for the 
	school we create. This has two reasons: (a) teachers are discouraged to send
	their own children to the same school they work at, to prevent a conflict of
	interest. (b) the simulation becomes a little less complex this way.
	Note: modifies the graph inplace by adding teacher nodes and teacher
	household member nodes to the graph.
	
	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges. 
	school_type : str
		Type of the school that is being modelled. Needs to be supported by
		the function get_N_teachers().
	N_classes : int
		Number of classes in the school. Used to determine the number of
		teachers depending on the school type.
	family_member_counter : int
		Global counter for the number of family (household) members already in 
		the graph. Used to create unique labels for family members.
	family_counter : int
		Global counter for the number of families (households) in the graph. 
		Used to create a unique label for every family.
	teacher_p_adults : dict
		Probabilites of a teacher household having a number of adults.
	teacher_p_children : dict
		Probabilities of a teacher household having a number of children given 
		the numebr of adults as precondition.              
	"""
	N_teachers = get_N_teachers(school_type, N_classes)
	teacher_nodes = ['t{:04d}'.format(i) for i in range(1, N_teachers + 1)]
	G.add_nodes_from(teacher_nodes)
	
	for t in teacher_nodes:
		family_nodes = [t]
		# draw a random number of children and adults for the family
		ages, N_adults = generate_teacher_family(teacher_p_adults, teacher_p_children)
		
		ages = list(ages)
		for adult in range(N_adults - 1):
			ages.append(20.5) # default age for adults
		
		# add the family member nodes and their attributes to the graph
		for age in ages:
			family_member_ID = 'f{:04d}'.format(family_member_counter)
			family_nodes.append(family_member_ID)
			G.add_node(family_member_ID)
			family_member_counter += 1
			nx.set_node_attributes(G, \
						{family_member_ID:{'type':'family_member',
										   'age':age,
										   'family':family_counter,
										   'unit':'family'}})
					
		# finally, also set the teacher's node attributes
		nx.set_node_attributes(G, \
					{t:{'type':'teacher', 
						# Note: 20.5 is the age at which
						# the symptom and transmission risk
						# is that of an adult
						'age':20.5,
						'unit':'faculty_room',
						'family':family_counter}})
		family_counter += 1


def assign_classes(G, school_type, class_size, N_classes, N_floors):
	"""
	Assign students to classes according to their age. The lowest age in the
	school type's age bracket will be assigned to the first class(es), the 
	highest age to the last class(es). A number of class_size students is
	assigned to every class. Class assignment is indicated in the graph by
	adding the node attribute 'unit' = class_i to the student nodes in the 
	graph. 
	Also assign students to floors, corresponding to the floor their class is 
	on, indicated in the dictionary floor_map. Floor assignment is indicated in
	the graph by adding the node attribute 'floor' to the student nodes.
	In the end, student nodes in the graph are relabelled such that student s1 
	is the first studend in the first class and student sN is the last student 
	in the last class.
	Note: the graph is modified inplace by adding node attributes to student
	nodes.

	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges. 
	school_type : str
		Type of the school being modelled. Needs to be supported by the function
		get_age_bracket().
	class_size : int
		Number of students in one class.
	N_classes : int
		Number of classes in the school.
	N_floors : int
		Number of floors over which the classes are distributed.
	"""
	# ages that are taught in the given school type
	age_bracket = get_age_bracket(school_type)
	# distribution of classes over the available floors and neighborhood 
	# relations of classes based on spatial proximity
	floors, floors_inv = get_floor_distribution(N_floors, N_classes)

	all_students = {age:[] for age in age_bracket}
	class_counter = 1
	sequential_students = []
	_, N_weekdays, weekend_days = get_teaching_framework()

	for age in age_bracket:
		# get all student nodes with one age
		all_students[age] = [n[0] for n in G.nodes(data=True) if \
							 n[1]['type'] == 'student' and n[1]['age'] == age]
		sequential_students.extend(all_students[age])

		# split the students of the same ages into classes of size class_size
		for i in range(int(len(all_students[age]) / class_size)):
			students_in_class = all_students[age][\
				i * class_size: (i + 1) * class_size]

			for s in students_in_class:
				# add class information to student node in graph
				nx.set_node_attributes(G, {s:{
								'unit':'class_{}'.format(class_counter),
								'floor':floors_inv[class_counter]}})

			class_counter += 1

	# relabel nodes, making sure the student node label increases sequentially
	# from class 1 to class N
	new_student_IDs = {s:'s{:04d}'.format(i + 1) for i, s in \
		enumerate(sequential_students)}
	nx.relabel_nodes(G, new_student_IDs, copy=False)



###############################
###							###	
### 	contact setting 	###
###							###	
###############################

def set_family_contacts(G):
	"""
	Set the household contacts between members of the same household.
	Household contacts are the same for every day of the week. Note: modifies
	the graph inplace by creating additional edges.

	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges.
	"""
	_, N_weekdays, _ = get_teaching_framework()

	# A list with all distinct families (households) in the graph.
	families = set(dict(G.nodes(data='family')).values())

	for family in families:
		# Get all nodes that are members of this family
		family_members = [n for n, f in G.nodes(data='family') if f==family]

		# Since we differentiate between contacts in teacher households and
		# contacts in student households, we need to determine if we are
		# dealing with the former or the latter.
		link_type = None
		for f in family_members:
			if f.startswith('t'):
				link_type = 'teacher_household'
			if f.startswith('s'):
				link_type = 'student_household'

		# Links between household members form a complete subgraph of all
		# members of the household with the corresponding link type.
		for f1 in family_members:
			for f2 in family_members:
				if f1 != f2:
					# The alphabetic sorting of node IDs is necessary to ensure 
					# the edge key is always composed of the node with the lower
					# ID counter first. Otherwise we would get duplicate edges 
					# with permuted node IDs and different keys.
					tmp = [f1, f2]
					tmp.sort()
					n1, n2 = tmp
					for wd in range(1, N_weekdays + 1):
						G.add_edge(n1, n2, link_type = link_type,
										   weekday = wd,
										   key = n1 + n2 + 'd{}'.format(wd))
					


def set_student_student_intra_class_contacts(G, N_classes):
	"""
	Set links between students in the same class and (stronger) contacts
	between students that are neighbours in the seating arrangement in the 
	class. These links are only set for days on which teaching happens, i.e.
	weekdays 1-5. Note: modifies the graph inplace by adding additional edges.

	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges.
	N_classes : int
		Number of classes in the school.
	"""
	_, N_weekdays, weekend_days = get_teaching_framework()

	for wd in range(1, N_weekdays + 1):
		if wd not in weekend_days:
			wd_string = 'd{}'.format(wd)
			for c in range(1, N_classes + 1):
				students_in_class = [n for n, u in G.nodes(data='unit') if \
					u == 'class_{}'.format(c)]
				students_in_class.sort()

				# add intra_class links between all students in the same class
				# as complete subgraph
				for s1 in students_in_class:
					for s2 in students_in_class:
						if s1 != s2:
							# The alphabetic sorting of node IDs is necessary to
							# ensure the edge key is always composed of the 
							# node with the lower ID counter first. Otherwise we
							# would get duplicate edges with permuted node IDs 
							# and different keys.
							tmp = [s1, s2]
							tmp.sort()
							n1, n2 = tmp

							G.add_edge(n1, n2, \
								link_type = 'student_student_intra_class',
								weekday = wd,
								key = n1 + n2 + wd_string)

				# add table neighbour relations to students in a ring
				for i, n in enumerate(students_in_class[0:-1]):
					s1 = students_in_class[i - 1]
					tmp = [s1, n]
					tmp.sort()
					n1, n2 = tmp
					G.add_edge(n1, n2, \
						link_type = 'student_student_table_neighbour',
						weekday = wd,
						key = n1 + n2 + wd_string)

					s1 = students_in_class[i + 1]
					tmp = [s1, n]
					tmp.sort()
					n1, n2 = tmp
					G.add_edge(n1, n2, \
						link_type = 'student_student_table_neighbour',
						weekday = wd,
						key = n1 + n2 + wd_string)

				# add the contacts for the last student separately, since 
				# this would exceed the list indexing otherwise
				s1 = students_in_class[0]
				s2 = students_in_class[-1]
				tmp = [s1, s2]
				tmp.sort()
				s1, s2 = tmp
				G.add_edge(s1, s2,
					link_type = 'student_student_table_neighbour',
					weekday = wd,
					key = s1 + s2 + wd_string)


def set_teacher_teacher_social_contacts(G, school_type, N_classes,
			r_teacher_conversation, r_teacher_friend):
	"""
	Add edges to the graph corresponding to social contacts between teachers.
	Teachers can have passing contacts (link_type 'teacher_teacher_short') for
	short meetings (< 15 min) corresponding to short conversations with other
	teachers at school (coffee kitchen, short exchange of information). Teachers
	can have longer contacts (link_type 'teacher_teacher_long'), corresponding
	to longer in-person meetings or social relationships (friendshios) among
	teachers. Contacts are created between random pairs of teachers, ensuring
	that the average nmber of contacts of teachers corresponds to the prescribed
	ratios. Teacher social contacts are only set for weekdays 1-5 and not for
	weekend days (6 & 7).
	Note: modifies the graph inplace by adding additional edges.

	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges.
	school_type : str
		Type of the school. Needs to be supported by get_N_teachers().
	N_classes: int
		Number of classes in the school.
	r_teacher_conversation : float
		Ratio of other teachers a given teacher has conversations with during
		any given school day (i.e. not on weekends).
	r_teacher_friend : float
		Ratio of other teachers a given teachers has longer conversations or
		social meetings with during any given school day (i.e. not on weekends).
	"""

	N_teachers = get_N_teachers(school_type, N_classes)
	teacher_nodes = ['t{:04d}'.format(i) for i in range(1, N_teachers + 1)]

	N_teacher_contacts_far = round(N_teachers * r_teacher_conversation)
	N_teacher_contacts_intermediate = round(N_teachers * r_teacher_friend)

	_, N_weekdays, weekend_days = get_teaching_framework()

	# total number of unique far contacts that will be generated. The division
	# by two ensures the ratio of far contacts to other teachers corresponds to
	# the given ratio, since every edge connects two teachers and is therefore
	# counted as a contact for both teachers.
	N_teacher_contacts_far = (N_teacher_contacts_far * N_teachers) / 2
	contacts_created = 0
	while contacts_created < N_teacher_contacts_far:
		t1 = np.random.choice(teacher_nodes)
		t2 = np.random.choice(teacher_nodes)
		if t1 == t2:
			continue

		if not G.has_edge(t1, t2):
			tmp = [t1, t2]
			tmp.sort()
			t1, t2 = tmp
			for wd in range(1, N_weekdays + 1):
				if not wd in weekend_days:
					G.add_edge(t1, t2, link_type='teacher_teacher_short',
								   weekday = wd,
								   key = t1 + t2 + 'd{}'.format(wd))
			contacts_created += 1
	
	# total number of unique intermediate contacts that will be generated
	N_teacher_contacts_intermediate = \
			(N_teacher_contacts_intermediate * N_teachers) / 2
	contacts_created = 0
	while contacts_created < N_teacher_contacts_intermediate:
		t1 = np.random.choice(teacher_nodes)
		t2 = np.random.choice(teacher_nodes)
		if t1 == t2:
			continue

		if not G.has_edge(t1, t2):
			tmp = [t1, t2]
			tmp.sort()
			t1, t2 = tmp
			for wd in range(1, N_weekdays + 1):
				if not wd in weekend_days:
					G.add_edge(t1, t2, link_type = 'teacher_teacher_long',
									   weekday = wd,
									   key = t1 + t2 + 'd{}'.format(wd))
			contacts_created += 1


def _set_teaching_contacts(G, teacher_schedule, student_schedule, 
					       teaching_hours, N_classes):
	_, N_weekdays, _ = get_teaching_framework()
	for wd in range(1, N_weekdays + 1):
		wd_teacher_schedule = teacher_schedule.loc[wd]
		wd_student_schedule = student_schedule.loc[wd]

		# morning classes: create links between the teachers and all students
		# in the classes taught by the teachers
		for hour in range(1, teaching_hours + 1):
			for c in range(1, N_classes + 1):
				hour_col = 'hour_{}'.format(hour)
				# teachers teaching a given class in a given hour during a 
				# given day
				teachers = wd_teacher_schedule[hour_col][\
					wd_teacher_schedule[hour_col] == c].index

				# students in a given class during a given day
				students = wd_student_schedule[hour_col][\
					wd_student_schedule[hour_col] == c].index

				for t in teachers:
					for s in students:
						key = s + t + 'd{}'.format(wd)
						# no sorting needed, student nodes come first
						G.add_edge(s, t, link_type = 'teaching_teacher_student',
										 weekday = wd,
										 key = key)

def set_teacher_student_teaching_contacts(G, school_type, N_classes, 
										  teacher_schedule, student_schedule):
	"""
	Set contacts between teachers and students based on which teacher teaches
	which class during a given hour. Teaching relationships are specified in
	the teacher_schedule and student_schedule respectively. Teaching contacts
	are set for every teaching day of the week (days 1-5) and not for weekends
	(days 6 & 7). Note: modifies the graph inplace by adding additional edges.

	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges.
	school_type : str
		Type of the school. Needs to be supported by get_teaching_hours().
	N_classes : int
		Number of classes in the school.
	teacher_schedule : pandas DataFrame
		Table of the form (N_teachers * N_weekdays) X N_hours, where N_hours is
		the total number of hours typically spent at school at maximum (=9).
		The table has a hierarchical index of [weekday, teacher]. Entries are
		the class that is taught by a given teacher during a given day and hour.
	student_schedule : pandas DataFrame
		Table of the form (N_students * N_weekdays) X N_hours, where N_hours is
		the total number of hours typically spent at school at maximum (=9).
		The table has a hierarchical index of [weekday, student]. Entries are
		the classroom that a given student is in (=the number of class the 
		student is assigned to) during a given day and hour.
	"""
	if school_type == 'secondary_dc':
		low_sec_students = [n[0] for n in \
				G.nodes(data='age') if n[1] < 14 and n[0].startswith('s')]
		low_sec_student_schedule = student_schedule.\
				loc[(slice(None), low_sec_students),].copy()
		low_sec_teaching_hours = get_teaching_hours('lower_secondary')
		# add an hour for the lunch break
		if low_sec_teaching_hours >= 5:
			low_sec_teaching_hours += 1
		_set_teaching_contacts(G, teacher_schedule, low_sec_student_schedule,
							   low_sec_teaching_hours, N_classes)


		up_sec_students = [n[0] for n in \
				G.nodes(data='age') if n[1] >= 14 and n[0].startswith('s')]
		up_sec_student_schedule = student_schedule.\
				loc[(slice(None), up_sec_students),].copy()
		up_sec_teaching_hours = get_teaching_hours('upper_secondary')
		# add an hour for the lunch break
		if up_sec_teaching_hours >= 5:
			up_sec_teaching_hours += 1
		_set_teaching_contacts(G, teacher_schedule, up_sec_student_schedule,
							   up_sec_teaching_hours, N_classes)
	else:
		teaching_hours = get_teaching_hours(school_type)
		# add an hour for the lunch break
		if teaching_hours >= 5:
			teaching_hours += 1
		_set_teaching_contacts(G, teacher_schedule, student_schedule,
							   teaching_hours, N_classes)
	

def set_teacher_teacher_teamteaching_contacts(G, school_type, teacher_schedule):
	"""
	Set contacts between teachers due to team-teaching. For the "Mittelschule" 
	(lower secondary school), team teaching is by now the norm for most of the 
	schools in Austria and most of the lessons taught in these schools. 
	For upper secondary schools, we also assume a small extent of team teaching 
	due to the high number of teachers / class. Here, team-teaching is mostly
	used for language lessons, where a native speaking teacher supports the 
	language teacher. During team teaching, two teachers supervise the same 
	lesson. We model these teachers as having a "long" contact to each other, 
	if they teach together. Here, we add links between teachers that teach 
	together according to the teacher_schedule. Team teaching links are only set
	for teaching days (weekdays 1-5) and not for weekends.
	Note: this function modifies the graph inplace by adding additional edges.

	Parameters
	-----------
	G : networkx graph Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges.
	school_type : str
		Type of the school, needs to be supported by get_teaching_hours()
	teacher_schedule : pandas DataFrame
		Table of form (N_teachers * N_weekdays) X N_hours, where entries are the
		class a given teacher is teaching during a given hour at a given day.
	"""

	# only three school types suppor team teaching. We need to hard-code these
	# types here and return immediately if the school type passed to the function
	# does not feature team teaching, because otherwise jointly supervised classes
	# during daycare in these school types will be mistaken for team teaching and
	# contacts not set correctly
	if school_type not in ['lower_secondary', 'lower_secondary_dc',\
		 'upper_secondary']:
		 return

	max_hours, N_weekdays, weekend_days = get_teaching_framework()
	# number of hours that are usually taught every day in the given school type
	teaching_hours = get_teaching_hours(school_type)
	# maximum hours students & teachers spend at the school on a given day
	teaching_hour_cols = ['hour_{}'.format(i) for \
			i in range(1, teaching_hours + 1)]

	for wd in range(1, N_weekdays + 1):
		if wd not in weekend_days:
			wd_schedule = teacher_schedule.loc[wd]
			for hour_col in teaching_hour_cols:
				team_taught_classes = wd_schedule[hour_col].value_counts()[\
								wd_schedule[hour_col].value_counts() > 1].index

				for team_class in team_taught_classes:
					team_teachers = wd_schedule[\
						wd_schedule[hour_col] == team_class][hour_col].index

					# sanity check to ensure there are only two teachers in the
					# same class at the same time
					assert len(team_teachers == 2), 'team teaching messup!'

					# The alphabetic sorting of node IDs is necessary to
					# ensure the edge key is always composed of the 
					# node with the lower ID counter first. Otherwise we
					# would get duplicate edges with permuted node IDs 
					# and different keys.
					t1 = team_teachers[0]
					t2 = team_teachers[1]
					tmp = [t1, t2]
					tmp.sort()
					t1, t2 = tmp
					G.add_edge(t1, t2, 
							   link_type = 'teacher_teacher_team_teaching',
							   weekday = wd,
							   key = t1 + t2 + 'd{}'.format(wd))


def set_teacher_teacher_daycare_supervision_contacts(G, school_type, 
	teacher_schedule):
	"""
	Set contacts between teachers that supervise a group of students during 
	daycare together. In school types with daycare, afternoon supervision 
	groups are also supervised by two teachers. These teachers have an 
	additional long contact. Daycare supervision contacts are only set for 
	teaching days (weekdays 1-5) and not on weekends (days 6 & 7).
	Note: this function modifies the graph G inplace by adding additional edges.

	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges.
	teacher_schedule: pandas DataFrame
		Table of form (N_teachers * N_weekdays) X N_hours, where entries are the
		class that is taught by a given teacher during a given hours at a given 
		weekday.
	"""
	if not school_type.endswith('_dc'):
		return

	# number of hours that are usually taught every day in the given school type
	teaching_hours = get_teaching_hours(school_type)
	max_hours, N_weekdays, weekend_days = get_teaching_framework()
	# hours that students spend in daycare (max_hours - teaching_hours)
	supervision_hour_cols = ['hour_{}'.format(i) for \
			i in range(teaching_hours + 1, max_hours + 1)]

	# the fifth hour is the lunch break by definition and is therefore removed 
	# from the list of daycare supervision hours
	if 'hour_5' in supervision_hour_cols:
		supervision_hour_cols.remove('hour_5')

	for wd in range(1, N_weekdays + 1):
		if wd not in weekend_days: 
			wd_schedule = teacher_schedule.loc[wd]

			for hour_col in supervision_hour_cols:
				supervised_classes = wd_schedule[hour_col].value_counts()[\
								wd_schedule[hour_col].value_counts() > 1].index


				for c in supervised_classes:
					supervising_teachers = wd_schedule[\
						wd_schedule[hour_col] == c][hour_col].index

					# in theory a daycare group can be supervised by more than 
					# two teachers. Create contacts between all of the teachers
					# supervising the same group
					for t1 in supervising_teachers:
						for t2 in supervising_teachers:
							if t1 != t2:
								# The alphabetic sorting of node IDs is necessary to
								# ensure the edge key is always composed of the 
								# node with the lower ID counter first. Otherwise we
								# would get duplicate edges with permuted node IDs 
								# and different keys.
								teachers = [t1, t2]
								teachers.sort()
								n1, n2 = teachers
								G.add_edge(n1, n2,\
								link_type='teacher_teacher_daycare_supervision',
								weekday=wd,
								key=n1 + n2 + 'd{}'.format(wd))


def set_teacher_student_daycare_supervision_contacts(G, school_type, N_classes,
	teacher_schedule, student_schedule):
	"""
	Set the contacts between the students in afternoon daycare supervision 
	groups and the teachers supervising these groups. These links are only set
	for teaching days (weekdays 1-5) and not for weekends (days 6 & 7).
	Note: this function modifies the graph G inplace by adding additional edges.

	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges.

	school_type : (str) type of the school

	N_classes: (int) number of classes in the school

	teacher_schedule : (pandas DataFrame) table of form 
	(N_teachers * N_weekdays) X N_hours, where entries are the class that is 
	taught by a given teacher during a given hour at a given weekday.

	student_schedule : (pandas DataFrame) table of form 
	(N_students * N_weekdays) X N_hour, where entries are the class that a 
	student is in during a given hour at a given weekday
	"""

	# number of hours that are usually taught every day in the given school type
	teaching_hours = get_teaching_hours(school_type)
	# add one hour for the lunch break
	if teaching_hours >= 5:
		teaching_hours += 1
	# maximum hours students & teachers spend at the school on a given day
	max_hours, N_weekdays, weekend_days = get_teaching_framework()
	supervision_hour_cols = ['hour_{}'.format(i) for \
			i in range(teaching_hours + 1, max_hours + 1)]

	# for secondary schools, only the age brackets corresponding to lower
	# secondary levels are eligible for daycare supervision
	age_bracket_map = get_age_distribution(school_type, N_classes)
	daycare_eligibe = [c for c, age in age_bracket_map.items() \
                            if age < 14]

	# the fifth hour is the lunch break by definition and is therefore removed 
	# from the list of daycare supervision hours
	if 'hour_5' in supervision_hour_cols:
		supervision_hour_cols.remove('hour_5')

	for wd in range(1, N_weekdays + 1):
		if wd not in weekend_days:
			wd_teacher_schedule = teacher_schedule.loc[wd]
			wd_student_schedule = student_schedule.loc[wd]

			for hour_col in supervision_hour_cols:
				# all classes that are taught in the afternoon
				tmp = wd_teacher_schedule[hour_col].dropna().unique()
				# classes eligible for daycare
				daycare_groups = [g for g in tmp if g in daycare_eligibe]
				for daycare_group in daycare_groups:
					# teachers supervising a given daycare group in a given hour
					# at a given day
					teachers = wd_teacher_schedule[\
							wd_teacher_schedule[hour_col] == daycare_group].index
					
					# students in a given daycare group during a given day
					students = wd_student_schedule[hour_col][\
						wd_student_schedule[hour_col] == daycare_group].index

					for t in teachers:
						for s in students:
							G.add_edge(s, t, 
								link_type = 'daycare_supervision_teacher_student',
								weekday = wd,
								key = s + t + 'd{}'.format(wd))


def set_student_student_daycare_contacts(G, school_type, student_schedule):
	"""
	Generate contact patterns between students based on their assignment to
	afternoon daycare groups. Contacts are only created for teaching days
	(weekdays 1-5) and not for weekend days (days 6 & 7).
	Note: the graph G is modified inplace by adding additional edges.

	Parameters
	----------
	G : networkx Graph or MultiGraph 
		Graph holding the agents (students, teachers, household members) of the
		school as nodes and their contacts as edges.
	school_type : str
		Type of the school, needs to be supported by get_teaching_hours().
	student_schedule : pandas DataFrame
		Table of the form (N_students * N_weekdays) X N_hours, where entries are
		the class a given student is at during a given hour at a given weekday.
	"""

	# number of hours that are usually taught every day in the given school type
	teaching_hours = get_teaching_hours(school_type)
	# add an hour for the lunch break
	if teaching_hours >= 5:
		teaching_hours += 1
	max_hours, N_weekdays, weekend_days = get_teaching_framework()
	supervision_hour_cols = ['hour_{}'.format(i) for \
			i in range(teaching_hours + 1, max_hours + 1)]

	# the fifth hour is the lunch break by definition and is therefore removed 
	# from the list of daycare supervision hours
	if 'hour_5' in supervision_hour_cols:
		supervision_hour_cols.remove('hour_5')

	for wd in range(1, N_weekdays + 1):
		if wd not in weekend_days:
			for hour_col in supervision_hour_cols:
				wd_schedule = student_schedule.loc[wd]
				daycare_groups = wd_schedule[hour_col].dropna().unique()

				for daycare_group in daycare_groups:
					students = wd_schedule[hour_col][\
						wd_schedule[hour_col] == daycare_group].index

					for s1 in students:
						for s2 in students:
							if s1 != s2:
								# The alphabetic sorting of node IDs is 
								# necessary to ensure the edge key is always 
								# composed of the  node with the lower ID 
								# counter first. Otherwise we would get 
								# duplicate edges with permuted node IDs and 
								# different keys.
								tmp = [s1, s2]
								tmp.sort()
								n1, n2 = tmp
								G.add_edge(s1, s2, \
									link_type = 'student_student_daycare',
									weekday = wd,
									key = n1 + n2 + 'd{}'.format(wd))


###########################
###						###
###		schedules 		###
###						###
###########################


def generate_student_schedule(school_type, N_classes, class_size, \
		student_offset=0):
	"""
	Generate the schedule of classes every student attends at every hour of
	every teaching day (days 1-5). For school types with no daycare, students
	spend their entire school day in the same class (room). For school types
	with daycare, students spend their mornings in the same class (room). For
	the afternoon, students are assigned to new groups and new classrooms.

	Parameters
	----------
	school_type : str
		Type of the school. Needs to be supported by get_daycare_ratio() and
		get_teaching_hours().
	N_classes : int
		Number of classes in the school
	class_size : int
		Number of students per class.

	Returns
	-------
	student_schedule : pandas DataFrame
		table of the form (N_students * N_weekdays) X N_hours where N_hours = 9
		and entries correspond to the classes / classrooms a student is at 
		during a given day and hour.
	"""
	# in the case of secondary schools with daycare, we have to split the
	# student population into students in lower secondary grades (that
	# participate in daycare) and students in upper secondary grades, that
	# have normal lessons. Here, we split the student population and then 
	# generate separate schedules according to the lower_secondary schedule
	# and the secondary schedule, which are then combined.
	if school_type == 'secondary_dc':
		age_bracket_map = get_age_distribution('secondary', N_classes)
		lower_secondary_classes = [c for c, age in age_bracket_map.items() \
									if age < 14]
		offset = len(lower_secondary_classes) * class_size

		lower_secondary_schedule = generate_student_schedule(\
			'lower_secondary_dc', len(lower_secondary_classes), class_size)
		upper_secondary_schedule = generate_student_schedule(\
			'secondary', N_classes - len(lower_secondary_classes),
			class_size, student_offset=offset)
		student_schedule = pd.concat([lower_secondary_schedule,
									  upper_secondary_schedule])
		return student_schedule.sort_index()

	# ratio of students that attend afternoon daycare
	daycare_ratio = get_daycare_ratio(school_type)
	# number of hours that are usually taught every day in the given school type
	teaching_hours = get_teaching_hours(school_type)
	max_hours, N_weekdays, weekend_days = get_teaching_framework()

	# no lunch break included
	if teaching_hours < 5:
		N_teaching_hours = range(1, teaching_hours + 1) 
	# lunch break included
	else:
		N_teaching_hours = range(1, teaching_hours + 2) 
	N_daycare_hours = range(teaching_hours + 2, max_hours + 1)


	# determine if any students will be in daycare
	daycare = False
	if daycare_ratio > 0:
		daycare = True

	student_nodes = ['s{:04d}'.format(i) for \
			i in range(1 + student_offset,
					   N_classes * class_size + 1 + student_offset)]


	student_schedule = pd.DataFrame(columns=['student'] + \
					['hour_{}'.format(i) for i in range(1, max_hours + 1)])
	student_schedule['student'] = student_nodes * N_weekdays

	# create a hierarchical index of form [weekday, student]
	iterables = [range(1, 8), student_nodes]
	index = pd.MultiIndex.from_product(iterables, names=['weekday', 'student'])
	student_schedule.index = index
	student_schedule = student_schedule.drop(columns=['student'])

	if daycare_ratio > 0:
		# pick a number of students at random to participate in full daycare
		daycare_students = np.random.choice(student_nodes, \
				   int((N_classes * class_size) * daycare_ratio), replace=False)
		non_daycare_students = [s for s in student_nodes if \
								 s not in daycare_students]
	else:
		daycare_students = []
		non_daycare_students = student_nodes

	for wd in range(1, N_weekdays + 1):
		# weekend: all students are at home
		if wd in weekend_days:
			for s in student_nodes:
				for hour in range(1, max_hours + 1):
					student_schedule.loc[wd, s]['hour_{}'.format(hour)] = pd.NA
						
		# weekdays: students are distributed across classes
		else:
			for s in student_nodes:
				# necessary to ensure classromms are assigned correctly, even
				# if there is a student offset (in the case of secondary_dc)
				i = int(s[1:])

				# teaching hours
				for hour in N_teaching_hours:
					if hour == 5: # lunchbreak
						classroom = pd.NA
						student_schedule.loc[wd, s]['hour_{}'.format(hour)] = classroom
					else:
						# students are distributed to classes evenly, starting by s1
						# in class 1 to student s N_classes * class_size in class N
						classroom = int((i - 1)/ class_size) + 1
						student_schedule.loc[wd,s]['hour_{}'.format(hour)]=classroom

			for i, s in enumerate(daycare_students):
				# daycare hours
				for hour in N_daycare_hours:
					# students in daycare are distributed evenly to the newly 
					# formed daycare group. Since these students (and their 
					# order) are randomly picked, the daycare groups also create
					# new contacts between  students, which are later set by the
					# function generate_student_daycare_contacts
					classroom = int((i - 1) / class_size) + 1
					student_schedule.loc[wd,s]['hour_{}'.format(hour)]=classroom

			for s in non_daycare_students:
				i = int(s[1:])
				# daycare hours
				for hour in N_daycare_hours:
					classroom = pd.NA
					student_schedule.loc[wd,s]['hour_{}'.format(hour)]=classroom

	student_schedule = student_schedule.replace({np.nan:pd.NA})
	return student_schedule


def generate_teacher_schedule_primary(N_classes):
	"""
	Generate the schedule of classes every teacher teaches at every hour of
	every teaching day (days 1-5). Teachers in primary schools without daycare
	are either "class teachers" that teach mainly one class, or teachers of
	minor subjects, that teach more classes on a given day. The number of
	classes passed to this function must be even, since this simplifies schedule
	creation tremendously.

	Parameters
	----------
	N_classes : int
		Number of classes in the school

	Returns
	-------
	teacher_schedule : pandas DataFrame
		Table of the form (N_teachers * N_weekdays) X N_hours, where N_hours=9
		and entries correspond to classes a teacher teaches during a given day
		and hour. 
	"""

	assert N_classes % 2 == 0, 'number of classes must be even'

	N_teachers = get_N_teachers('primary', N_classes)
	teacher_nodes = ['t{:04d}'.format(i) for i in range(1, N_teachers + 1)]

	N_teaching_hours = get_teaching_hours('primary')
	max_hours, N_weekdays, weekend_days = get_teaching_framework()

	schedule = {t:[] for t in teacher_nodes}

	# the first N_teaching_hours / 2 hours are taught by teachers 1 to 
	# N_classes:
	for i in range(1, N_classes + 1):
		schedule['t{:04d}'.format(i)].extend([i] * int(N_teaching_hours / 2))

	# the rest of the teachers take a break in the faculty room
	for i in range(N_classes + 1, N_teachers + 1):
		schedule['t{:04d}'.format(i)].extend([pd.NA] * int(N_teaching_hours/2))

	# the next two hours are shared between the teachers of the 
	# primary subjects and additional teachers for the secondary subject, 
	# such that every teacher sees a total of two different classes every day
	for i, j in enumerate(range(N_classes + 1, N_teachers + 1)):
		schedule['t{:04d}'.format(j)].append(i + 1)
		schedule['t{:04d}'.format(j)].append(i + int(N_classes / 2) + 1)
	for i,j in enumerate(range(1, int(N_classes / 2) + 1)):
		schedule['t{:04d}'.format(j)].append(i + int(N_classes / 2) + 1)
		schedule['t{:04d}'.format(j)].append(pd.NA)
	for i,j in enumerate(range(int(N_classes / 2) + 1, N_classes + 1)):
		schedule['t{:04d}'.format(j)].append(pd.NA)
		schedule['t{:04d}'.format(j)].append(i + 1)

	# students and teachers spend the rest of the day (until hour 9) at home
	for i in range(0, max_hours - N_teaching_hours):
		for t in teacher_nodes:
			schedule[t].append(pd.NA)

	# convert the schedule to a data frame
	schedule_df = pd.DataFrame(columns=['teacher'] + ['hour_{}'.format(i)\
				 for i in range(1, max_hours + 1)])
	schedule_df['teacher'] = teacher_nodes * N_weekdays
	iterables = [range(1, N_weekdays + 1), teacher_nodes]
	index = pd.MultiIndex.from_product(iterables, names=['weekday', 'teacher'])
	schedule_df.index = index
	schedule_df = schedule_df.drop(columns = ['teacher'])

	for wd in range(1, N_weekdays + 1):
		for t in teacher_nodes:
			for hour, c in enumerate(schedule[t]):
				if wd not in weekend_days:
					schedule_df.loc[wd, t]['hour_{}'.format(hour + 1)] = c

	return schedule_df


def generate_teacher_schedule_primary_daycare(N_classes):
	"""
	Generate the schedule of classes every teacher teaches at every hour of
	every teaching day (days 1-5). Teachers in primary schools with daycare
	are either "class teachers" that teach mainly one class, or teachers of
	minor subjects, that teach more classes on a given day and supervise
	students during daycare in the afternoons. The number of classes passed to 
	this function must be even, since this simplifies schedule creation 
	tremendously.

	Parameters
	----------
	N_classes : int
		Number of classes in the school

	Returns
	-------
	teacher_schedule : pandas DataFrame
		Table of the form (N_teachers * N_weekdays) X N_hours, where N_hours=9
		and entries correspond to classes a teacher teaches during a given day
		and hour. 
	"""

	assert N_classes % 2 == 0, 'number of classes must be even'

	## teacher schedule
	N_teachers = get_N_teachers('primary_dc', N_classes)
	teacher_nodes = ['t{:04d}'.format(i) for i in range(1, N_teachers + 1)]

	N_teaching_hours = get_teaching_hours('primary_dc')
	max_hours, N_weekdays, weekend_days = get_teaching_framework()

	schedule = {t:[] for t in teacher_nodes}

	# the first two hours are taught by teachers 1 to N_classes:
	for i in range(1, N_classes + 1):
		schedule['t{:04d}'.format(i)].extend([i] * 2)
	for i in range(N_classes + 1, N_classes * 2 + 1):
		schedule['t{:04d}'.format(i)].extend([pd.NA] * 2)

	# the third hour is also taught by teachers 1 to N_classes, but classes
	# are shifted:
	for i in range(1, N_classes + 1):
		schedule['t{:04d}'.format(i)].append(i % N_classes + 1)
	for i in range(N_classes + 1, N_classes * 2 + 1):
		schedule['t{:04d}'.format(i)].append(pd.NA)
		
	# the fourth hour is taught by teachers N_classes + 1 to N_classes * 2
	for i, j in enumerate(range(N_classes + 1, N_classes * 2 + 1)):
		schedule['t{:04d}'.format(j)].append(i + 1)
	for i in range(1, N_classes + 1):
		schedule['t{:04d}'.format(i)].append(pd.NA)

	# the fifth hour is lunchbreak for all teachers
	for t in teacher_nodes:
		schedule[t].append(pd.NA)
		
	# the afternoon supervision is done by teachers N_classes + 1 to 
	# N_classes * 2 and every two teachers supervise a group
	for i, j in enumerate(range(N_classes + 1, N_classes * 2 + 1)):
		schedule['t{:04d}'.format(j)].extend(\
				[int(i / 2 + 1)] * (max_hours - N_teaching_hours))
	# the rest of the teachers go home
	for i in range(1, N_classes + 1):
		schedule['t{:04d}'.format(i)].extend(\
				[pd.NA] * (max_hours - N_teaching_hours))
		
	schedule_df = pd.DataFrame(columns=['teacher'] + \
					['hour_{}'.format(i) for i in range(1, max_hours + 1)])
	schedule_df['teacher'] = teacher_nodes * N_weekdays
	iterables = [range(1, N_weekdays + 1), teacher_nodes]
	index = pd.MultiIndex.from_product(iterables, names=['weekday', 'teacher'])
	schedule_df.index = index
	schedule_df = schedule_df.drop(columns = ['teacher'])

	for wd in range(1, N_weekdays + 1):
		for t in teacher_nodes:
			for hour, c in enumerate(schedule[t]):
				if wd not in weekend_days:
					schedule_df.loc[wd, t]['hour_{}'.format(hour + 1)] = c

	return schedule_df


def generate_teacher_schedule_lower_secondary(N_classes):
	"""
	Generate the schedule of classes every teacher teaches at every hour of
	every teaching day (days 1-5). Teachers in lower secondary schools without
	daycare teach see four different classes each day. In lower secondary 
	schools (Mittelschule), team teaching is very common. Therefore for the 
	majority of lessons there are two teachers present in the classroom, which 
	is reflected in the teacher_schedule, where two teachers will be teaching 
	the same class at the same hour and weekday. The number of classes passed to
	this function must be even, since this simplifies schedule creation 
	tremendously.

	Parameters
	----------
	N_classes : int
		Number of classes in the school

	Returns
	-------
	teacher_schedule : pandas DataFrame
		Table of the form (N_teachers * N_weekdays) X N_hours, where N_hours=9
		and entries correspond to classes a teacher teaches during a given day
		and hour. 
	"""
	assert N_classes % 2 == 0, 'number of classes must be even'

	N_teachers = get_N_teachers('lower_secondary', N_classes)
	N_hours = get_teaching_hours('lower_secondary')
	teacher_nodes = ['t{:04d}'.format(i) for i in range(1, N_teachers + 1)]
	max_hours, N_weekdays, weekend_days = get_teaching_framework()

	# we create the schedule for first teachers and second teachers by first 
	# creating a list of teacher node IDs and then reshaping it such that it 
	# fits the N_hours X N_classes format. The list schedule of first teachers
	# is created in such a way that it ensures every class is taught by at least
	# one teachers during every hour in N_hours. The schedule for second
	# teachers adds a second teacher to the majority (4 out of 6) of lessons.
	teacher_list =list(range(1, N_teachers + 1)) * 2
	teacher_list.extend(list(range(2, N_teachers + 1)))
	teacher_list.extend(list(range(1, N_teachers + 1)) + [1])
	teacher_list = np.asarray(teacher_list)
	first_teachers = teacher_list[0:N_hours * N_classes]\
				.reshape((N_hours, N_classes))
	second_teachers = teacher_list[N_hours * N_classes:]\
				.reshape((int(N_hours * (2/3)), N_classes))

	# distill the first teacher schedule into a DataFrame with a hierarchical
	# index of form [weekday, teacher]
	first_teacher_schedule = pd.DataFrame(columns=['hour'] + ['class_{}'\
			.format(i) for i in range(1, N_classes + 1)])
	first_teacher_schedule['hour'] = [i for i in range(1, N_hours + 1)]
	for i in range(0, N_classes):
		first_teacher_schedule['class_{}'.format(i + 1)] = first_teachers[0:,i]
	first_teacher_schedule.index = first_teacher_schedule['hour']
	first_teacher_schedule = first_teacher_schedule.drop(columns = ['hour'])
		
	# distill the second teacher schedule into a DataFrame with a hierarchical
	# index of form [weekday, teacher]
	second_teacher_schedule = pd.DataFrame(columns=['hour'] + ['class_{}'.format(i) for i in range(1, N_classes + 1)])
	second_teacher_schedule['hour'] = [i for i in range(1, int(N_hours * (2/3)) + 1)]
	for i in range(0, N_classes):
		second_teacher_schedule['class_{}'.format(i + 1)] = second_teachers[0:, i]
	second_teacher_schedule.index = second_teacher_schedule['hour']
	second_teacher_schedule = second_teacher_schedule.drop(columns = ['hour'])

	# create the overall teacher schedule of form (N_weekdays * N_teachers) X
	# N_hours by drawing information from the first_teacher_schedule and the
	# second_teacher_schedule
	schedule_df = pd.DataFrame(columns=['teacher'] + ['hour_{}'.format(i) for\
			 i in range(1, max_hours + 1)])
	schedule_df['teacher'] = teacher_nodes * N_weekdays
	iterables = [range(1, N_weekdays + 1), teacher_nodes]
	index = pd.MultiIndex.from_product(iterables, names=['weekday', 'teacher'])
	schedule_df.index = index
	schedule_df = schedule_df.drop(columns = ['teacher'])

	for c in range(1, N_classes + 1):
		for hour in range(1, N_hours + 1):
			for wd in range(1, N_weekdays + 1):
				if wd not in weekend_days:
					t1 = first_teacher_schedule.loc[hour, 'class_{}'.format(c)]
					schedule_df.loc[wd, 't{:04d}'.format(t1)]\
								['hour_{}'.format(hour)] = c
					# try to find a second teacher for the same lesson. 
					try:
						t2 = second_teacher_schedule.loc[hour, 'class_{}'.format(c)]
						schedule_df.loc[wd, 't{:04d}'.format(t2)]\
								['hour_{}'.format(hour)] = c
					except KeyError:
						pass

	# for the hours past the teaching hours (N_hours): set schedule entries for
	# all teachers to NaN
	for t in teacher_nodes:
		for hour in range(N_hours + 1, max_hours + 1):
			for wd in range(1, N_weekdays + 1):
				schedule_df.loc[wd, t]['hour_{}'.format(hour)] = pd.NA

	schedule_df = schedule_df.replace({np.nan:pd.NA})
	# shift afternoon teaching hours by one to make space for the lunch break
	# in the fifth hour:
	schedule_df = schedule_df.rename(columns={
				'hour_9':'hour_5', 'hour_5':'hour_6', 'hour_6':'hour_7',
				'hour_7':'hour_8', 'hour_8':'hour_9'})
	schedule_df = schedule_df[['hour_{}'\
				.format(i) for i in range(1, max_hours + 1)]]

	return schedule_df


def generate_teacher_schedule_lower_secondary_daycare(N_classes):
	"""
	Generate the schedule of classes every teacher teaches at every hour of
	every teaching day (days 1-5). The majority of teachers in lower secondary 
	schools with daycare teach three differnt classes each day, with some 
	teaching four and some teaching two, depending on daycare supervision load.
	In lower secondary schools (Mittelschule), team teaching is very common.
	Therefore for the majority of lessons there are two teachers present in
	the classroom, which is reflected in the teacher_schedule, where two
	teachers will be teaching the same class at the same hour and weekday.
	The number of classes passed to this function must be even, since this 
	simplifies schedule creation tremendously.

	Parameters
	----------
	N_classes : int
		Number of classes in the school

	Returns
	-------
	teacher_schedule : pandas DataFrame
		Table of the form (N_teachers * N_weekdays) X N_hours, where N_hours=9
		and entries correspond to classes a teacher teaches during a given day
		and hour. 
	"""
	assert N_classes % 2 == 0, 'number of classes must be even'

	N_teachers = get_N_teachers('lower_secondary_dc', N_classes)
	N_hours = get_teaching_hours('lower_secondary_dc')
	max_hours, N_weekdays, weekend_days = get_teaching_framework()
	daycare_hours = range(N_hours + 1, max_hours)
	if 5 in daycare_hours:
		daycare_hours.remove(5)
	teacher_nodes = ['t{:04d}'.format(i) for i in range(1, N_teachers + 1)]
	

	# for lower secondary schools with daycare, there are 3 teachers per class
	# 5 out of 6 hours / day are taught in team-teaching and daycare supervision
	# of each group is also done by two teachers. To create the schedule for the
	# teachers, we have to make sure that no teacher teaches two classes at the 
	# same time and that teachers see a different class every hour (to account 
	# for the number of classes a teacher sees on average, according to the 
	# interviews we conducted). The following solution is a bit hacky but gets 
	# the job done:

	# first, we construct a sequential list of length N_classes * 6, to ensure 
	# that in every hour there is at least one teacher in every class 

	# during the first three hours, all teachers teach once
	first_teacher_list = list(range(1, N_teachers + 1)) 
	# by shifting the list by 1 for the hours 4-6, we ensure that no teacher 
	# teaches the same class twice
	first_teacher_list.extend(list(range(2, N_teachers + 1)) + [1]) 
	# the list is then reshaped into an N_hours X N_classes array - the schedule
	first_teacher_list = np.asarray(first_teacher_list)
	first_teachers = first_teacher_list.reshape((N_hours, N_classes))
	# we convert the array to a data frame for easier indexing when we create 
	# the overall teacher schedule below
	first_teacher_schedule = pd.DataFrame(columns=['hour'] + \
				['class_{}'.format(i) for i in range(1, N_classes + 1)])
	first_teacher_schedule['hour'] = [i for i in range(1, N_hours + 1)]

	for i in range(0, N_classes):
		first_teacher_schedule['class_{}'.format(i + 1)] = first_teachers[0:,i]
	first_teacher_schedule.index = first_teacher_schedule['hour']
	first_teacher_schedule = first_teacher_schedule.drop(columns = ['hour'])
		
	# then we construct a sequential list of length N_classes * 5, intended to 
	# add a second teacher to 5 out of 6 lessons per day. The list is shifted in
	# such a way that no teacher teaches the same class twice or is supposed to
	# teach two classes during the same time
	second_teacher_list = list(range(9, N_teachers + 1)) + list(range(1, 9))
	second_teacher_list.extend(list(range(4, 4 + N_classes * 2)))
	# the list is reshaped into a 5 hours X N_classes array, which is then 
	# superimposed  with the schedule of first teachers, to create the team-
	# teaching schedule
	second_teacher_list = np.asarray(second_teacher_list)
	second_teachers = second_teacher_list.reshape((5, N_classes))
	second_teacher_schedule = pd.DataFrame(columns=['hour'] + \
				['class_{}'.format(i) for i in range(1, N_classes + 1)])
	second_teacher_schedule['hour'] = [i for i in range(1, 5 + 1)]
	for i in range(0, N_classes):
		second_teacher_schedule['class_{}'.format(i+1)] = second_teachers[0:, i]
	second_teacher_schedule.index = second_teacher_schedule['hour']
	second_teacher_schedule = second_teacher_schedule.drop(columns = ['hour'])

	# the overall schedule is a table of (N_weekdays * N_teachers) X N_hours,
	# in which the entries are the class that is taught by a given teacher in a
	# given time. We construct this table from the first teacher schedule and 
	# the second teacher schedule
	schedule_df = pd.DataFrame(columns=['teacher'] + ['hour_{}'.format(i) for\
			 i in range(1, max_hours + 1)])
	schedule_df['teacher'] = teacher_nodes * N_weekdays
	iterables = [range(1, N_weekdays + 1), teacher_nodes]
	index = pd.MultiIndex.from_product(iterables, names=['weekday', 'teacher'])
	schedule_df.index = index
	schedule_df = schedule_df.drop(columns = ['teacher'])

	for c in range(1, N_classes + 1):
		for hour in range(1, N_hours + 1):
			for wd in range(1, N_weekdays):
				if not wd in weekend_days:
					t1 = first_teacher_schedule.loc[hour, 'class_{}'.format(c)]
					schedule_df.loc[wd, 't{:04d}'.format(t1)]\
						['hour_{}'.format(hour)] = c
					# not all hours have a second teacher
					try:
						t2 = second_teacher_schedule.loc[\
										hour, 'class_{}'.format(c)]
						schedule_df.loc[wd, 't{:04d}'.format(t2)]\
							['hour_{}'.format(hour)] = c
					except KeyError:
						pass

	# daycare is handled separately: in the afternoon, half of the students go 
	# home and the other half are randomly distributed to a number of groups 
	# equal to N_classes / 2. These groups are supervised by two teachers each. 
	# The supervising teachers are the first N_classes teachers and the last 
	# N_classes teachers, since these teachers have a smaller number of team-
	# teaching lessons than the other teachers
	daycare_teacher_list = list(range(1, int(N_classes / 2) + 1))
	daycare_teacher_list.extend(list(range(N_teachers - int(N_classes / 2) + 1,\
										   N_teachers + 1)))
	daycare_teacher_list = np.asarray(daycare_teacher_list)\
							 .reshape((2, int(N_classes / 2)))
	# add the daycare supervision to the overall teacher schedule
	for dc_group in range(0, int(N_classes / 2)):
		for t in daycare_teacher_list[0:, dc_group]:
			for wd in range(1, N_weekdays + 1):
				if wd not in weekend_days:
					for hour in daycare_hours:
						schedule_df.loc[wd, 't{:04d}'.format(t)]\
							['hour_{}'.format(hour)] = dc_group + 1


	schedule_df = schedule_df.replace({np.nan:pd.NA})
	# shift afternoon teaching hours by one to make space for the lunch break
	# in the fifth hour:
	schedule_df = schedule_df.rename(columns={
				'hour_9':'hour_5', 'hour_5':'hour_6','hour_6':'hour_7',
				'hour_7':'hour_8', 'hour_8':'hour_9'})
	schedule_df = schedule_df[['hour_{}'.format(i) \
				for i in range(1, max_hours + 1)]]

	return schedule_df
		

def generate_teacher_schedule_upper_secondary(N_classes):
	"""
	Generate the schedule of classes every teacher teaches at every hour of
	every teaching day (days 1-5). Teachers in upper secondary schools teach
	either only "major" subjects or only "minor" subjects or a mix of both. 
	Teachers with mainly major subjects see less classes / day, teachers with 
	mainly minor subects see more different classes per day. Therefore, the 
	number of different classes each teacher sees per day ranges between two and
	five.
	Team teaching is not that very common and mainly occurs during language 
	classes, where the main teacher is supported by a native speaking teacher. 
	Therefore we model approximately 10% of lessons as team-teaching lessons. 
	In the schedule this is reflected by two teachers teaching the same class at
	the same hour and weekday. The number of classes passed to this function 
	must be even, since this simplifies schedule creation tremendously.

	Parameters
	----------
	N_classes : int
		Number of classes in the school

	Returns
	-------
	teacher_schedule : pandas DataFrame
		Table of the form (N_teachers * N_weekdays) X N_hours, where N_hours=9
		and entries correspond to classes a teacher teaches during a given day
		and hour. 
	"""
	assert N_classes % 2 == 0, 'number of classes must be even'

	N_hours = get_teaching_hours('upper_secondary')
	all_teachers = get_N_teachers('upper_secondary', N_classes)
	N_teachers = int(N_classes * 2.5)
	N_additional_teachers = all_teachers - N_teachers # for team teaching
	max_hours, N_weekdays, weekend_days = get_teaching_framework()
	teacher_nodes = ['t{:04d}'.format(i) for i in range(1, all_teachers + 1)]

	# we create the schedule for teachers by first creating a list of teacher 
	# node IDs and then reshaping it such that it fits the N_hours X N_classes 
	# format. The schedule is created in such a way that it ensures every class 
	# is taught by at least one teachers during every hour in N_hours.
	teacher_list = list(range(1, int(N_teachers * 2/3) + 1))
	teacher_list.extend(list(range(1, int(N_teachers * 2/3) + 1)))
	teacher_list.extend(list(range(1, N_teachers + 1)))
	teacher_list.extend(list(range(1, int(N_teachers * 1/3) + 1)))
	teacher_list.extend(list(range(int(N_teachers * 2/3), N_teachers + 1)))
	tmp_list = list(range(1, int(N_teachers * (1/3))))
	tmp_list.reverse()
	teacher_list.extend(tmp_list)
	teacher_list = np.asarray(teacher_list)
	teacher_array = teacher_list[0: N_hours * N_classes]\
		.reshape((N_hours, N_classes))

	# distill the first teacher schedule into a DataFrame with a hierarchical
	# index of form [weekday, teacher]
	first_teacher_schedule = pd.DataFrame(columns=['hour'] + \
				['class_{}'.format(i) for i in range(1, N_classes + 1)])
	first_teacher_schedule['hour'] = [i for i in range(1, N_hours + 1)]
	for i in range(0, N_classes):
		first_teacher_schedule['class_{}'.format(i + 1)] = teacher_array[0:,i]
	first_teacher_schedule.index = first_teacher_schedule['hour']
	first_teacher_schedule = first_teacher_schedule.drop(columns = ['hour'])

	# create the overall teacher schedule of form (N_weekdays * N_teachers) X
	# N_hours by drawing information from the first_teacher_schedule and then 
	# adding additional teacher to about 10% of lessons at random
	schedule_df = pd.DataFrame(columns=['teacher'] + ['hour_{}'.format(i) for\
			 i in range(1, max_hours + 1)])
	schedule_df['teacher'] = teacher_nodes * N_weekdays
	iterables = [range(1, N_weekdays + 1), teacher_nodes]
	index = pd.MultiIndex.from_product(iterables, names=['weekday', 'teacher'])
	schedule_df.index = index
	schedule_df = schedule_df.drop(columns = ['teacher'])

	for c in range(1, N_classes + 1):
		for hour in range(1, N_hours + 1):
			for wd in range(1, N_weekdays + 1):
				if wd not in weekend_days:
					t1 = first_teacher_schedule.loc[hour, 'class_{}'.format(c)]
					schedule_df.loc[wd, 't{:04d}'.format(t1)]\
							['hour_{}'.format(hour)] = c

	## team-teaching
	# Note: this has a small chance that the same teacher team-teaches twice in 
	# the same hour, effectiely slightly reducing the number of team-taught 
	# lessons
	all_hours = [(hour, c) for hour in range(1, N_hours + 1) \
			for c in range(1, N_classes + 1)]
	N_team_hours = 3
	team_idx = np.random.choice(range(len(all_hours)), \
				N_additional_teachers * N_team_hours, replace=False)
	for t in range(1, N_additional_teachers + 1):
		for idx in team_idx[(t - 1) * N_team_hours: t * N_team_hours]:
			hour, c = all_hours[idx]
			for wd in range(1, N_weekdays + 1):
				if wd not in weekend_days:
					schedule_df.loc[wd, 't{:04d}'.format(N_teachers + t)]\
						['hour_{}'.format(hour)] = c

	schedule_df = schedule_df.replace({np.nan:pd.NA})
	# shift afternoon teaching hours by one to make space for the lunch break
	# in the fifth hour:
	schedule_df = schedule_df.rename(columns={
					'hour_9':'hour_5', 'hour_5':'hour_6', 'hour_6':'hour_7',
					'hour_7':'hour_8', 'hour_8':'hour_9'})
	schedule_df = schedule_df[['hour_{}'.format(i) \
					for i in range(1, max_hours + 1)]]

	return schedule_df


def generate_teacher_schedule_secondary(N_classes):
	"""
	Generate the schedule of classes every teacher teaches at every hour of
	every teaching day (days 1-5). Teachers in secondary schools teach
	either only "major" subjects or only "minor" subjects or a mix of both. 
	Teachers with mainly major subjects see less classes / day, teachers with 
	mainly minor subects see more different classes per day. Therefore, the 
	number of different classes each teacher sees per day ranges between two and
	five. There is no team-teaching. The number of classes passed to this 
	function must be even, since this simplifies schedule creation tremendously.

	Parameters
	----------
	N_classes : int
		Number of classes in the school

	Returns
	-------
	teacher_schedule : pandas DataFrame
		Table of the form (N_teachers * N_weekdays) X N_hours, where N_hours=9
		and entries correspond to classes a teacher teaches during a given day
		and hour. 
	"""
	assert N_classes % 2 == 0, 'number of classes must be even'

	N_hours = get_teaching_hours('secondary')
	N_teachers = get_N_teachers('secondary', N_classes)
	teacher_nodes = ['t{:04d}'.format(i) for i in range(1, N_teachers + 1)]
	max_hours, N_weekdays, weekend_days = get_teaching_framework()

	# we create the schedule for teachers by first creating a list of teacher 
	# node IDs and then reshaping it such that it fits the N_hours X N_classes 
	# format. The schedule is created in such a way that it ensures every class 
	# is taught by at least one teachers during every hour in N_hours. 
	teacher_list = list(range(1, int(N_teachers * 2/3) + 1))
	teacher_list.extend(list(range(1, int(N_teachers * 2/3) + 1)))
	teacher_list.extend(list(range(1, N_teachers + 1)))
	teacher_list.extend(list(range(1, int(N_teachers * 1/3) + 1)))
	teacher_list.extend(list(range(int(N_teachers * 2/3), N_teachers + 1)))
	tmp_list = list(range(1, int(N_teachers * (1/3))))
	tmp_list.reverse()
	teacher_list.extend(tmp_list)
	teacher_list = np.asarray(teacher_list)
	teacher_array = teacher_list[0: N_hours * N_classes].reshape((N_hours, N_classes))

	# distill the first teacher schedule into a DataFrame with a hierarchical
	# index of form [weekday, teacher]
	first_teacher_schedule = pd.DataFrame(columns=['hour'] + ['class_{}'.format(i) for i in range(1, N_classes + 1)])
	first_teacher_schedule['hour'] = [i for i in range(1, N_hours + 1)]
	for i in range(0, N_classes):
		first_teacher_schedule['class_{}'.format(i + 1)] = teacher_array[0:,i]
	first_teacher_schedule.index = first_teacher_schedule['hour']
	first_teacher_schedule = first_teacher_schedule.drop(columns = ['hour'])

	# create the overall teacher schedule of form (N_weekdays * N_teachers) X
	# N_hours by drawing information from the first_teacher_schedule 
	schedule_df = pd.DataFrame(columns=['teacher'] + ['hour_{}'.format(i) for\
			 i in range(1, max_hours + 1)])
	schedule_df['teacher'] = teacher_nodes * N_weekdays
	iterables = [range(1, N_weekdays + 1), teacher_nodes]
	index = pd.MultiIndex.from_product(iterables, names=['weekday', 'teacher'])
	schedule_df.index = index
	schedule_df = schedule_df.drop(columns = ['teacher'])

	for c in range(1, N_classes + 1):
		for hour in range(1, N_hours + 1):
			t1 = first_teacher_schedule.loc[hour, 'class_{}'.format(c)]
			for wd in range(1, N_weekdays + 1):
				if wd not in weekend_days:
					schedule_df.loc[wd, 't{:04d}'.format(t1)]\
						['hour_{}'.format(hour)] = c

	schedule_df = schedule_df.replace({np.nan:pd.NA})
	# shift afternoon teaching hours by one to make space for the lunch break
	# in the fifth hour:
	schedule_df = schedule_df.rename(columns={
				'hour_9':'hour_5', 'hour_5':'hour_6', 'hour_6':'hour_7',
				'hour_7':'hour_8', 'hour_8':'hour_9'})
	schedule_df = schedule_df[['hour_{}'.format(i) \
				for i in range(1, max_hours + 1)]]

	return schedule_df


def generate_teacher_schedule_secondary_daycare(N_classes):
	"""
	Generate the schedule of classes every teacher teaches at every hour of
	every teaching day (days 1-5). Teachers in secondary schools with dayare
	teach either only "major" subjects or only "minor" subjects or a mix of both. 
	Teachers with mainly major subjects see less classes / day, teachers with 
	mainly minor subects see more different classes per day. In addition, 
	teachers supervise groups of students in the age bracket 11-14 attending
	daycare in the afternoons. Therefore, the number of different classes each 
	teacher sees per day ranges between two and five. There is no team-teaching.
	The number of classes passed to this function must be even, since this 
	simplifies schedule creation tremendously.

	Parameters
	----------
	N_classes : int
		Number of classes in the school

	Returns
	-------
	teacher_schedule : pandas DataFrame
		Table of the form (N_teachers * N_weekdays) X N_hours, where N_hours=9
		and entries correspond to classes a teacher teaches during a given day
		and hour. 
	"""
	assert N_classes % 2 == 0, 'number of classes must be even'

	daycare_hours = [8, 9]
	dc_cols = ['hour_{}'.format(h) for h in daycare_hours]
	age_bracket = get_age_bracket('secondary')
	age_bracket_map = get_age_distribution('secondary', N_classes)

	# first create the part of the schedule that is similar to secondary schools
	# without daycare
	teacher_schedule = generate_teacher_schedule_secondary(N_classes)
	
	# only students in the age bracket 11-14 participate in daycare
	lower_secondary_classes = [c for c, age in age_bracket_map.items() \
								if age < 14]
	# the number of daycare groups is equal to half the number of classes that
	# have students in the daycare-eligible age bracket
	N_daycare_groups = int(len(lower_secondary_classes) / 2)
	empty_dc_classes = lower_secondary_classes[N_daycare_groups:]
	full_dc_classes = lower_secondary_classes[0:N_daycare_groups]
	# mapping between the teachers in the empty classes to the full classes
	dc_class_mapping = {empty:full for empty, full in \
				zip(empty_dc_classes, full_dc_classes)}
	teacher_schedule[dc_cols] = teacher_schedule[dc_cols]\
				.replace({pd.NA:np.nan})
	# send all teachers in classes that are empty during the afternoons to full
	# classes, supervising students in daycare
	teacher_schedule[dc_cols] = teacher_schedule[dc_cols]\
				.replace(dc_class_mapping)
	teacher_schedule = teacher_schedule.replace({np.nan:pd.NA})

	return teacher_schedule
  

def compose_school_graph(school_type, N_classes, class_size, N_floors, 
		student_p_children, student_p_parents, teacher_p_adults,
		teacher_p_children, r_teacher_conversation, r_teacher_friend):
	"""
	Compose a graph containing all agents important for the dynamics of
	infection spread in schools, namely students, teachers and members of 
	student and teacher households, as well as their connections. Agent types 
	are stored in the graph as node attributes, alongside their age, location
	('unit', class(room) for students, faculty room for teachers, home for
	family members) and the 'family' they belong to.
	Connections are made between teachers and students during teaching and 
	afternoon daycare supervision. Connections are made between students and 
	other students that are in the same class (or even table neighbours) or in 
	the same afternoon daycare supervision groups. Connections are made between 
	teachers and other teachers if they teach together (team-teaching), 
	supervise afternoon daycare groups togeter or have (short) conversations or 
	(long) meetings or social connections (friendship). Connections between all 
	members of a household are also made. The type of the connection is 
	indicated by the edge attribute 'link_type'.
	"""
	assert N_classes % 2 == 0, 'number of classes needs to be even'

	G = nx.MultiGraph()


	# add students and their household members as nodes to the graph
	family_member_counter, family_counter = generate_students(G, school_type, 
				  N_classes, class_size, student_p_children, student_p_parents)

	# assign students to classes based on their age
	assign_classes(G, school_type, class_size, N_classes, N_floors)

	# add teachers and their household members as nodes to the graph
	generate_teachers(G, school_type, N_classes, family_member_counter, 
					  family_counter, teacher_p_adults, teacher_p_children)

	# set all contacts between members of families
	set_family_contacts(G)

	# generate intra-class contacts between all students in the same class and
	# additional (closer) contacts between table neighbours
	set_student_student_intra_class_contacts(G, N_classes)

	# add short (conversations) and long (meetings, friendships) contacts 
	# between teachers and other teachers
	set_teacher_teacher_social_contacts(G, school_type, N_classes,
				r_teacher_conversation, r_teacher_friend)

	# generate the teacher teaching schedule based on the school type
	teacher_schedule = get_scheduler(school_type)(N_classes)
	# generate the student schedule based on whether or not there is daycare
	# for the given school type
	student_schedule = generate_student_schedule(school_type, N_classes,
						class_size)

	# create teacher links due to team-teaching (currently only relevant for
	# lower secondary and upper secondary)
	set_teacher_teacher_teamteaching_contacts(G, school_type, teacher_schedule)

	# create links between teachers and students based on the teaching schedule
	set_teacher_student_teaching_contacts(G, school_type, N_classes, 
		teacher_schedule, student_schedule)

	# generate links between teachers that supervise groups during daycare
	# together
	set_teacher_teacher_daycare_supervision_contacts(G, school_type, 
		teacher_schedule)

	# create links between the teachers supervising the afternoon groups and
	# all students in the afternoon groups. Note: the information about 
	# which students are in which afternoon group are taken from the student
	# schedule, because students are assigned to afternoon groups at random.
	set_teacher_student_daycare_supervision_contacts(G, school_type, N_classes, 
		teacher_schedule, student_schedule)

	# add student contacts based on the groups they belong to druing the 
	# afternoon daycare. Only relevant for schools with daycare
	set_student_student_daycare_contacts(G, school_type, student_schedule)

	#teacher_schedule = teacher_schedule.reset_index()
	#student_schedule = student_schedule.reset_index()   
	return G, teacher_schedule, student_schedule



#############################################################
###													      ###
###    functions for graph modification after greation    ###
###													      ###
#############################################################

def map_contacts(G, contact_map, copy=False):
	"""
	Map the different link types between agents to contact types None, far, 
	intermediate and close, depending on link type. Contact
	types are added to the graph as additional edge attributes, next to link
	types.

	Parameters
	----------
	G : networkx Graph or MultiGrahp
		The School contact network with node (agent) types student, teacher
		and family members of student- and teachre households. Contacts of 
		different types (e.g. within households or during teaching) are 
		modelled as edges between nodes with different link types. 
		In MultiGraphs edges can exist on certain weekdaays only (1=Monday, ...,
		7=Sunday).
	contact_map : dict
		Dictionary that contains a contact type for every link type, specifying 
		the contact type in the given scenario (link type).
	copy : bool
		If copy=True, a copy of the graph will be made before contacts are
		mapped and the copy will then be returned by the function.

	Returns
	-------
	networkx Graph or MultiGraph
		if copy=True, the modified copy of the graph is returned.              
	"""
	if copy:
		G = G.copy()

	# links for which purely student mask wearing is important to determine the
	# contact type
	student_links = [c for c in contact_map.keys() if c.startswith('student_')]
	# links for which purely teacher mask wearing is important to determine the
	# contact type
	teacher_links = [c for c in contact_map.keys() if c.startswith('teacher_')]
	# links for which mask wearing behavuour of both students and teachers is
	# important to determine the contact type
	student_teacher_links = ['teaching_teacher_student', 
							 'daycare_supervision_teacher_student']

	household_links = ['student_household', 'teacher_household']

	_, N_weekdays, _ = get_teaching_framework()
	for wd in range(1, N_weekdays + 1):
		for n1, n2 in [(n1, n2) for (n1, n2, linkday) \
			in G.edges(data='weekday') if linkday == wd]:

			tmp = [n1, n2]
			tmp.sort()
			n1, n2 = tmp
			key = n1 + n2 + 'd{}'.format(wd)
			link_type = G[n1][n2][key]['link_type']
			G[n1][n2][key]['contact_type'] = contact_map[link_type]

	if copy:
		return G


def make_half_classes(class_size, N_classes, G, student_schedule, 
					  copy=False):
	"""
	Split classes in a school such that one half of every class is present on
	weekdays 1, 3 and 5, and the other half is present on weekdays 2 and 4. 
	Remove links from the graph and entries in the student schedule accordingly.
	
	Parameters
	----------
	class_size : integer
		Number of students in every class.
	N_classes : integer
		Number of classes in the school.
	G : networkx MultiGraph
		Graph in which the contacts (links) between all actors in the school
		(students, teachers, household members of students & teachers) are 
		stored for every day of the week (Monday=weekday 1, Sunday=weekday 7).
	student_schedule : pandas DataFrame
		Table of shape (N_classes * class_size * N_weekdays) X N_hours, where
		N_weekdays=7 and N_hours=9 for the 9 hours a day at school (including)
		lunch break usually covers. The table has a hierarchical index. 
		[week, student_ID]. Entries in the table are the class (=room) in which
		a student is at a given hour during a given day.
	copy : bool, optional
		If True, the graph and student schedule are copied before they are
		modified and returned by the function, instead of being modified
		inplace.
		
	Returns
	-------
	networkx MultiGraph
		If copy=True, a modified copy of the graph is returned.
	pandas DataFrame
		If copy=True, a modified copy of the student schedule is returned.
	"""
	if copy:
		G = G.copy()
		student_schedule = student_schedule.copy()
	
	# weekdays during which the first half of students is present
	weekdays_1 = [1, 3, 5]
	# weekdays during which the second half of students is present
	weekdays_2 = [2, 4]

	student_nodes = list(student_schedule.loc[1].index)
	half_class = int(class_size / 2)
	
	# list of students in the first half of every class
	students_first_half = []
	for c in range(N_classes):
		students_first_half.extend(student_nodes[\
							c * class_size:c * class_size + half_class])
	# list of students in the second half of every class
	students_second_half = []
	for c in range(N_classes):
		students_second_half.extend(student_nodes[\
							c * class_size + half_class:(c + 1) * class_size])
		
	
	## remove affected edges from the graph
	
	# link types that are affected by students not being present at school
	affected_links = ['student_student_intra_class', 
					  'student_student_table_neighbour',
					  'student_student_daycare',
					  'teaching_teacher_student',
					  'daycare_supervision_teacher_student']
	
	# find all edges on weekdays 1, 3 and 5 in which at least one student from
	# the second half of students (not present at school during these days)
	# is involved. Only edges with a link type that is affected by the absence
	# from school are selected (i.e. no family or friendship contacts)
	edges_to_remove_first_half = [(u, v, k) for \
		u, v, k, data in G.edges(keys=True, data=True)\
		if data['link_type'] in affected_links and \
			data['weekday'] in weekdays_1 and \
			(u in students_second_half or v in students_second_half)]

	# remove the selected edges from the graph
	for e in edges_to_remove_first_half:
		G.remove_edge(e[0], e[1], key=e[2])

	# repeat with weekdays 2 and 4 and the other half of students
	edges_to_remove_second_half = [(u, v, k) for \
		u, v, k, data in G.edges(keys=True, data=True) \
		if data['link_type'] in affected_links and \
			data['weekday'] in weekdays_2 and \
			(u in students_first_half or v in students_first_half)]

	for e in edges_to_remove_second_half:
		G.remove_edge(e[0], e[1], key=e[2])
	   
	
	## remove entries in the student schedule at the corresponding days
	
	# set all entries for students in the first half at weekdays 2 and 4 to
	# nan in the student schedule
	for s in students_first_half:
		for wd in weekdays_2:
			for hour in range(1, 10):
				student_schedule.loc[wd, s]['hour_{}'.format(hour)] = pd.NA
			
	# set all entries for students in the second half at weekdays 1, 3 and 5 to
	# nan in the student schedule
	for s in students_second_half:
		for wd in weekdays_1:
			for hour in range(1, 10):
				student_schedule.loc[wd, s]['hour_{}'.format(hour)] = pd.NA
				
	if copy:
		return G, student_schedule


def reduce_class_size(ratio, class_size, N_classes, G, student_schedule, 
					  copy=False):
	"""
	Reduce the size of a class by randomly removing a number of students
	equal to ratio * class_size every day.
	
	Parameters
	----------
	ratio : float
		Ratio of students that will be randomly removed every day
	class_size : integer
		Number of students in every class.
	N_classes : integer
		Number of classes in the school.
	G : networkx MultiGraph
		Graph in which the contacts (links) between all actors in the school
		(students, teachers, household members of students & teachers) are 
		stored for every day of the week (Monday=weekday 1, Sunday=weekday 7).
	student_schedule : pandas DataFrame
		Table of shape (N_classes * class_size * N_weekdays) X N_hours, where
		N_weekdays=7 and N_hours=9 for the 9 hours a day at school (including)
		lunch break usually covers. The table has a hierarchical index. 
		[week, student_ID]. Entries in the table are the class (=room) in which
		a student is at a given hour during a given day.
	copy : bool, optional
		If True, the graph and student schedule are copied before they are
		modified and returned by the function, instead of being modified
		inplace.
		
	Returns
	-------
	networkx MultiGraph
		If copy=True, a modified copy of the graph is returned.
	pandas DataFrame
		If copy=True, a modified copy of the student schedule is returned.
	"""
	if copy:
		G = G.copy()
		student_schedule = student_schedule.copy()
	
	N_remove = round(ratio * class_size)

	# link types that are affected by students not being present at school
	affected_links = ['student_student_intra_class', 
					  'student_student_table_neighbour',
					  'student_student_daycare',
					  'teaching_teacher_student',
					  'daycare_supervision_teacher_student']

	for wd in range(1, 6):
		for c in range(1, N_classes + 1):
			student_nodes = student_schedule[student_schedule['hour_1'] == c]\
					.loc[wd].index
			# pick a number of students from every class and remove them
			students_to_remove = np.random.choice(student_nodes, N_remove, \
				replace=False)

			## remove edges from the graph
			# find all edges on the given weekday in which at least one student
			# from the list of students to remove is involved. Only edges with a
			# link type that is affected by the absence from school are selected 
			# (i.e. no family or friendship contacts)
			edges_to_remove = [(u, v, k) for u, v, k, data in \
			G.edges(keys=True, data=True) if data['link_type'] in \
			affected_links and data['weekday'] == wd and \
			(u in students_to_remove or v in students_to_remove)]
			# remove affected edges from the graph
			for e in edges_to_remove:
				G.remove_edge(e[0], e[1], key=e[2])
	
			## remove entries in the student schedule at the corresponding days
	
			# set all entries for students on the given weekday to nan in the 
			# student schedule
			for s in students_to_remove:
				for hour in range(1, 10):
					student_schedule.loc[wd, s]['hour_{}'.format(hour)] = pd.NA
									
	if copy:
		return G, student_schedule

def add_between_class_contacts(ratio, class_size, N_classes, G, copy=False):
	"""
	Adds additional contacts of type "student_student_friends" between
	a number of students equal to ratio * class_size from every class
	and a number of students equal to ratio *class_size from other classes.
	These pairs of students stay the same for every day of the week.
	
	Parameters
	----------
	ratio : float
		Ratio of students that will be randomly removed every day
	class_size : integer
		Number of students in every class.
	N_classes : integer
		Number of classes in the school.
	G : networkx MultiGraph
		Graph in which the contacts (links) between all actors in the school
		(students, teachers, household members of students & teachers) are 
		stored for every day of the week (Monday=weekday 1, Sunday=weekday 7).
	copy : bool
		If true, copies the graph and returns the copy. Otherwise modifies the
		graph inplace.
		
	Returns
	-------
	networkx MultiGraph
		If copy=True, a modified copy of the graph is returned.
	"""
	if copy:
		G = G.copy()

	_, N_weekdays, _ = get_teaching_framework()

	N_students = round(ratio * class_size)
	for c in range(1, N_classes + 1):
	    students_in_class = [n[0] for n in G.nodes(data=True) \
	        if n[1]['type'] == 'student' and n[1]['unit'] == 'class_{}'.format(c)]
	    sources = np.random.choice(students_in_class, N_students, replace=False)
	    
	    students_in_other_classes = [n[0] for n in G.nodes(data=True) \
	        if n[1]['type'] == 'student' and n[1]['unit'] != 'class_{}'.format(c)]
	    targets = np.random.choice(students_in_other_classes, N_students, replace=False)
	    
	    for source, target in zip(sources, targets):
	    	for wd in range(1, N_weekdays + 1):
		        tmp = [source, target]
		        tmp.sort()
		        n1, n2 = tmp
		        G.add_edge(n1, n2, link_type='student_student_friends',
		                            weekday = wd,
		                            key = n1 + n2 + 'd{}'.format(wd))

	if copy:
		return G


def get_node_list(G):
	"""
	Extract information about the family (household) number, location and node
	type for every node present in the graph into a DataFrame.

	Parameters
	----------
	G : networkx Graph or MultiGraph
		Graph that holds the agents (nodes) acting in the school and their 
		contacts (edges). Nodes have an ID starting with "s" for students, "t"
		for teachers and "f" for family members. Nodes also have attributes 
		'type' indicating an agent's type, family', indicating the household 
		number of an agent and 'location', indicating the agent's location which
		is 'home' for household members that are not students or teachers, 
		'faculty_room' for teachers and classroom 'class_i' for students, where
		i is the class the student belongs to. This has the implicit assumption
		that students of the same class always stay in the same room and the
		room number always equals the class number.

	Returns
	-------
	pandas DataFrame
		table of shape N_agents X [ID, family, locatoin, type], where 
		N_agents = N_students + N_teachers + N_family_members.

	"""
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

