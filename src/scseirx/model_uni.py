import numpy as np
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from scseirx.model_SEIRX import *


## data collection functions ##

def count_S_student(model):
    S = np.asarray([1 for a in model.schedule.agents if a.type == 'student' and\
                    a.exposed == False and a.recovered == False \
                    and a.infectious == False]).sum()
    return S


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

def count_V_student(model):
    V = np.asarray([a.vaccinated for a in model.schedule.agents if
        (a.type == 'student')]).sum()
    return V

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


def count_S_lecturer(model):
    S = np.asarray([1 for a in model.schedule.agents if a.type == 'feacher' and\
                    a.exposed == False and a.recovered == False \
                    and a.infectious == False]).sum()
    return S


def count_E_lecturer(model):
    E = np.asarray(
        [a.exposed for a in model.schedule.agents if a.type == 'lecturer']).sum()
    return E


def count_I_lecturer(model):
    I = np.asarray(
        [a.infectious for a in model.schedule.agents if a.type == 'lecturer']).sum()
    return I


def count_I_symptomatic_lecturer(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'lecturer'and a.symptomatic_course)]).sum()
    return I

def count_V_lecturer(model):
    V = np.asarray([a.vaccinated for a in model.schedule.agents if
        (a.type == 'lecturer')]).sum()
    return V

def count_I_asymptomatic_lecturer(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'lecturer'and a.symptomatic_course == False)]).sum()
    return I


def count_R_lecturer(model):
    R = np.asarray(
        [a.recovered for a in model.schedule.agents if a.type == 'lecturer']).sum()
    return R


def count_X_lecturer(model):
    X = np.asarray(
        [a.quarantined for a in model.schedule.agents if a.type == 'lecturer']).sum()
    return X


def check_reactive_student_screen(model):
    return model.screened_agents['reactive']['student']


def check_follow_up_student_screen(model):
    return model.screened_agents['follow_up']['student']


def check_preventive_student_screen(model):
    return model.screened_agents['preventive']['student']


def check_reactive_lecturer_screen(model):
    return model.screened_agents['reactive']['lecturer']


def check_follow_up_lecturer_screen(model):
    return model.screened_agents['follow_up']['lecturer']


def check_preventive_lecturer_screen(model):
    return model.screened_agents['preventive']['lecturer']



data_collection_functions = \
    {
    'student':
        {
        'S':count_S_student,
        'E':count_E_student,
        'I':count_I_student,
        'I_asymptomatic':count_I_asymptomatic_student,
        'V':count_V_student,
        'I_symptomatic':count_I_symptomatic_student,
        'R':count_R_student,
        'X':count_X_student
         },
    'lecturer':
        {
        'S':count_S_lecturer,
        'E':count_E_lecturer,
        'I':count_I_lecturer,
        'I_asymptomatic':count_I_asymptomatic_lecturer,
        'V':count_V_lecturer,
        'I_symptomatic':count_I_symptomatic_lecturer,
        'R':count_R_lecturer,
        'X':count_X_lecturer
         }
    }



