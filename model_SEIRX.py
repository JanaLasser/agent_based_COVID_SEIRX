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
def count_I_symptomatic_patient(model):
    I = np.asarray([a.infected for a in model.schedule.agents if \
        (a.type == 'patient'and a.symptomatic_course)]).sum()
    return I
def count_I_asymptomatic_patient(model):
    I = np.asarray([a.infected for a in model.schedule.agents if \
        (a.type == 'patient'and a.symptomatic_course == False)]).sum()
    return I
def count_R_patient(model):
    R = np.asarray([a.recovered for a in model.schedule.agents if a.type == 'patient']).sum()
    return R
def count_X_patient(model):
    X = np.asarray([a.quarantined for a in model.schedule.agents if a.type == 'patient']).sum()
    return X
def count_T_patient(model):
    T = np.asarray([a.testable for a in model.schedule.agents if a.type == 'patient']).sum()
    return T
def count_E_employee(model):
    E = np.asarray([a.exposed for a in model.schedule.agents if a.type == 'employee']).sum()
    return E
def count_I_employee(model):
    I = np.asarray([a.infected for a in model.schedule.agents if a.type == 'employee']).sum()
    return I
def count_I_symptomatic_employee(model):
    I = np.asarray([a.infected for a in model.schedule.agents if \
        (a.type == 'employee'and a.symptomatic_course)]).sum()
    return I
def count_I_asymptomatic_employee(model):
    I = np.asarray([a.infected for a in model.schedule.agents if \
        (a.type == 'employee'and a.symptomatic_course == False)]).sum()
    return I
def count_R_employee(model):
    R = np.asarray([a.recovered for a in model.schedule.agents if a.type == 'employee']).sum()
    return R
def count_X_employee(model):
    X = np.asarray([a.quarantined for a in model.schedule.agents if a.type == 'employee']).sum()
    return X
def count_T_employee(model):
    T = np.asarray([a.testable for a in model.schedule.agents if a.type == 'employee']).sum()
    return T
def check_screen(model):
    return model.screened
def get_infection_state(agent):
    if agent.exposed == True: return 'exposed'
    elif agent.infected == True: return 'infected'
    elif agent.recovered == True: return 'recovered'
    else: return 'susceptible'
def get_quarantine_state(agent):
    if agent.quarantined == True: return True
    else: return False

