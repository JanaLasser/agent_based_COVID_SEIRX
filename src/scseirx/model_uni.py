import numpy as np
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from scseirx.model_SEIRX import *


## data collection functions ##

def count_S_unistudent(model):
    S = np.asarray([1 for a in model.schedule.agents if a.type == 'unistudent' and\
                    a.exposed == False and a.recovered == False \
                    and a.infectious == False]).sum()
    return S


def count_E_unistudent(model):
    E = np.asarray(
        [a.exposed for a in model.schedule.agents if a.type == 'unistudent']).sum()
    return E


def count_I_unistudent(model):
    I = np.asarray(
        [a.infectious for a in model.schedule.agents if a.type == 'unistudent']).sum()
    return I


def count_I_symptomatic_unistudent(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'unistudent'and a.symptomatic_course)]).sum()
    return I

def count_V_unistudent(model):
    V = np.asarray([a.vaccinated for a in model.schedule.agents if
        (a.type == 'unistudent')]).sum()
    return V

def count_I_asymptomatic_unistudent(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'unistudent'and a.symptomatic_course == False)]).sum()
    return I


def count_R_unistudent(model):
    R = np.asarray(
        [a.recovered for a in model.schedule.agents if a.type == 'unistudent']).sum()
    return R


def count_X_unistudent(model):
    X = np.asarray(
        [a.quarantined for a in model.schedule.agents if a.type == 'unistudent']).sum()
    return X


def count_S_lecturer(model):
    S = np.asarray([1 for a in model.schedule.agents if a.type == 'lecturer' and\
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


def check_reactive_unistudent_screen(model):
    return model.screened_agents['reactive']['unistudent']


def check_follow_up_unistudent_screen(model):
    return model.screened_agents['follow_up']['unistudent']


def check_preventive_unistudent_screen(model):
    return model.screened_agents['preventive']['unistudent']


def check_reactive_lecturer_screen(model):
    return model.screened_agents['reactive']['lecturer']


def check_follow_up_lecturer_screen(model):
    return model.screened_agents['follow_up']['lecturer']


def check_preventive_lecturer_screen(model):
    return model.screened_agents['preventive']['lecturer']



data_collection_functions = \
    {
    'unistudent':
        {
        'S':count_S_unistudent,
        'E':count_E_unistudent,
        'I':count_I_unistudent,
        'I_asymptomatic':count_I_asymptomatic_unistudent,
        'V':count_V_unistudent,
        'I_symptomatic':count_I_symptomatic_unistudent,
        'R':count_R_unistudent,
        'X':count_X_unistudent
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
            'unistudent':      {'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_probability': 0}},
        mask_filter_efficiency = {'exhale':0, 'inhale':0},
        age_transmission_risk_discount = \
             {'slope':0,
              'intercept':1},
        age_symptom_modification = \
             {'slope':0,
              'intercept':0.6},
        transmission_risk_ventilation_modifier = 0,
        transmission_risk_vaccination_modifier = {'reception':1, 'transmission':0},
        N_days_in_network = 7,
        seed = None):


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
            N_days_in_network = N_days_in_network,
            seed = seed)

        # type of the model for some type-specific functionality
        self.model = 'uni'

        # agent types that are included in preventive, background & follow-up
        # screens
        self.screening_agents = ['lecturer', 'unistudent']

        # define, whether or not a multigraph that defines separate connections
        # for every day of the week is used
        self.dynamic_connections = True
        self.MG = G
        self.day_connections = {}
        all_edges = self.MG.edges(keys=True, data='day')
        for i in range(1, self.N_days_in_network + 1):
            day_edges = [(u, v, k) for (u, v, k, day) in all_edges if day == i]
            self.day_connections[i] = G.edge_subgraph(day_edges).copy()


        # data collectors to save population counts and agent states every
        # time step
        model_reporters = {}
        for agent_type in self.agent_types:

            for state in ['S','E','I','I_asymptomatic','I_symptomatic','R','X', 'V']:

                model_reporters.update({'{}_{}'.format(state, agent_type):\
                    data_collection_functions[agent_type][state]})

        model_reporters.update(\
            {
            'screen_unistudents_reactive':check_reactive_unistudent_screen,
            'screen_unistudents_follow_up':check_follow_up_unistudent_screen,
            'screen_unistudents_preventive':check_preventive_unistudent_screen,
            'screen_lecturers_reactive':check_reactive_lecturer_screen,
            'screen_lecturers_follow_up':check_follow_up_lecturer_screen,
            'screen_lecturers_preventive':check_preventive_lecturer_screen,
            'N_diagnostic_tests':get_N_diagnostic_tests,
            'N_preventive_screening_tests':get_N_preventive_screening_tests,
            'diagnostic_test_detected_infections_unistudent':\
                    get_diagnostic_test_detected_infections_unistudent,
            'diagnostic_test_detected_infections_lecturer':\
                    get_diagnostic_test_detected_infections_lecturer,
            'preventive_test_detected_infections_unistudent':\
                    get_preventive_test_detected_infections_unistudent,
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
        
    def get_transmission_risk_contact_duration_modifier(self, source, target):
        # construct the edge key as combination between agent IDs and day
        n1 = source.ID
        n2 = target.ID
        tmp = [n1, n2]
        tmp.sort()
        n1, n2 = tmp
        key = '{}{}d{}'.format(n1, n2, self.day)
        # duration of the contact in minutes
        duration = self.G.get_edge_data(n1, n2, key)['duration']

        # the link weight is a multiplicative modifier of the link strength.
        # contacts of type "close" have, by definition, a weight of 1. Contacts
        # of type intermediate, far or very far have a weight < 1 and therefore
        # are less likely to transmit an infection. For example, if the contact
        # type far has a weight of 0.2, a contact of type far has only a 20%
        # chance of transmitting an infection, when compared to a contact of
        # type close. To calculate the probability of success p in the Bernoulli
        # trial, we need to reduce the base risk (or base probability of success)
        # by the modifications introduced by preventive measures. These
        # modifications are formulated in terms of "probability of failure", or
        # "q". A low contact weight has a high probability of failure, therefore
        # we return q = 1 - contact_weight here.
        
        # assumed average contact duration between students in school
        calibrated_duration = 360 
        # contact weight calibrated to contacts of students in school
        calibrated_contact_weight = self.infection_risk_contact_type_weights['far']
        
        #contact_weight = calibrated_contact_weight * duration /  calibrated_duration
        contact_weight = 1

        q1 = 1 - contact_weight

        return q1

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

        q1 = self.get_transmission_risk_contact_duration_modifier(source, target)
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
