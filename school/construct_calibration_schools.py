import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import construct_school_network as csn
import sys
from os.path import join

from importlib import reload

# for progress bars
from ipywidgets import IntProgress
from IPython.display import display
import time

# different age structures in Austrian school types
age_brackets = {'primary':[6, 7, 8, 9],
                'primary_dc':[6, 7, 8, 9],
                'lower_secondary':[10, 11, 12, 13],
                'lower_secondary_dc':[10, 11, 12, 13],
                'upper_secondary':[14, 15, 16, 17],
                'secondary':[10, 11, 12, 13, 14, 15, 16, 17],
                'secondary_dc':[10, 11, 12, 13, 14, 15, 16, 17]
               }

school_characteristics = {
    # Volksschule: Schulen: 3033, Klassen: 18245, Schüler*innen: 339382
    'primary':            {'classes':8, 'students':19},
    'primary_dc':         {'classes':8, 'students':19},
    
    # Hauptschulen: 47, Klassen 104, Schüler*innen: 1993
    # Neue Mittelschule: Schulen 1131, Klassen: 10354, Schüler*innen: 205905
    # Sonderschulen: 292, Klassen: 1626, Schüler*innen: 14815
    # Gesamt: Schulen: 1470, Klassen: 12084, Schüler*innen: 222713
    'lower_secondary':    {'classes':8, 'students':18},
    'lower_secondary_dc': {'classes':8, 'students':18},
    
    # Oberstufenrealgymnasium: Schulen 114, Klassen 1183, Schüler*innen: 26211
    # BMHS: schulen 734, Klassen 8042, Schüler*innen 187592
    # Gesamt: Schulen: 848, Klassen 9225, Schüler*innen: 213803
    'upper_secondary':    {'classes':10, 'students':23}, # rounded down from 10.8 classes
    
    # AHS Langform: Schulen 281, Klassen 7610, schüler*innen 179633
    'secondary':          {'classes':28, 'students':24}, # rounded up from 27.1 classes
    'secondary_dc':       {'classes':28, 'students':24} # rounded up from 27.1 classes
}
# given the precondition that the family has at least one child, how many
# children does the family have?
p_children = {1:0.4815, 2:0.3812, 3:0.1069, 4:0.0304}

# probability of being a single parent, depending on the number of children
p_parents = {1:{1:0.1805, 2:0.8195},
             2:{1:0.1030, 2:0.8970},
             3:{1:0.1174, 2:0.8826},
             4:{1:0.1256, 2:0.8744}
            }

# probability of a household having a certain size, independent of having a child
teacher_p_adults = {1:0.4655, 2:0.5186, 3:0.0159}
teacher_p_children = {1:{0:0.8495, 1:0.0953, 2:0.0408, 3:0.0144},
                      2:{0:0.4874, 1:0.2133, 2:0.2158, 3:0.0835},
                      3:{0:1, 1:0, 2:0, 3:0}}

# Note: student_student_daycare overwrites student_student_intra_class and
# student_student_table_neighbour

# Note: teacher_teacher_daycare_supervision and teacher_teacher_team_teaching 
# overwrite teacher_teacher_short and teacher_teacher_long
contact_map = {
    'student_household':{True:'close', False:'close'}, # no-mask setting
    'student_student_friends':{True:'intermediate', False:'intermediate'}, # no-mask setting, not implemented
    'student_student_intra_class':{True:None, False:'far'}, # only student masks are important
    'student_student_table_neighbour':{True:'far', False:'intermediate'}, # only student masks are important
    'student_student_daycare':{True:None, False:'far'},
    'teacher_household':{True:'close', False:'close'}, # no-mask setting
    'teacher_teacher_short':{True: None, False:'far'}, # only teacher masks are important
    'teacher_teacher_long':{True:'far', False:'intermediate'}, # only teacher masks are important
    'teacher_teacher_team_teaching':{True:'far', False:'intermediate'}, # only teacher masks are important
    'teacher_teacher_daycare_supervision':{True:'far', False:'intermediate'}, # only teacher masks are important
    'teaching_teacher_student':{True:'far', False:'intermediate'}, # both teacher and student masks are important
    'daycare_supervision_teacher_student':{True:'far', False:'intermediate'}, # both teacher and student masks are important
}


# teacher social contacts
r_teacher_friend = 0.059
r_teacher_conversation = 0.255


student_mask = False
teacher_mask = False

school_type = sys.argv[1]
instances = int(sys.argv[2])

N_classes = school_characteristics[school_type]['classes']
class_size = school_characteristics[school_type]['students']
school_name = '{}_classes-{}_students-{}'.format(school_type,\
            N_classes, class_size)
age_bracket = age_brackets[school_type]
N_floors = 1

res_path = join('../data/school/calibration_schools', school_type)

for instance in range(1, instances + 1):
	if instance % 100 == 0:
		print('{} {}/{}'.format(school_type, instance, instances))
    instance_name = school_name + '_{}'.format(instance)
    
    G, teacher_schedule, student_schedule = csn.compose_school_graph(\
                school_type, N_classes, class_size, 
                N_floors, p_children, p_parents, teacher_p_adults,
                teacher_p_children, r_teacher_conversation, r_teacher_friend)

    csn.map_contacts(G, student_mask, teacher_mask, contact_map)
    
    family_members = [n for n, tp in G.nodes(data='type') \
                  if tp in ['family_member_student', 'family_member_teacher']]
    G.remove_nodes_from(family_members)
                                          
    nx.readwrite.gpickle.write_gpickle(G, join(res_path, \
    	'{}.gpickle'.format(instance_name)))

    # extract node list
    node_list = csn.get_node_list(G)
    node_list.to_csv(join(res_path, '{}_node_list.csv'
                        .format(school_name)), index=False)

    # format schedule
    for schedule, agent_type in zip([teacher_schedule, student_schedule], ['teachers', 'students']):
        schedule.to_csv(join(res_path, '{}_schedule_{}.csv'
                            .format(school_name, agent_type)))
                    