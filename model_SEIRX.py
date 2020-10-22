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
def check_patient_screen(model):
    return model.screened_patients
def check_employee_screen(model):
    return model.screened_employees
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
    def __init__(self, G, num_employees, verbosity=0, testing=True,
    	infection_duration=10, exposure_duration=5, time_until_testable=2,
    	time_until_symptoms=2, time_testable=10, quarantine_duration=14,
    	symptom_probability=0.4, subclinical_modifier=1,
        time_until_test_result=2, index_probability=0.01, follow_up_interval=4,
        screening_interval_patients=3, screening_interval_employees=3, 
        index_case_mode='continuous', seed=0):

        self.verbosity = verbosity
        self.testing = testing # flag to turn off the testing strategy
        self.running = True # needed for the batch runner

        assert index_case_mode in ['single', 'continuous']
        self.index_case_mode = index_case_mode
        self.Nstep = 0 # internal step counter used to launch screening tests

        ## durations
        #  NOTE: all durations are inclusive, i.e. comparison are "<=" and ">="
        self.infection_duration = infection_duration # number of days agents stay infectuous
        self.exposure_duration = exposure_duration # days after transmission until agent becomes infectuous
        self.time_until_testable = time_until_testable # days after becoming infectuous until becoming testable
        self.time_until_symptoms = time_until_symptoms # days after becoming infectuous until showing symptoms
        self.time_testable = time_testable # days after becoming infectuous while still testable
        self.quarantine_duration = quarantine_duration # duration of quarantine
        self.time_until_test_result = time_until_test_result
        
        # infection risk
        self.transmission_risk_patient_patient = 0.008 # per infected per day
        self.transmission_risk_employee_patient = 0.008 # per infected per day
        self.transmission_risk_employee_employee = 0.008 # per infected per day1
        self.transmission_risk_patient_employee = 0.008 # not used so far
        self.infection_risk_area_weights = {'room':7, 
                                            'table':3,
                                            'quarters':1}

        # index case probability
        self.index_probability = index_probability # for every employee in every step

        # symptom probability
        self.symptom_probability = symptom_probability
        # modifier for infectiosness for asymptomatic cases
        self.subclinical_modifier = subclinical_modifier

        ## agents and their interactions
        self.G = G # interaction graph of patients
        IDs = list(G.nodes)
        #IDs = [i+1 for i in range(len(G.nodes))]
        self.num_agents = len(IDs) + num_employees
        self.num_patients = len(IDs)
        self.num_employees = num_employees

        # add patient and employee agents to the scheduler
        self.schedule = SimultaneousActivation(self)
        for ID in IDs:
            p = Patient(ID, self, verbosity)
            self.schedule.add(p)

        for i in range(1, num_employees + 1):
            e = Employee(i, self, verbosity)
            self.schedule.add(e)

        # infect the first employee to introduce the disease. 
        if self.index_case_mode == 'single':
            employees = [a for a in self.schedule.agents if a.type == 'employee']
            employees[0].exposed = True
            if self.verbosity > 0:
                print('employee exposed: {}'.format(employees[0].ID))

        # flag that indicates whether a screen took place this turn in a given
        # agent group
        self.screened_patients = False
        self.screened_employees = False

        # list of agents that were tested positive this turn
        self.newly_positive_agents = []
        self.new_positive_tests = False
        self.scheduled_follow_up_screen = False

        # counter for days since the last test screen
        self.days_since_last_patient_screen = 0
        if self.index_case_mode == 'continuous':
            self.days_since_last_employee_screen = 0
        # NOTE: if we initialize this variable with 0 as well, we introduce a
        # bias since in 'single index case mode' the first index case will always
        # become exposed in step 0 and we want to realize random states of the
        # preventive scenning procedure with respect to the incidence of the
        # index case
        elif screening_interval_employees != None:
            self.days_since_last_employee_screen = \
                self.random.choice(range(0, screening_interval_employees + 1))
        else:
            self.days_since_last_employee_screen = 0

        # testing strategy
        self.Testing = Testing(self, follow_up_interval, screening_interval_patients,
                     screening_interval_employees, verbosity)
        
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
                               'screen_patients':check_patient_screen,
                               'screen_employees':check_employee_screen},
            agent_reporters = {'infection_state':get_infection_state,
                               'quarantine_state':get_quarantine_state})

    def test_agents(self, agent_group):
        untested_agents = [a for a in self.schedule.agents if \
            (a.tested == False and a.type == agent_group)]

        if len(untested_agents) > 0:
            if agent_group == 'patient': 
                self.screened_patients = True
            elif agent_group == 'employee': 
                self.screened_employees = True
            else:
                print('unknown agent group!')
            
            if self.verbosity > 1:
                print([a.ID for a in untested_agents])
            for a in untested_agents:
                a.tested = True
                if a.testable == True:
                    if self.verbosity > 0: print('{} {} sent positive sample'\
                        .format(a.type, a.ID))
                    a.sample = 'positive'
                else:
                    a.sample = 'negative'
        
    def step(self):
        if self.testing:
            # act on new test results
            if len(self.newly_positive_agents) > 0:
                if self.verbosity > 0: print('new positive test(s)')
                # send all K1 contacts of positive agents into quarantine
                # patients. NOTE: so far this is only implemented for patients
                for a in self.newly_positive_agents:
                    a.quarantined = True
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
            # (c) if there is a preventive screening policy and it is time for
            # a preventive screen in a given agent group

            # (a)
            if self.new_positive_tests == True:
                if self.verbosity > 0: print('initiating screen because of positive test(s)')
                self.test_agents('patient')
                self.screened_patients = True
                self.days_since_last_patient_screen = 0
                self.test_agents('employee')
                self.screening_employees = True
                self.days_since_last_employee_screen = 0
                
                self.scheduled_follow_up_screen = True
            # (b)
            elif self.scheduled_follow_up_screen == True \
                and self.days_since_last_patient_screen >= self.Testing.follow_up_interval:
                if self.verbosity > 0: print('initiating follow-up screen')
                self.test_agents('patient')
                self.screened_patients = True
                self.days_since_last_patient_screen = 0
                self.test_agents('employee')
                self.screened_employees = True
                self.days_since_last_employee_screen = 0
                self.scheduled_follow_up_screen = False 
            # (c) 
            elif (self.Testing.screening_interval_patients != None or\
                  self.Testing.screening_interval_employees != None):
                # preventive patient screens
                if self.Testing.screening_interval_patients != None and\
                   self.days_since_last_patient_screen >= self.Testing.screening_interval_patients:
                    if self.verbosity > 0: print('initiating preventive patient screen')
                    self.test_agents('patient')
                    self.screened_patients = True
                    self.days_since_last_patient_screen = 0
                else:
                    self.screened_patients = False
                    self.days_since_last_patient_screen += 1

                # preventive employee screens
                if self.Testing.screening_interval_employees != None and\
                   self.days_since_last_employee_screen >= self.Testing.screening_interval_employees:
                   if self.verbosity > 0: print('initiating preventive employee screen')
                   self.test_agents('employee')
                   self.screened_employees = True
                   self.days_since_last_employee_screen = 0 
                else:
                    self.screened_employees = False
                    self.days_since_last_employee_screen += 1
            else:
                self.screened_patients = False
                self.screened_employees = False
                self.days_since_last_patient_screen += 1
                self.days_since_last_employee_screen += 1


            # find symptomatic agents that have not been tested yet and are not in
            # quarantine and test them
            newly_symptomatic_agents = np.asarray([a for a in self.schedule.agents \
                if (a.symptoms == True and a.tested == False and a.quarantined == False)])
            for a in newly_symptomatic_agents:
                # all symptomatic agents are quarantined by default
                if self.verbosity > 0:
                    print('quarantined: {} {}'.format(a.type, a.ID))
                a.quarantined = True
                a.tested = True
                if a.testable:
                    if self.verbosity > 0: print('tested {} {}'.format(a.type, a.ID))
                    a.sample = 'positive'
                else:
                    a.sample = 'negative'


        self.schedule.step()
        self.datacollector.collect(self)
        self.Nstep += 1