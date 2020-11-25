import numpy as np
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

import sys
sys.path.insert(0,'..')
from model_SEIRX import*


## data collection functions ##

def count_E_student(model):
    E = np.asarray(
        [a.exposed for a in model.schedule.agents if a.type == 'student']).sum()
    return E


def count_I_student(model):
    I = np.asarray(
        [a.infectious for a in model.schedule.agents if a.type == 'student']).sum()
    return I


def count_I_symptomatic_student(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'student'and a.symptomatic_course)]).sum()
    return I


def count_I_asymptomatic_student(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'student'and a.symptomatic_course == False)]).sum()
    return I


def count_R_student(model):
    R = np.asarray(
        [a.recovered for a in model.schedule.agents if a.type == 'student']).sum()
    return R


def count_X_student(model):
    X = np.asarray(
        [a.quarantined for a in model.schedule.agents if a.type == 'student']).sum()
    return X


def count_E_teacher(model):
    E = np.asarray(
        [a.exposed for a in model.schedule.agents if a.type == 'teacher']).sum()
    return E


def count_I_teacher(model):
    I = np.asarray(
        [a.infectious for a in model.schedule.agents if a.type == 'teacher']).sum()
    return I


def count_I_symptomatic_teacher(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'teacher'and a.symptomatic_course)]).sum()
    return I


def count_I_asymptomatic_teacher(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'teacher'and a.symptomatic_course == False)]).sum()
    return I


def count_R_teacher(model):
    R = np.asarray(
        [a.recovered for a in model.schedule.agents if a.type == 'teacher']).sum()
    return R


def count_X_teacher(model):
    X = np.asarray(
        [a.quarantined for a in model.schedule.agents if a.type == 'teacher']).sum()
    return X


def count_E_family_member(model):
    E = np.asarray(
        [a.exposed for a in model.schedule.agents if a.type == 'family_member']).sum()
    return E


def count_I_family_member(model):
    I = np.asarray(
        [a.infectious for a in model.schedule.agents if a.type == 'family_member']).sum()
    return I


def count_I_symptomatic_family_member(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'family_member'and a.symptomatic_course)]).sum()
    return I


def count_I_asymptomatic_family_member(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'family_member'and a.symptomatic_course == False)]).sum()
    return I


def count_R_family_member(model):
    R = np.asarray(
        [a.recovered for a in model.schedule.agents if a.type == 'family_member']).sum()
    return R


def count_X_family_member(model):
    X = np.asarray(
        [a.quarantined for a in model.schedule.agents if a.type == 'family_member']).sum()
    return X


def check_reactive_student_screen(model):
    return model.screened_agents['reactive']['student']


def check_follow_up_student_screen(model):
    return model.screened_agents['follow_up']['student']


def check_preventive_student_screen(model):
    return model.screened_agents['preventive']['student']


def check_reactive_teacher_screen(model):
    return model.screened_agents['reactive']['teacher']


def check_follow_up_teacher_screen(model):
    return model.screened_agents['follow_up']['teacher']


def check_preventive_teacher_screen(model):
    return model.screened_agents['preventive']['teacher']


def check_reactive_family_member_screen(model):
    return model.screened_agents['reactive']['family_member']


def check_follow_up_family_member_screen(model):
    return model.screened_agents['follow_up']['family_member']


def check_preventive_family_member_screen(model):
    return model.screened_agents['preventive']['family_member']



data_collection_functions = \
    {
    'student':
        {
        'E':count_E_student,
        'I':count_I_student,
        'I_asymptomatic':count_I_asymptomatic_student,
        'I_symptomatic':count_I_symptomatic_student,
        'R':count_R_student,
        'X':count_X_student
         },
    'teacher':
        {
        'E':count_E_teacher,
        'I':count_I_teacher,
        'I_asymptomatic':count_I_asymptomatic_teacher,
        'I_symptomatic':count_I_symptomatic_teacher,
        'R':count_R_teacher,
        'X':count_X_teacher
         },
    'family_member':
        {
        'E':count_E_family_member,
        'I':count_I_family_member,
        'I_asymptomatic':count_I_asymptomatic_family_member,
        'I_symptomatic':count_I_symptomatic_family_member,
        'R':count_R_family_member,
        'X':count_X_family_member
         }
    }




