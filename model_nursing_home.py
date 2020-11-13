import numpy as np
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from model_SEIRX import SEIRX
from agent_resident import resident
from agent_employee import employee
from testing_strategy import Testing


class SEIRX_nursing_home(SEIRX):

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
                              'symptom_probability': 0.6}},
        seed=0):

        print(testing)

        super().__init__(G, verbosity, testing, infection_duration, 
            exposure_duration, time_until_symptoms, quarantine_duration,
            subclinical_modifier, infection_risk_contact_type_weights,
            K1_contact_types, diagnostic_test_type, 
            preventive_screening_test_type, follow_up_testing_interval,
            liberating_testing, index_case, agent_types, seed)


        self.agent_types.append('employee')

        # add resident agents to the scheduler
        IDs = list(self.G.nodes)
        quarters = [self.G.nodes[ID]['quarter'] for ID in IDs]
        for ID, quarter in zip(IDs, quarters):
            p = resident(ID, quarter, self, verbosity)
            self.schedule.add(p)
        self.num_residents = len(IDs)

        # add employee agents to the scheduler
        self.employees_per_quarter = check_positive_int(employees_per_quarter)
        quarters = set([n[1]['quarter'] for n in self.G.nodes(data=True)])
        i = 1
        for quarter in quarters:
            for j in range(self.employees_per_quarter):
                e = employee('e{}'.format(i), quarter, self, verbosity)
                self.schedule.add(e)
                i += 1

        self.num_agents = len(IDs) + self.employees_per_quarter * len(quarters)
        
        # data collectors to save population counts and agent states every
        # time step
        self.datacollector = DataCollector(
            model_reporters = {
                                'E_resident':self.count_E_resident,
                                'I_resident':self.count_I_resident,
                                'I_symptomatic_resident':\
                                self.count_I_symptomatic_resident,
                                'R_resident':self.count_R_resident,
                                'X_resident':self.count_X_resident,
                                'E_employee':self.count_E_employee,
                                'I_employee':self.count_I_employee,
                                'I_symptomatic_employee':\
                                self.count_I_symptomatic_employee,
                                'R_employee':self.count_R_employee,
                                'X_employee':self.count_X_employee,
                                'screen_residents':self.check_resident_screen,
                                'screen_employees':self.check_employee_screen,
                                'number_of_diagnostic_tests':\
                                self.get_number_of_diagnostic_tests,
                                'number_of_preventive_screening_tests':\
                                self.get_number_of_preventive_screening_tests,
                                'undetected_infections':\
                                self.get_undetected_infections,
                                'predetected_infections':\
                                self.get_predetected_infections,
                                'pending_test_infections':\
                                self.get_pending_test_infections},

            agent_reporters = {'infection_state':self.get_infection_state,
                               'quarantine_state':self.get_quarantine_state})

    ## additional data collection functions ##

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


    def check_resident_screen(model):
        return model.screened_residents


    def check_employee_screen(model):
        return model.screened_employees
