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


def check_student_screen(model):
    return model.screened_agents['student']


def check_teacher_screen(model):
    return model.screened_agents['teacher']



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
        infection_duration=11, exposure_duration=4, time_until_symptoms=6,
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
                              'symptom_probability': 0.6}}):

        super().__init__(G, verbosity, testing, infection_duration, 
            exposure_duration, time_until_symptoms, quarantine_duration,
            subclinical_modifier, infection_risk_contact_type_weights,
            K1_contact_types, diagnostic_test_type, 
            preventive_screening_test_type, follow_up_testing_interval,
            liberating_testing, index_case, agent_types)


        
        # data collectors to save population counts and agent states every
        # time step
        model_reporters = {}
        for agent_type in self.agent_types:
            for state in ['E','I','I_asymptomatic','I_symptomatic','R','X']:
                model_reporters.update({'{}_{}'.format(state, agent_type):\
                    data_collection_functions[agent_type][state]})

        model_reporters.update(\
            {
            'screen_students':check_student_screen,
            'screen_teachers':check_teacher_screen,
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
