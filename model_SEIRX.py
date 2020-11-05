import numpy as np
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from agent_resident import resident
from agent_employee import Employee
from testing_strategy import Testing


## data collection functions ##
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


def get_number_of_diagnostic_tests(model):
    return model.number_of_diagnostic_tests


def get_number_of_preventive_screening_tests(model):
    return model.number_of_preventive_screening_tests


def check_resident_screen(model):
    return model.screened_residents


def check_employee_screen(model):
    return model.screened_employees


def get_infection_state(agent):
    if agent.exposed == True: return 'exposed'
    elif agent.infectious == True: return 'infectious'
    elif agent.recovered == True: return 'recovered'
    else: return 'susceptible'


def get_quarantine_state(agent):
    if agent.quarantined == True: return True
    else: return False


def get_undetected_infections(model):
    return model.undetected_infections


def get_predetected_infections(model):
    return model.predetected_infections


def get_pending_test_infections(model):
    return model.pending_test_infections

# parameter sanity check functions


def check_positive(var):
	assert var >= 0, 'negative number'
	return var


def check_bool(var):
	assert type(var) == bool, 'not a bool'
	return var


def check_positive_int(var):
    if var == None:
        return var
    assert type(var) == int, 'not an integer'
    assert var >= 0, 'negative number'
    return var


def check_area_dict(var):
	assert type(var) == dict, 'not a dictionary'
	assert set(var.keys()).issubset({'facility', 'room', 'table', 'quarters'}), \
		'does not contain the correct area types (has to be room, table, quarters)'
	return var

def check_K1_areas(var):
    for area in var:
        assert area in ['facility', 'quarters', 'table', 'room'], 'are not recognised'
    return var


def check_probability(var):
	assert type(var) == float, 'not a float'
	assert var >= 0, 'probability negative'
	assert var <= 1, 'probability larger than 1'
	return var


def check_graph(var):
    assert type(var) == nx.Graph, 'not a networkx graph'
    assert len(var.nodes) > 0, 'graph has no nodes'
    assert len(var.edges) > 0, 'graph has no edges'
    areas = [e[2]['area'] for e in var.edges(data=True)]
    areas = set(areas)
    for a in areas:
        assert a in {'facility', 'room', 'table', 'quarters'}, 'area not recognised'
    return var


def check_index_case_mode(var):
	assert var in ['single_employee', 'single_resident', 'continuous_employee',
	'continuous_resident', 'continuous_both'], 'unknown index case mode'
	return var


