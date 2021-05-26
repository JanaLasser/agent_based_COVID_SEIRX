import numpy as np
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from scseirx.model_SEIRX import *


## data collection functions ##
def count_S_resident(model):
    S = np.asarray([1 for a in model.schedule.agents if a.type == 'resident' and\
                    a.exposed == False and a.recovered == False \
                    and a.infectious == False]).sum()
    return S
    
    
def count_E_resident(model):
    E = np.asarray(
        [a.exposed for a in model.schedule.agents if a.type == 'resident']).sum()
    return E


def count_I_resident(model):
    I = np.asarray(
        [a.infectious for a in model.schedule.agents if a.type == 'resident']).sum()
    return I


def count_I_symptomatic_resident(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'resident'and a.symptomatic_course)]).sum()
    return I

def count_V_resident(model):
    V = np.asarray([a.vaccinated for a in model.schedule.agents if
        (a.type == 'resident')]).sum()
    return V

def count_I_asymptomatic_resident(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'resident'and a.symptomatic_course == False)]).sum()
    return I


def count_R_resident(model):
    R = np.asarray(
        [a.recovered for a in model.schedule.agents if a.type == 'resident']).sum()
    return R


def count_X_resident(model):
    X = np.asarray(
        [a.quarantined for a in model.schedule.agents if a.type == 'resident']).sum()
    return X


def count_S_employee(model):
    S = np.asarray([1 for a in model.schedule.agents if a.type == 'employee' and\
                    a.exposed == False and a.recovered == False \
                    and a.infectious == False]).sum()
    return S


def count_E_employee(model):
    E = np.asarray(
        [a.exposed for a in model.schedule.agents if a.type == 'employee']).sum()
    return E


def count_I_employee(model):
    I = np.asarray(
        [a.infectious for a in model.schedule.agents if a.type == 'employee']).sum()
    return I


def count_I_symptomatic_employee(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'employee'and a.symptomatic_course)]).sum()
    return I

def count_V_employee(model):
    V = np.asarray([a.vaccinated for a in model.schedule.agents if
        (a.type == 'employee')]).sum()
    return V

def count_I_asymptomatic_employee(model):
    I = np.asarray([a.infectious for a in model.schedule.agents if
        (a.type == 'employee'and a.symptomatic_course == False)]).sum()
    return I


def count_R_employee(model):
    R = np.asarray(
        [a.recovered for a in model.schedule.agents if a.type == 'employee']).sum()
    return R


def count_X_employee(model):
    X = np.asarray(
        [a.quarantined for a in model.schedule.agents if a.type == 'employee']).sum()
    return X


def check_reactive_resident_screen(model):
    return model.screened_agents['reactive']['resident']


def check_follow_up_resident_screen(model):
    return model.screened_agents['follow_up']['resident']


def check_preventive_resident_screen(model):
    return model.screened_agents['preventive']['resident']


def check_reactive_employee_screen(model):
    return model.screened_agents['reactive']['employee']


def check_follow_up_employee_screen(model):
    return model.screened_agents['follow_up']['employee']


def check_preventive_employee_screen(model):
    return model.screened_agents['preventive']['employee']

data_collection_functions = \
    {
    'resident':
        {
        'S':count_S_resident,
        'E':count_E_resident,
        'I':count_I_resident,
        'I_asymptomatic':count_I_asymptomatic_resident,
        'V':count_V_resident,
        'I_symptomatic':count_I_symptomatic_resident,
        'R':count_R_resident,
        'X':count_X_resident
         },
    'employee':
        {
        'S':count_S_employee,
        'E':count_E_employee,
        'I':count_I_employee,
        'I_asymptomatic':count_I_asymptomatic_employee,
        'V':count_V_employee,
        'I_symptomatic':count_I_symptomatic_employee,
        'R':count_R_employee,
        'X':count_X_employee
         }
    }




class SEIRX_nursing_home(SEIRX):


    def __init__(self, G,
        verbosity = 0,
        base_transmission_risk = 0.05,
        testing='diagnostic',
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
        index_case = 'employee',
        agent_types = {
            'employee':      {'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_probability': 0},
            'resident':      {'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_probability': 0}},
        age_transmission_risk_discount = \
             {'slope':-0.02,
              'intercept':1},
        age_symptom_modification = \
             {'slope':0.00777777,
              'intercept':-0.022222},
        mask_filter_efficiency = {'exhale':0, 'inhale':0},
        transmission_risk_ventilation_modifier = 0,
        transmission_risk_vaccination_modifier = {'reception':1, 'transmission':0},
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
            seed = seed)



        # agent types that are included in preventive, background & follow-up
        # screens
        self.screening_agents = ['employee', 'resident']

        # define, whether or not a multigraph that defines separate connections
        # for every day of the week is used
        self.dynamic_connections = False


        # data collectors to save population counts and agent states every
        # time step
        model_reporters = {}
        for agent_type in self.agent_types:

            for state in ['S','E','I','I_asymptomatic','I_symptomatic','R','X', 'V']:

                model_reporters.update({'{}_{}'.format(state, agent_type):\
                    data_collection_functions[agent_type][state]})

        model_reporters.update(\
            {
            'screen_residents_reactive':check_reactive_resident_screen,
            'screen_residents_follow_up':check_follow_up_resident_screen,
            'screen_residents_preventive':check_preventive_resident_screen,
            'screen_employees_reactive':check_reactive_employee_screen,
            'screen_employees_follow_up':check_follow_up_employee_screen,
            'screen_employees_preventive':check_preventive_employee_screen,
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

    def calculate_transmission_probability(self, source, target, base_risk):
        """
        Calculates the risk of transmitting an infection between a source agent
        and a target agent given the model's and agent's properties and the base
        transmission risk.

        Transmission is an independent Bernoulli trial with a probability of
        success p. The probability of transmission without any modifications
        by for example masks or ventilation is given by the base_risk, which
        is calibrated in the model. The probability is modified by contact type
        q1 (also calibrated in the model), infection progression q2
        (from literature), reduction of the viral load due to a sublclinical
        course of the disease q3 (from literature), reduction of exhaled viral
        load of the source by mask wearing q4 (from literature), reduction of
        inhaled viral load by the target q5 (from literature), and ventilation
        of the rooms q6 (from literature).

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
        n1 = source.ID
        n2 = target.ID
        link_type = self.G.get_edge_data(n1, n2)['link_type']

        q1 = self.get_transmission_risk_contact_type_modifier(source, target)
        q2 = self.get_transmission_risk_progression_modifier(source)
        q3 = self.get_transmission_risk_subclinical_modifier(source)
        q9 = self.get_transmission_risk_vaccination_modifier_reception(target)
        q10 = self.get_transmission_risk_vaccination_modifier_transmission(source)

        # contact types where masks and ventilation are irrelevant
        if link_type in ['resident_resident_room', 'resident_resident_table']:
            p = 1 - (1 - base_risk * (1- q1) * (1 - q2) * (1 - q3) * (1 - q9) \
                * (1 - q10))

        # contact types were masks and ventilation are relevant
        elif link_type in ['resident_resident_quarters',
                           'employee_resident_care',
                           'employee_employee_short']:

            q4 = self.get_transmission_risk_exhale_modifier(source)
            q5 = self.get_transmission_risk_inhale_modifier(target)
            q6 = self.get_transmission_risk_ventilation_modifier()

            p = 1 - (1 - base_risk * (1- q1) * (1 - q2) * (1 - q3) * \
                (1 - q4) * (1 - q5) * (1 - q6) * (1 - q9) * (1 - q10))

        else:
            print('unknown link type: {}'.format(link_type))
            p = None
        return p