class SEIRX_uni(SEIRX):
    '''
    Model specific parameters:

    See documentation of model_SEIRX for the description of other parameters.
    '''

    def __init__(self, G,
        verbosity = 0,
        base_transmission_risk = 0.05,
        testing = 'diagnostic',
        exposure_duration = [5.0, 1.9],
        time_until_symptoms = [6.4, 0.8],
        infection_duration = [10.91, 3.95],
        quarantine_duration = 10,
        subclinical_modifier = 0.6,
        infection_risk_contact_type_weights = {
            'very_far': 0.1,
            'far': 0.25,
            'intermediate': 0.5,
            'close': 1},
        K1_contact_types = ['close'],
        diagnostic_test_type = 'one_day_PCR',
        preventive_screening_test_type = 'same_day_antigen',
        follow_up_testing_interval = None,
        liberating_testing = False,
        index_case = 'lecturer',
        agent_types = {
            'lecturer':      {'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_probability': 0},
            'student':      {'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_probability': 0}},
        mask_filter_efficiency = {'exhale':0, 'inhale':0},
        transmission_risk_ventilation_modifier = 0,
        transmission_risk_vaccination_modifier = {'reception':1, 'transmission':0},
        seed = None):

        age_transmission_risk_discount = \
             {'slope':0,
              'intercept':1},
        age_symptom_modification = \
             {'slope':0,
              'intercept':1}

        super().__init__(G,
            verbosity = verbosity,
            base_transmission_risk = base_transmission_risk,
            testing = testing,
            exposure_duration = exposure_duration,
            time_until_symptoms = time_until_symptoms,
            infection_duration = infection_duration,
            quarantine_duration = quarantine_duration,
            subclinical_modifier = subclinical_modifier,
            infection_risk_contact_type_weights = \
                         infection_risk_contact_type_weights,
            K1_contact_types = K1_contact_types,
            diagnostic_test_type = diagnostic_test_type,
            preventive_screening_test_type = \
                         preventive_screening_test_type,
            follow_up_testing_interval = follow_up_testing_interval,
            liberating_testing = liberating_testing,
            index_case = index_case,
            agent_types = agent_types,
            age_transmission_risk_discount = \
                 age_transmission_risk_discount,
            age_symptom_modification = age_symptom_modification,
            mask_filter_efficiency = mask_filter_efficiency,
            transmission_risk_ventilation_modifier = \
                         transmission_risk_ventilation_modifier,
            transmission_risk_vaccination_modifier = \
                        transmission_risk_vaccination_modifier,
            seed = seed)

        # agent types that are included in preventive, background & follow-up
        # screens
        self.screening_agents = ['lecturer', 'student']

        # define, whether or not a multigraph that defines separate connections
        # for every day of the week is used
        self.dynamic_connections = True
        self.MG = G
        self.weekday_connections = {}
        all_edges = self.MG.edges(keys=True, data='weekday')
        N_weekdays = 7
        for i in range(1, N_weekdays + 1):
            wd_edges = [(u, v, k) for (u, v, k, wd) in all_edges if wd == i]
            self.weekday_connections[i] = G.edge_subgraph(wd_edges).copy()


        # data collectors to save population counts and agent states every
        # time step
        model_reporters = {}
        for agent_type in self.agent_types:

            for state in ['S','E','I','I_asymptomatic','I_symptomatic','R','X', 'V']:

                model_reporters.update({'{}_{}'.format(state, agent_type):\
                    data_collection_functions[agent_type][state]})

        model_reporters.update(\
            {
            'screen_students_reactive':check_reactive_student_screen,
            'screen_students_follow_up':check_follow_up_student_screen,
            'screen_students_preventive':check_preventive_student_screen,
            'screen_lecturers_reactive':check_reactive_lecturer_screen,
            'screen_lecturers_follow_up':check_follow_up_lecturer_screen,
            'screen_lecturers_preventive':check_preventive_lecturer_screen,
            'N_diagnostic_tests':get_N_diagnostic_tests,
            'N_preventive_screening_tests':get_N_preventive_screening_tests,
            'diagnostic_test_detected_infections_student':\
                    get_diagnostic_test_detected_infections_student,
            'diagnostic_test_detected_infections_lecturer':\
                    get_diagnostic_test_detected_infections_lecturer,
            'preventive_test_detected_infections_student':\
                    get_preventive_test_detected_infections_student,
            'preventive_test_detected_infections_lecturer':\
                    get_preventive_test_detected_infections_lecturer,
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

    def calculate_transmission_probability(self, source, target, base_risk):
        """
        Calculates the risk of transmitting an infection between a source agent
        and a target agent given the model's and agent's properties and the base
        transmission risk.

        Transmission is an independent Bernoulli trial with a probability of
        success p. The probability of transmission without any modifications
        by for example masks or ventilation is given by the base_risk, which
        is calibrated in the model. The probability is modified by contact type
        q1 (also calibrated in the model), age of the transmitting agent q2
        & age of the receiving agent q3 (both age dependencies are linear in
        age and the same, and they are calibrated), infection progression q4
        (from literature), reduction of viral load due to a sublclinical course
        of the disease q5 (from literature), reduction of exhaled viral load of
        the source by mask wearing q6 (from literature), reduction of inhaled
        viral load by the target q7 (from literature), and ventilation of the
        rooms q8 (from literature).

        Parameters
        ----------
        source : agent_SEIRX
            Source agent that transmits the infection to the target.
        target: agent_SEIRX
            Target agent that (potentially) receives the infection from the
            source.
        base_risk : float
            Probability p of infection transmission without any modifications
            through prevention measures.

        Returns
        -------
        p : float
            Modified transmission risk.
        """

        q1 = self.get_transmission_risk_contact_type_modifier(source, target)
        q2 = self.get_transmission_risk_progression_modifier(source)
        q3 = self.get_transmission_risk_subclinical_modifier(source)
        q4 = self.get_transmission_risk_exhale_modifier(source)
        q5 = self.get_transmission_risk_inhale_modifier(target)
        q6 = self.get_transmission_risk_ventilation_modifier()
        q7 = self.get_transmission_risk_vaccination_modifier_reception(target)
        q8 = self.get_transmission_risk_vaccination_modifier_transmission(source)

        p = 1 - (1 - base_risk * (1 - q1) * (1 - q2) * (1 - q3) * \
            (1 - q4) * (1 - q5) * (1 - q6) * (1 - q7) * (1 - q8))

        return p
