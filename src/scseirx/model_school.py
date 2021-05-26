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


def count_S_teacher(model):
    S = np.asarray([1 for a in model.schedule.agents if a.type == 'feacher' and\
                    a.exposed == False and a.recovered == False \
                    and a.infectious == False]).sum()
    return S


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

def count_V_teacher(model):
    V = np.asarray([a.vaccinated for a in model.schedule.agents if
        (a.type == 'teacher')]).sum()
    return V

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


def count_S_family_member(model):
    S = np.asarray([1 for a in model.schedule.agents if a.type == 'family_member' and\
                    a.exposed == False and a.recovered == False \
                    and a.infectious == False]).sum()
    return S


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

def count_V_family_member(model):
    V = np.asarray([a.vaccinated for a in model.schedule.agents if
        (a.type == 'family_member')]).sum()
    return V

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
        'S':count_S_student,
        'E':count_E_student,
        'I':count_I_student,
        'I_asymptomatic':count_I_asymptomatic_student,
        'V':count_V_student,
        'I_symptomatic':count_I_symptomatic_student,
        'R':count_R_student,
        'X':count_X_student
         },
    'teacher':
        {
        'S':count_S_teacher,
        'E':count_E_teacher,
        'I':count_I_teacher,
        'I_asymptomatic':count_I_asymptomatic_teacher,
        'V':count_V_teacher,
        'I_symptomatic':count_I_symptomatic_teacher,
        'R':count_R_teacher,
        'X':count_X_teacher
         },
    'family_member':
        {
        'S':count_S_family_member,
        'E':count_E_family_member,
        'I':count_I_family_member,
        'I_asymptomatic':count_I_asymptomatic_family_member,
        'V':count_V_family_member,
        'I_symptomatic':count_I_symptomatic_family_member,
        'R':count_R_family_member,
        'X':count_X_family_member
         }
    }



class SEIRX_school(SEIRX):
    '''
    Model specific parameters:
        age_risk_discount: discount factor that lowers the transmission and
        reception risk of agents based on age for children. This is only applied
        to student agents as all other agents are assumed to be adults. This
        parameter needs to be calibrated against data.

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
        index_case = 'teacher',
        agent_types = {
            'teacher':      {'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_probability': 0},
            'student':      {'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_probability': 0},
            'family_member':{'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_probability': 0}},
        age_transmission_risk_discount = \
             {'slope':-0.02,
              'intercept':1},
        age_symptom_modification = \
             {'slope':-0.02545,
              'intercept':0.854545},
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
        self.screening_agents = ['teacher', 'student']

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
            'screen_teachers_reactive':check_reactive_teacher_screen,
            'screen_teachers_follow_up':check_follow_up_teacher_screen,
            'screen_teachers_preventive':check_preventive_teacher_screen,
            'screen_family_members_reactive':check_reactive_family_member_screen,
            'screen_family_members_follow_up':check_follow_up_family_member_screen,
            'screen_family_members_preventive':check_preventive_family_member_screen,
            'N_diagnostic_tests':get_N_diagnostic_tests,
            'N_preventive_screening_tests':get_N_preventive_screening_tests,
            'diagnostic_test_detected_infections_student':\
                    get_diagnostic_test_detected_infections_student,
            'diagnostic_test_detected_infections_teacher':\
                    get_diagnostic_test_detected_infections_teacher,
            'diagnostic_test_detected_infections_family_member':\
                    get_diagnostic_test_detected_infections_family_member,
            'preventive_test_detected_infections_student':\
                    get_preventive_test_detected_infections_student,
            'preventive_test_detected_infections_teacher':\
                    get_preventive_test_detected_infections_teacher,
            'preventive_test_detected_infections_family_member':\
                    get_preventive_test_detected_infections_family_member,
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
        n1 = source.ID
        n2 = target.ID
        tmp = [n1, n2]
        tmp.sort()
        n1, n2 = tmp
        key = n1 + n2 + 'd{}'.format(self.weekday)
        link_type = self.G.get_edge_data(n1, n2, key)['link_type']

        q1 = self.get_transmission_risk_contact_type_modifier(source, target)
        q2 = self.get_transmission_risk_age_modifier_transmission(source)
        q3 = self.get_transmission_risk_age_modifier_reception(target)
        q4 = self.get_transmission_risk_progression_modifier(source)
        q5 = self.get_transmission_risk_subclinical_modifier(source)
        q9 = self.get_transmission_risk_vaccination_modifier_reception(target)
        q10 = self.get_transmission_risk_vaccination_modifier_transmission(source)

        # contact types where masks and ventilation are irrelevant
        if link_type in ['student_household', 'teacher_household']:
            p = 1 - (1 - base_risk * (1- q1) * (1 - q2) * (1 - q3) * \
                (1 - q4) * (1 - q5) * (1 - q9)*(1-q10))

        # contact types were masks and ventilation are relevant
        elif link_type in ['student_student_intra_class',
                           'student_student_table_neighbour',
                           'student_student_daycare',
                           'teacher_teacher_short',
                           'teacher_teacher_long',
                           'teacher_teacher_team_teaching',
                           'teacher_teacher_daycare_supervision',
                           'teaching_teacher_student',
                           'daycare_supervision_teacher_student']:
            q6 = self.get_transmission_risk_exhale_modifier(source)
            q7 = self.get_transmission_risk_inhale_modifier(target)
            q8 = self.get_transmission_risk_ventilation_modifier()

            p = 1 - (1 - base_risk * (1- q1) * (1 - q2) * (1 - q3) * \
                (1 - q4) * (1 - q5) * (1 - q6) * (1 - q7) * (1 - q8) * (1 - q9)*(1-q10))

        else:
            print('unknown link type: {}'.format(link_type))
            p = None
        return p
