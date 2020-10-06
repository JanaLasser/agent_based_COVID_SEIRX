import numpy as np
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from agent_patient import Patient

def count_E(model):
    E = np.asarray([a.exposed for a in model.schedule.agents]).sum()
    return E
def count_I(model):
    I = np.asarray([a.infected for a in model.schedule.agents]).sum()
    return I
def count_R(model):
    R = np.asarray([a.recovered for a in model.schedule.agents]).sum()
    return R


class SIR(Model):
    '''
    A model with a number of patients that reproduces the SEIR dynamics
    G: interaction graph between agents
    verbosity: verbosity level [0, 1, 2]
    '''
    def __init__(self, G, verbosity):
        IDs = list(G.nodes)
        self.num_agents = len(IDs)
        self.schedule = SimultaneousActivation(self)
        self.infection_duration = 14
        self.exposure_duration = 1
        self.G = G
        
        for ID in IDs:
            a = Patient(ID, self, verbosity)
            self.schedule.add(a)
        
        self.infection_risk = 0.01
        
        # infect initial patient
        self.schedule.agents[0].exposed = True
        
        self.datacollector = DataCollector(
            model_reporters = {'E':count_E,
                               'I':count_I,
                               'R':count_R})
        
    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()