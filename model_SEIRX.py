import numpy as np
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from agent_patient import Patient
from agent_employee import Employee
from testing_strategy import Testing

# NOTE: "patients" and "inhabitants" are used interchangeably in the documentation


## data collection functions ##
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

## parameter sanity check functions
def test_positive(var):
	assert var >= 0, 'negative number'
	return var
def test_bool(var):
	assert type(var) == bool, 'not a bool'
	return var
def test_positive_int(var):
	assert type(var) == int, 'not an integer'
	assert var >= 0, 'negative number'
	return var
def test_area_dict(var):
	assert type(var) == dict, 'not a dictionary'
	assert set(var.keys()) == {'room', 'table', 'quarters'}, \
		'does not contain the correct area types (has to be room, table, quarters)'
	return var
def test_probability(var):
	assert type(var) == float, 'not a float'
	assert var >= 0, 'probability negative'
	assert var <= 1, 'probability larger than 1'
	return var
def test_graph(var):
	assert type(var) == nx.Graph, 'not a networkx graph'
	assert len(var.nodes) > 0, 'graph has no nodes'
	assert len(var.edges) > 0, 'graph has no edges'
	nested_list = [list(e[2].values()) for e in var.edges(data=True)]
	areas = set([item for sublist in nested_list for item in sublist])
	for a in areas:
		assert a in {'room', 'table', 'quarters'}, 'area not recognised'
	return var
def test_index_case_mode(var):
	assert var in ['single', 'continuous'], 'inknown index case mode'
	return var

class SIR(Model):
    '''
    A model with a number of patients/inhabitatns and employees that reproduces 
    the SEIRX dynamics of pandemic spread in a long time care facility. Note: 
    all times are set to correspond to days

    G: networkx undirected graph, interaction graph between inhabitants. 
    Note: the number of nodes in G also sets the number of inhabitants
    num_employees: integer, number of employees
    verbosity: integer in [0, 1, 2], controls text output to std out to track
    simulation progress and transmission dynamics
    testing: bool, toggles testing/tracing activities of the facility
    infection_duration: positive integer, sets the time an infected agent stays
    infectious
    exposure_duration: positive integer, sets the time from transmission to 
    becoming infectious
	time_until_testable: positive integer, sets the time between becoming 
	infectious and being testable, i.e. returning a positive result upon testing
    time_until_symptoms: positive integer, sets the time between becoming 
    infectious and (potentially) developing symptoms
    time_testable: positive integer, sets the time after becoming infectious
    during which an agent is testable
    quarantine_duration: positive integer, sets the time a positively tested
    agent is quarantined
    symptom_probability: float in the range [0, 1], sets the probability for a
    symptomatic disease course
    subclinical_modifier: float, modifies the infectiousness of asymptomatic
    cases
    infection_risk_area_weights: dictionary of the form {'room':int, 'table':int,
    'quarters':int} that sets transmission risk multipliers for different living
    areas of inhabitants
    time_until_test_result: positive integer, sets the time until a test result
    arrives after an agent has been tested
    follow_up_testing_interval: positive integer, sets the time a follow-up
    screen is run after an initial screen triggered by a positive test result
    screening_interval_patients: positive integer, sets the time for regular
    preventive screens of the patient population
    screening_interval_employees: positive integer, sets the time for regular
    preventive screens of the employee population
    index_case_mode: string, can be 'continuous' or 'single'. If 'continuous', 
    new index cases can be introduced by employees in every simulation time step.
    If 'single', one employee is an index case (exposed) in the first time step
    of the simulation but no further index cases are introduced throughout the
    course of the simulation
    index_probability: float, sets the probability an employee will become an
    index case in one simulation time step if index_case_mode = 'continuous'
    seed: positive integer, fixes the seed of the simulation to enable 
    repeatable simulation runs
    '''
    def __init__(self, G, num_employees, verbosity=0, testing=True,
    	infection_duration=10, exposure_duration=5, time_until_testable=2,
    	time_until_symptoms=2, time_testable=10, quarantine_duration=14,
    	symptom_probability=0.6, subclinical_modifier=1,
    	infection_risk_area_weights={'room':7, 'table':3, 'quarters':1},
        time_until_test_result=2, follow_up_testing_interval=4,
        screening_interval_patients=3, screening_interval_employees=3, 
        index_case_mode='continuous', index_probability=0.01, seed=0):

    	# sets the level of detail of text output to stdout (0 = no output)
        self.verbosity = test_positive_int(verbosity)
        # flag to turn off the testing & tracing strategy
        self.testing = test_bool(testing) 
        self.running = True # needed for the batch runner implemented by mesa

        # one of two ways to introduce index cases into the system
        self.index_case_mode = test_index_case_mode(index_case_mode)
        self.Nstep = 0 # internal step counter used to launch screening tests

        ## durations
        #  NOTE: all durations are inclusive, i.e. comparison are "<=" and ">="
        # number of days agents stay infectuous
        self.infection_duration = test_positive_int(infection_duration) 
        # days after transmission until agent becomes infectuous
        self.exposure_duration = test_positive_int(exposure_duration) 
        # days after becoming infectuous until becoming testable
        self.time_until_testable = test_positive_int(time_until_testable) 
        # days after becoming infectuous until showing symptoms
        self.time_until_symptoms = test_positive_int(time_until_symptoms) 
        # days after becoming infectuous while still testable
        self.time_testable = test_positive_int(time_testable) 
        # duration of quarantine
        self.quarantine_duration = test_positive_int(quarantine_duration) 
        # time until a result returns from a test
        self.time_until_test_result = test_positive_int(time_until_test_result)
        
        # infection risk
        self.transmission_risk_patient_patient = 0.008 # per infected per day
        self.transmission_risk_employee_patient = 0.008 # per infected per day
        self.transmission_risk_employee_employee = 0.008 # per infected per day1
        self.transmission_risk_patient_employee = 0.008 # per infected per day
        self.infection_risk_area_weights = test_area_dict(infection_risk_area_weights)

        # index case probability for every employee in every step
        self.index_probability = test_probability(index_probability) 

        # symptom probability
        self.symptom_probability = test_probability(symptom_probability)
        # modifier for infectiosness for asymptomatic cases
        self.subclinical_modifier = test_positive(subclinical_modifier)

        ## agents and their interactions
        self.G = test_graph(G) # interaction graph of patients
        IDs = list(G.nodes)
        self.num_employees = test_positive_int(num_employees)
        self.num_agents = len(IDs) + self.num_employees
        self.num_patients = len(IDs)
        

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
        self.Testing = Testing(self, follow_up_testing_interval, screening_interval_patients,
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
                and self.days_since_last_patient_screen >= self.Testing.follow_up_testing_interval:
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