class SIR(Model):
    '''
    A model with a number of patients that reproduces the SEIR dynamics
    G: interaction graph between agents
    verbosity: verbosity level [0, 1, 2]
    '''
    def __init__(self, G, N_employees, verbosity, seed):
        self.verbosity = verbosity
        self.Nstep = 0 # internal step counter used to launch screening tests

        ## durations
        #  NOTE: all durations are inclusive, i.e. comparison are "<=" and ">="
        self.infection_duration = 12 # number of days agents stay infectuous
        self.exposure_duration = 5 # days after transmission until agent becomes infectuous
        self.time_until_testable = 2 # days after becoming infectuous until becoming testable
        self.time_until_symptoms = 2 # days after becoming infectuous until showing symptoms
        self.time_testable = 10 # days after becoming infectuous while still testable
        self.quarantine_duration = 10 # duration of quarantine
        self.time_until_test_result = 2
        
        # infection risk
        self.transmission_risk_patient_patient = 0.0005 # per infected per day
        self.transmission_risk_employee_patient = 0.005 # per infected per day
        self.transmission_risk_employee_employee = 0.005 # per infected per day1
        self.transmission_risk_patient_employee = 0.005 # not used so far

        # index case probability
        self.index_probability = 0.001 # for every employee in every step

        # symptom probability
        self.symptom_probability = 0.5

        # testing strategy
        self.testing_interval = 3 # days
        self.Testing = Testing(self, self.testing_interval,
                     self.verbosity)

        ## agents and their interactions
        self.G = G # interaction graph of patients
        IDs = list(G.nodes)
        #IDs = [i+1 for i in range(len(G.nodes))]
        self.num_agents = len(IDs) + N_employees
        self.num_patients = len(IDs)
        self.num_employees = N_employees

        # add patient and employee agents to the scheduler
        self.schedule = SimultaneousActivation(self)
        for ID in IDs:
            p = Patient(ID, self, verbosity)
            self.schedule.add(p)

        for i in range(1, N_employees + 1):
            e = Employee(i, self, verbosity)
            self.schedule.add(e)

        # flag that indicates whether a screen took place this turn
        self.screened = False

        # list of agents that were tested positive this turn
        self.newly_positive_agents = []
        self.new_positive_tests = False
        self.scheduled_follow_up_screen = False

        # counter for days since the last test screen
        self.days_since_last_screen = None
        
        # data collectors to save population counts and patient / employee
        # states every time step
        self.datacollector = DataCollector(
            model_reporters = {'E_patient':count_E_patient,
                               'I_patient':count_I_patient,
                               'I_symptomatic_patient':count_I_symptomatic_patient,
                               'R_patient':count_R_patient,
                               'X_patient':count_X_patient,
                               'T_patient':count_T_patient,
                               'E_employee':count_E_employee,
                               'I_employee':count_I_employee,
                               'I_symptomatic_employee':count_I_symptomatic_employee,
                               'R_employee':count_R_employee,
                               'X_employee':count_X_employee,
                               'T_employee':count_T_employee,
                               'screen':check_screen},
            agent_reporters = {'infection_state':get_infection_state,
                               'quarantine_state':get_quarantine_state})

    def test_agents(self):
        untested_agents = [a for a in self.schedule.agents if a.tested == False]
        if len(untested_agents) > 0:
            self.screen = True
            for a in self.schedule.agents:
                if a.tested == False:
                    a.tested = True
                    if a.testable == True:
                        if self.verbosity > 0: print('{} {} sent positive sample'.format(a.type, a.ID))
                        a.sample = 'positive'
                    else:
                        a.sample = 'negative'
        
    def step(self):
        self.schedule.step()
        # act on new test results
        if len(self.newly_positive_agents) > 0:
            if self.verbosity > 0: print('new positive test')
            # send all K1 contacts of positive agents into quarantine
            # patients. NOTE: so far this is only implemented for patients
            for a in self.newly_positive_agents:
                if a.type == 'patient':
                    # find all agents that share edges with the given agent
                    # that are classified as K1 contact areas in the testing
                    # strategy
                    K1_contacts = [e[1] for e in self.G.edges(a.ID, data=True) if \
                        e[2]['area'] in self.Testing.K1_areas]
                    K1_contacts = [a for a in self.schedule.agents if \
                        (a.type == 'patient' and a.ID in K1_contacts)]
                    for K1_contact in K1_contacts:
                        if self.verbosity > 0:
                            print('quarantine {} {}'.format(K1_contact.type, K1_contact.ID))
                        K1_contact.quarantined = True

            # indicate that a screen should happen
            self.new_positive_tests = True
            self.newly_positive_agents = []
        else:
            self.new_positive_tests = False

        ## screening:
        # a screen should take place if
        # (a) there are newly positive cases and the last screen was more than 
        # Testing.interval steps ago or
        # (b) as a follow-up screen for a screen that was initiated becuase of
        # new positive cases
        if (self.days_since_last_screen == None or \
            self.days_since_last_screen >= self.Testing.interval):
            # (a)
            if self.new_positive_tests == True:
                if self.verbosity > 0: print('initiating screen because of positive test(s)')
                self.test_agents()
                self.screened = True
                self.days_since_last_screen = 0
                self.scheduled_follow_up_screen = True
            # (b)
            elif self.scheduled_follow_up_screen == True:
                if self.verbosity > 0: print('initiating follow-up screen')
                self.test_agents()
                self.screened = True
                self.days_since_last_screen = 0
                self.scheduled_follow_up_screen = False 
        else:
            self.screened = False
            if self.days_since_last_screen != None:
                self.days_since_last_screen += 1


        # find symptomatic agents that have not been tested yet and are not in
        # quarantine and test them
        newly_symptomatic_agents = np.asarray([a for a in self.schedule.agents \
            if (a.symptoms == True and a.tested == False and a.quarantined == False)])
        for a in newly_symptomatic_agents:
            # all symptomatic agents are quarantined by default
            a.quarantined = True
            a.tested = True
            if a.testable:
                if self.verbosity > 0: print('tested {} {}'.format(a.type, a.ID))
                a.sample = 'positive'
            else:
                a.sample = 'negative'

        # launches an employee screen every testing_interval step
        #if self.Nstep % self.testing_interval == 0:
        #    cases = self.Testing.screen('employee')
            # if infected employees are detected, an patient screen is launched
        #    if cases > 0:
        #        _ = self.Testing.screen('patient')
        self.datacollector.collect(self)
        self.Nstep += 1