class SEIRX_school(SEIRX):

    def __init__(self, G, verbosity=0, testing=True,
        exposure_duration=4, time_until_symptoms=6,infection_duration=11, 
        quarantine_duration=14, subclinical_modifier=1,
        infection_risk_contact_type_weights={
            'very_far': 0.1, 'far': 0.5, 'intermediate': 1, 'close': 3},
        K1_contact_types=['close'], diagnostic_test_type='one_day_PCR',
        preventive_screening_test_type='one_day_PCR',
        follow_up_testing_interval=None, liberating_testing=False,
        index_case='employee', 
        agent_types={'type1': {'screening_interval': None,
                              'index_probability': None,
                              'transmission_risk': 0.015,
                              'reception_risk': 0.015,
                              'symptom_probability': 0.6}},
        seed=None):

        super().__init__(G, verbosity, testing, exposure_duration, 
            time_until_symptoms, infection_duration, quarantine_duration,
            subclinical_modifier, infection_risk_contact_type_weights,
            K1_contact_types, diagnostic_test_type, 
            preventive_screening_test_type, follow_up_testing_interval,
            liberating_testing, index_case, agent_types, seed)


        
        # data collectors to save population counts and agent states every
        # time step
        model_reporters = {}
        for agent_type in self.agent_types:
            for state in ['E','I','I_asymptomatic','I_symptomatic','R','X']:
                model_reporters.update({'{}_{}'.format(state, agent_type):\
                    data_collection_functions[agent_type][state]})

        model_reporters.update(\
            {
            'screen_students_reactive':check_reactive_student_screen,
            'screen_students_follow_up':check_follow_up_student_screen,
            'screen_students_preventive':check_preventive_student_screen,
            'screen_teachers_reactive':check_reactive_teacher_screen,
            'screen_teachers_follow_up':check_follow_up_teacher_screen,
            'screen_teachers_preventive':check_preventive_teacher_screen,
            'screen_family_members_reactive':check_reactive_family_member_screen,
            'screen_family_members_follow_up':check_follow_up_family_member_screen,
            'screen_family_members_preventive':check_preventive_family_member_screen,
            'N_diagnostic_tests':get_N_diagnostic_tests,
            'N_preventive_screening_tests':get_N_preventive_screening_tests,
            'undetected_infections':get_undetected_infections,
            'predetected_infections':get_predetected_infections,
            'pending_test_infections':get_pending_test_infections
            })

        agent_reporters =\
            {
            'infection_state':get_infection_state,
            'quarantine_state':get_quarantine_state
             }

        self.datacollector = DataCollector(
            model_reporters = model_reporters,
            agent_reporters = agent_reporters)


    def step(self):
        if self.testing:
            for agent_type in self.agent_types:
                for screen_type in ['reactive', 'follow_up', 'preventive']:
                    self.screened_agents[screen_type][agent_type] = False

            if self.verbosity > 0: 
                print('* testing and tracing *')
            
            self.test_symptomatic_agents()
            

            # collect and act on new test results
            agents_with_test_results = self.collect_test_results()
            for a in agents_with_test_results:
                a.act_on_test_result()
            
            self.quarantine_contacts()

            # screening:
            # a screen should take place if
            # (a) there are new positive test results
            # (b) as a follow-up screen for a screen that was initiated because
            # of new positive cases
            # (c) if there is a preventive screening policy and it is time for
            # a preventive screen in a given agent group

            # (a)
            if (self.testing == 'background' or self.testing == 'preventive')\
               and self.new_positive_tests == True:
                for agent_type in ['teacher', 'student']:
	                self.screen_agents(
	                    agent_type, self.Testing.diagnostic_test_type, 'reactive')
	                self.scheduled_follow_up_screen[agent_type] = True

            # (b)
            elif (self.testing == 'background' or self.testing == 'preventive') and \
                self.Testing.follow_up_testing_interval != None and \
                sum(list(self.scheduled_follow_up_screen.values())) > 0:
                for agent_type in ['teacher', 'student']:
                    if self.scheduled_follow_up_screen[agent_type] and\
                       self.days_since_last_agent_screen[agent_type] >=\
                       self.Testing.follow_up_testing_interval:
                        self.screen_agents(
                            agent_type, self.Testing.diagnostic_test_type, 'follow_up')
                    else:
                        if self.verbosity > 0: 
                            print('not initiating {} follow-up screen (last screen too close)'\
                            	.format(agent_type))

            # (c) 
            elif self.testing == 'preventive' and \
                np.any(list(self.Testing.screening_intervals.values())):

                for agent_type in ['teacher', 'student']:
                    if self.Testing.screening_intervals[agent_type] != None and\
                    self.days_since_last_agent_screen[agent_type] >=\
                    self.Testing.screening_intervals[agent_type]:
                        self.screen_agents(agent_type,
                            self.Testing.preventive_screening_test_type, 'preventive')
                    else:
                        if self.verbosity > 0: 
                            print('not initiating {} preventive screen (last screen too close)'\
                                .format(agent_type))

            else:
                # do nothing
                pass

            for agent_type in self.agent_types:
            	if not (self.screened_agents['reactive'][agent_type] or \
            		    self.screened_agents['follow_up'][agent_type] or \
            		    self.screened_agents['preventive'][agent_type]):
            			self.days_since_last_agent_screen[agent_type] += 1


        if self.verbosity > 0: print('* agent interaction *')
        self.datacollector.collect(self)
        self.schedule.step()
        self.Nstep += 1