class SEIRX(Model):
    '''
    A model with a number of residents/inhabitatns and employees that reproduces
    the SEIRX dynamics of pandemic spread in a long time care facility. Note:
    all times are set to correspond to days

    G: networkx undirected graph, interaction graph between inhabitants.
    Note: the number of nodes in G also sets the number of inhabitants

    employees_per_quarter: integer, number of employees per living quarter of
    the facility

    verbosity: integer in [0, 1, 2], controls text output to std out to track
    simulation progress and transmission dynamics

    testing: bool, toggles testing/tracing activities of the facility

    infection_duration: positive integer, sets the duration of the infection
    NOTE: includes the time an agent is exposed but not yet infectious at the
    beginning of an infection

    exposure_duration: positive integer, sets the time from transmission to
    becoming infectious

    time_until_symptoms: positive integer, sets the time from transmission to
    becoming infectious and (potentially) developing symptoms

    quarantine_duration: positive integer, sets the time a positively tested
    agent is quarantined

    symptom_probability: float in the range [0, 1], sets the probability for a
    symptomatic disease course

    subclinical_modifier: float, modifies the infectiousness of asymptomatic
    cases

    infection_risk_area_weights: dictionary of the form {'room':int, 'table':int,
    'quarters':int} that sets transmission risk multipliers for different living
    areas of inhabitants

    K1_areas: list of strings. Definition of areas for which agents are 
    considered "K1 contact persons" if they had contact to a positively tested
    person in a given area. Possible areas are "quarters", "room", "table"

    time_until_test_result: positive integer, sets the time until a test result
    arrives after an agent has been tested

    follow_up_testing_interval: positive integer, sets the time a follow-up
    screen is run after an initial screen triggered by a positive test result

    screening_interval_residents: positive integer, sets the time for regular
    preventive screens of the resident population

    screening_interval_employees: positive integer, sets the time for regular
    preventive screens of the employee population

    index_case_mode: string, can be 'continuous' or 'single'. If 'continuous',
    new index cases can be introduced by employees in every simulation time step.
    If 'single', one employee is an index case (exposed) in the first time step
    of the simulation but no further index cases are introduced throughout the
    course of the simulation

    index_probability_employee: float, sets the probability an employee will
    become an index case in one simulation time step if index_case_mode is one
    of 'continuous_employee' or 'continuous_both'

    index_probability_resident: float, sets the probability an employee will
    become an index case in one simulation time step if index_case_mode is one
    of 'continuous_inhabitant' or 'continuous_both'

    seed: positive integer, fixes the seed of the simulation to enable
    repeatable simulation runs
    '''

    def __init__(self, G, employees_per_quarter, verbosity=0, testing=True,
    	infection_duration=11, exposure_duration=4, time_until_symptoms=6,
        quarantine_duration=14, symptom_probability=0.6, subclinical_modifier=1,
    	infection_risk_area_weights={'room':4,'table':2,'quarters':1,'facility':0.1},
        K1_areas=['room', 'table'], diagnostic_test_type='one_day_PCR',
        preventive_screening_test_type='one_day_PCR',
        follow_up_testing_interval=None, screening_interval_residents=None, 
        screening_interval_employees=None, liberating_testing = False,
        index_case_mode='continuous_employee',
        index_probability_employee=0.01, index_probability_resident=0.01):

    	# sets the level of detail of text output to stdout (0 = no output)
        self.verbosity = check_positive_int(verbosity)
        # flag to turn off the testing & tracing strategy
        self.testing = check_bool(testing)
        self.running = True  # needed for the batch runner implemented by mesa

        # one of two ways to introduce index cases into the system
        self.index_case_mode = check_index_case_mode(index_case_mode)
        self.Nstep = 0  # internal step counter used to launch screening tests

        # durations
        # NOTE: all durations are inclusive, i.e. comparison are "<=" and ">="
        # number of days agents stay infectuous
        self.infection_duration = check_positive_int(infection_duration)
        # days after transmission until agent becomes infectuous
        self.exposure_duration = check_positive_int(exposure_duration)
        # days after becoming infectuous until showing symptoms
        self.time_until_symptoms = check_positive_int(time_until_symptoms)
        # duration of quarantine
        self.quarantine_duration = check_positive_int(quarantine_duration)

        # infection risk
        self.transmission_risk_resident_resident = 0.01  # per infected per day
        self.transmission_risk_employee_resident = 0.01  # per infected per day
        self.transmission_risk_employee_employee = 0.01  # per infected per day
        self.transmission_risk_resident_employee = 0.01  # per infected per day
        self.infection_risk_area_weights = check_area_dict(
            infection_risk_area_weights)

        # index case probability for every employee in every step
        self.index_probability_employee = check_probability(
            index_probability_employee)
        self.index_probability_resident = check_probability(
            index_probability_resident)

        # symptom probability
        self.symptom_probability = check_probability(symptom_probability)
        # modifier for infectiosness for asymptomatic cases
        self.subclinical_modifier = check_positive(subclinical_modifier)

        ## agents and their interactions
        # interaction graph of residents
        self.G = check_graph(G)  
        # add weights as edge attributes so they can be visualised easily
        for e in G.edges(data=True):
            G[e[0]][e[1]]['weight'] = self.infection_risk_area_weights[G[e[0]][e[1]]['area']]

        # add resident agents to the scheduler
        IDs = list(self.G.nodes)
        quarters = [self.G.nodes[ID]['quarter'] for ID in IDs]
        self.schedule = SimultaneousActivation(self)
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
                e = Employee('e{}'.format(i), quarter, self, verbosity)
                self.schedule.add(e)
                i += 1

        self.num_agents = len(IDs) + self.employees_per_quarter * len(quarters)


        # infect the first employee to introduce the disease.
        if self.index_case_mode == 'single_employee':
            employees = [
                a for a in self.schedule.agents if a.type == 'employee']
            employees[0].exposed = True
            if self.verbosity > 0:
                print('employee exposed: {}'.format(employees[0].ID))

        # infect the first inhabitant to introduce the disease.
        if self.index_case_mode == 'single_resident':
            residents = [a for a in self.schedule.agents if a.type == 'resident']
            residents[0].exposed = True
            if self.verbosity > 0:
                print('resident exposed: {}'.format(residents[0].ID))

        # flag that indicates whether a screen took place this turn in a given
        # agent group
        self.screened_residents = False
        self.screened_employees = False

        # list of agents that were tested positive this turn
        self.newly_positive_agents = []
        self.new_positive_tests = False
        self.scheduled_follow_up_screen_resident = False
        self.scheduled_follow_up_screen_employee = False

        # counters
        self.number_of_diagnostic_tests = 0
        self.number_of_preventive_screening_tests = 0
        self.undetected_infections = 0
        self.predetected_infections = 0
        self.pending_test_infections = 0

        # counter for days since the last test screen
        # NOTE: if we initialize these variables with 0 in the case of a single
        # index case for either employees or inhabitants, we introduce a
        # bias since in 'single index case mode' the first index case will always
        # become exposed in step 0. To realize random states of the preventive
        # scenning procedure with respect to the incidence of the index case, we
        # have to randomly pick the "days_since_last_X_screen" as well

        if self.index_case_mode == 'single_employee' and \
        	screening_interval_employees != None:
            self.days_since_last_resident_screen = 0
            self.days_since_last_employee_screen = \
                self.random.choice(range(0, screening_interval_employees + 1))

        elif self.index_case_mode == 'single_resident' and \
        	screening_interval_residents != None:
        	self.days_since_last_employee_screen = 0
        	self.days_since_last_resident_screen = \
                self.random.choice(range(0, screening_interval_residents + 1))

        else:
            self.days_since_last_employee_screen = 0
            self.days_since_last_resident_screen = 0

        # testing strategy
        self.Testing = Testing(self, diagnostic_test_type,
             preventive_screening_test_type,
             check_positive_int(follow_up_testing_interval),
             check_positive_int(screening_interval_residents),
             check_positive_int(screening_interval_employees),
             check_bool(liberating_testing),
             check_K1_areas(K1_areas),
             verbosity)
        
        # data collectors to save population counts and resident / employee
        # states every time step
        self.datacollector = DataCollector(
            model_reporters = {'E_resident':count_E_resident,
                               'I_resident':count_I_resident,
                               'I_symptomatic_resident':count_I_symptomatic_resident,
                               'R_resident':count_R_resident,
                               'X_resident':count_X_resident,
                               'E_employee':count_E_employee,
                               'I_employee':count_I_employee,
                               'I_symptomatic_employee':count_I_symptomatic_employee,
                               'R_employee':count_R_employee,
                               'X_employee':count_X_employee,
                               'screen_residents':check_resident_screen,
                               'screen_employees':check_employee_screen,
                               'number_of_diagnostic_tests':get_number_of_diagnostic_tests,
                               'number_of_preventive_screening_tests':get_number_of_preventive_screening_tests,
                               'undetected_infections':get_undetected_infections,
                               'predetected_infections':get_predetected_infections,
                               'pending_test_infections':get_pending_test_infections},

            agent_reporters = {'infection_state':get_infection_state,
                               'quarantine_state':get_quarantine_state})


    def test_agent(self, a, test_type):
        a.tested = True
        a.pending_test = test_type
        if test_type == self.Testing.diagnostic_test_type:
            self.number_of_diagnostic_tests += 1
        else:
            self.number_of_preventive_screening_tests += 1


        if a.exposed:
            # tests that happen in the period of time in which the agent is
            # exposed but not yet infectious
            if a.days_since_exposure >= self.Testing.tests[test_type]['time_until_testable']:
                if self.verbosity > 0: print('{} {} sent positive sample (even though not infectious yet)'\
                    .format(a.type, a.ID))
                a.sample = 'positive'
                self.predetected_infections += 1
            else:
                if self.verbosity > 0: print('{} {} sent negative sample'\
                    .format(a.type, a.ID))
                a.sample = 'negative'

        elif a.infectious:
            # tests that happen in the period of time in which the agent is
            # infectious and the infection is detectable by a given test
            if a.days_since_exposure >= self.Testing.tests[test_type]['time_until_testable'] and \
               a.days_since_exposure <= self.Testing.tests[test_type]['time_testable']:
                if self.verbosity > 0: print('{} {} sent positive sample'\
                    .format(a.type, a.ID))
                a.sample = 'positive'
            else:
                if self.verbosity > 0: print('{} {} sent negative sample (even though infectious)'\
                    .format(a.type, a.ID))
                a.sample = 'negative'
                self.undetected_infections += 1

        else:
            if self.verbosity > 0: print('{} {} sent negative sample'\
                .format(a.type, a.ID))
            a.sample = 'negative'

        # for same-day testing, immediately act on the results of the test
        if a.days_since_tested >= self.Testing.tests[test_type]['time_until_test_result']:
            a.act_on_test_result()



    def screen_agents(self, agent_group, test_type):
        # only test agents that have not been tested already in this simulation
        # step and that are not already known positive cases
        untested_agents = [a for a in self.schedule.agents if \
            (a.tested == False and a.known_positive == False \
                and a.type == agent_group)]

        if len(untested_agents) > 0:
            if agent_group == 'resident': 
                self.screened_residents = True
            elif agent_group == 'employee': 
                self.screened_employees = True
            else:
                print('unknown agent group!')

            for a in untested_agents:
                self.test_agent(a, test_type)                

            if self.verbosity > 0:
                print()
        else:
            if self.verbosity > 0:
                print('no agents tested because all agents have already been tested')


    # the type of the test used in the pending test result is stored in the 
    # variable pending_test
    def collect_test_results(self):
        agents_with_test_results = [a for a in self.schedule.agents if \
            (a.pending_test and \
             a.days_since_tested >= self.Testing.tests[a.pending_test]['time_until_test_result'])]

        return agents_with_test_results


    def trace_contacts(self, a):
        if a.quarantined == False:
            a.quarantined = True
            if self.verbosity > 0:
                print('qurantined {} {}'.format(a.type, a.ID))

        if a.type == 'resident':
            # find all residents that share edges with the given resident
            # that are classified as K1 contact areas in the testing
            # strategy
            K1_contacts = [e[1] for e in self.G.edges(a.ID, data=True) if \
                e[2]['area'] in self.Testing.K1_areas]
            K1_contacts = [a for a in self.schedule.agents if \
                (a.type == 'resident' and a.ID in K1_contacts)]
            for K1_contact in K1_contacts:
                if self.verbosity > 0:
                    print('quarantined {} {} (K1 contact of {} {})'\
                        .format(K1_contact.type, K1_contact.ID, a.type, a.ID))
                K1_contact.quarantined = True

        if a.type == 'employee' and 'quarters' in self.Testing.K1_areas:
            # find all employees that work in the same quarters as 
            # the infected employee and send them to quarantine
            quarter = a.quarter
            K1_contacts = [e for e in self.schedule.agents if e.quarter == quarter]
            for K1_contact in K1_contacts:
                if self.verbosity > 0:
                    print('quarantined {} {} (K1 contact of {} {})'\
                        .format(K1_contact.type, K1_contact.ID, a.type, a.ID))
                K1_contact.quarantined = True

        
    def step(self):
        if self.testing:
            if self.verbosity > 0: print('* testing and tracing *')

            # find symptomatic agents that have not been tested yet and are not 
            # in quarantine and test them
            newly_symptomatic_agents = np.asarray([a for a in self.schedule.agents \
                if (a.symptoms == True and a.tested == False and a.quarantined == False)])

            for a in newly_symptomatic_agents:
                # all symptomatic agents are quarantined by default
                if self.verbosity > 0:
                    print('quarantined: {} {}'.format(a.type, a.ID))
                a.quarantined = True
                self.test_agent(a, self.Testing.diagnostic_test_type)

            # collect and act on new test results
            agents_with_test_results = self.collect_test_results()
            for a in agents_with_test_results:
                a.act_on_test_result()

            # trace and quarantine contacts of newly positive agents
            if len(self.newly_positive_agents) > 0:
                if self.verbosity > 0: print('new positive test(s) from {}'\
                    .format([a.ID for a in self.newly_positive_agents]))
                
                # send all K1 contacts of positive agents into quarantine
                for a in self.newly_positive_agents:
                    self.trace_contacts(a)

                # indicate that a screen should happen because there are new
                # positive test results
                self.new_positive_tests = True
                self.newly_positive_agents = []

            else:
                self.new_positive_tests = False

            # screening:
            # a screen should take place if
            # (a) there are new positive test results
            # (b) as a follow-up screen for a screen that was initiated because
            # of new positive cases
            # (c) if there is a preventive screening policy and it is time for
            # a preventive screen in a given agent group

            # (a)
            if self.new_positive_tests == True:

                #if self.Testing.follow_up_testing_interval != None:
                #    if self.days_since_last_resident_screen >= self.Testing.follow_up_testing_interval:
                #        if self.verbosity > 0: 
                #            print('initiating resident screen because of positive test(s)')
                #        self.screen_agents('resident')
                #        self.screened_residents = True
                #        self.days_since_last_resident_screen = 0
                #        self.scheduled_follow_up_screen_resident = True
                #    else:
                #        if self.verbosity > 0: 
                #            print('not initiating resident screen because of positive test(s) (last screen too close)')
                #        self.screened_residents = False
                #        self.days_since_last_resident_screen += 1

                if self.verbosity > 0: 
                    print('initiating resident screen because of positive test(s)')
                self.screen_agents('resident', self.Testing.diagnostic_test_type)
                self.screened_residents = True
                self.days_since_last_resident_screen = 0
                self.scheduled_follow_up_screen_resident = True


                #if self.Testing.follow_up_testing_interval != None:
                #    if self.days_since_last_employee_screen >= self.Testing.follow_up_testing_interval:
                #        if self.verbosity > 0: 
                #            print('initiating employee screen because of positive test(s)')
                #        self.screen_agents('employee')
                #        self.screened_employees = True
                #        self.days_since_last_employee_screen = 0
                #        self.scheduled_follow_up_screen_employee = True
                #    else:
                #        if self.verbosity > 0: 
                #            print('not initiating employee screen because of positive test(s) (last screen too close)')
                #        self.screened_employees = False
                #        self.days_since_last_employee_screen += 1

                if self.verbosity > 0: 
                    print('initiating employee screen because of positive test(s)')
                self.screen_agents('employee', self.Testing.diagnostic_test_type)
                self.screened_employees = True
                self.days_since_last_employee_screen = 0
                self.scheduled_follow_up_screen_employee = True
                
            # (b)
            elif self.Testing.follow_up_testing_interval != None:
                if self.scheduled_follow_up_screen_resident or self.scheduled_follow_up_screen_employee:

                    if self.scheduled_follow_up_screen_resident and \
                       self.days_since_last_resident_screen >= self.Testing.follow_up_testing_interval:
                        if self.verbosity > 0: print('initiating resident follow-up screen')
                        self.screen_agents('resident', self.Testing.diagnostic_test_type)
                        self.screened_residents = True
                        self.days_since_last_resident_screen = 0
                    else:
                        if self.verbosity > 0: 
                            print('not initiating resident follow-up screen (last screen too close)')
                        self.screened_residents = False
                        self.days_since_last_resident_screen += 1

                    if self.scheduled_follow_up_screen_employee and \
                       self.days_since_last_employee_screen >= self.Testing.follow_up_testing_interval:
                        if self.verbosity > 0: print('initiating employee follow-up screen')
                        self.screen_agents('employee', self.Testing.diagnostic_test_type)
                        self.screened_employees = True
                        self.days_since_last_employee_screen = 0
                        self.scheduled_follow_up_screen = False 
                    else:
                        if self.verbosity > 0: 
                            print('not initiating employee follow-up screen (last screen too close)')
                        self.screened_employees = False
                        self.days_since_last_employee_screen += 1

            # (c) 
            elif (self.Testing.screening_interval_residents != None or\
                  self.Testing.screening_interval_employees != None):

                # preventive resident screens
                if self.Testing.screening_interval_residents != None and\
                   self.days_since_last_resident_screen >= self.Testing.screening_interval_residents:
                    if self.verbosity > 0: print('initiating preventive resident screen')
                    self.screen_agents('resident', self.Testing.preventive_screening_test_type)
                    self.screened_residents = True
                    self.days_since_last_resident_screen = 0
                else:
                    self.screened_residents = False
                    self.days_since_last_resident_screen += 1

                # preventive employee screens
                if self.Testing.screening_interval_employees != None and\
                   self.days_since_last_employee_screen >= self.Testing.screening_interval_employees:
                   if self.verbosity > 0: print('initiating preventive employee screen')
                   self.screen_agents('employee', self.Testing.preventive_screening_test_type)
                   self.screened_employees = True
                   self.days_since_last_employee_screen = 0 
                else:
                    self.screened_employees = False
                    self.days_since_last_employee_screen += 1
            else:
                self.screened_residents = False
                self.screened_employees = False
                self.days_since_last_resident_screen += 1
                self.days_since_last_employee_screen += 1


        if self.verbosity > 0: print('* agent interaction *')
        self.datacollector.collect(self)
        self.schedule.step()
        self.Nstep += 1
