import numpy as np
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from agent_patient import Patient
from agent_employee import Employee
from testing_strategy import Testing

def count_E_patient(model):
    E = np.asarray([a.exposed for a in model.schedule.agents if a.type == 'patient']).sum()
    return E
def count_I_patient(model):
    I = np.asarray([a.infected for a in model.schedule.agents if a.type == 'patient']).sum()
    return I
def count_R_patient(model):
    R = np.asarray([a.recovered for a in model.schedule.agents if a.type == 'patient']).sum()
    return R
def count_E_employee(model):
    E = np.asarray([a.exposed for a in model.schedule.agents if a.type == 'employee']).sum()
    return E
def count_I_employee(model):
    I = np.asarray([a.infected for a in model.schedule.agents if a.type == 'employee']).sum()
    return I
def count_R_employee(model):
    R = np.asarray([a.recovered for a in model.schedule.agents if a.type == 'employee']).sum()
    return R
def get_state(agent):
    if agent.exposed == True: return 'exposed'
    elif agent.infected == True: return 'infected'
    elif agent.recovered == True: return 'recovered'
    else: return 'susceptible'

class SIR(Model):
    '''
    A model with a number of patients that reproduces the SEIR dynamics
    G: interaction graph between agents
    verbosity: verbosity level [0, 1, 2]
    '''
    def __init__(self, G, N_employees, verbosity):
        # durations. NOTE: all durations are inclusive, i.e. comparisons
        # are "<=" and ">="
        self.infection_duration = 14
        self.exposure_duration = 2
        self.time_until_testable = 1
        self.time_testable = 7
        self.quarantine_duration = 10
        
        # infection risk
        self.transmission_risk_patient_patient = 0.01
        self.transmission_risk_employee_patient = 0.01
        self.transmission_risk_employee_employee = 0.01
        self.transmission_risk_patient_employee = 0.01 # not used so far

        # index case probability
        self.index_probability = 0.01 # for every employee in every step

        # testing strategy
        self.testing_interval = 7
        self.testing_target = 'employee'
        self.Testing = Testing(self, self.testing_interval, self.testing_target)

        # agents and their interactions
        self.G = G
        IDs = list(G.nodes)
        self.num_agents = len(IDs) + N_employees
        self.num_patients = len(IDs)
        self.num_employees = N_employees
        self.schedule = SimultaneousActivation(self)

        for ID in IDs:
            p = Patient(ID, self, verbosity)
            self.schedule.add(p)

        for i in range(1, N_employees + 1):
            e = Employee(i, self, verbosity)
            self.schedule.add(e)
        
        # infect initial patient
        #self.schedule.agents[0].exposed = True
        
        self.datacollector = DataCollector(
            model_reporters = {'E_patient':count_E_patient,
                               'I_patient':count_I_patient,
                               'R_patient':count_R_patient},
            agent_reporters = {'state':get_state})
        
    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
        self.Testing.screen()