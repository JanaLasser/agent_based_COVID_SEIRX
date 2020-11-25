import numpy as np
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

import sys
sys.path.insert(0,'school')
sys.path.insert(0, 'nursing_home')

from testing_strategy import Testing
from agent_resident import resident
from agent_employee import employee
from agent_student import student
from agent_teacher import teacher
from agent_family_member import family_member

## data collection functions ##

def get_N_diagnostic_tests(model):
    return model.number_of_diagnostic_tests


def get_N_preventive_screening_tests(model):
    return model.number_of_preventive_screening_tests


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


def check_contact_type_dict(var):
	assert type(var) == dict, 'not a dictionary'
	assert set(var.keys()).issubset({'very_far', 'far', 'intermediate', 'close'}), \
		'does not contain the correct contact types (has to be very_far, far, intermediate or close)'
	assert all((isinstance(i, int) or isinstance(i, float)) for i in var.values()), \
		'contact type weights are not numeric'

	return var


def check_K1_contact_types(var):
    for area in var:
        assert area in ['very_far', 'far', 'intermediate',
            'close'], 'K1 contact type not recognised'
    return var


def check_testing(var):
    assert var in ['diagnostic', 'background', 'preventive', False], \
        'unknown testing mode: {}'.format(var)

    return var



def check_probability(var):
	assert (type(var) == float) or (var == 0) or (var == 1), \
		 '{} not a float'.format(var)
	assert var >= 0, 'probability negative'
	assert var <= 1, 'probability larger than 1'
	return var


def check_graph(var):
    assert type(var) == nx.Graph, 'not a networkx graph'
    assert len(var.nodes) > 0, 'graph has no nodes'
    assert len(var.edges) > 0, 'graph has no edges'
    areas = [e[2]['contact_type'] for e in var.edges(data=True)]
    areas = set(areas)
    for a in areas:
        assert a in {'very_far', 'far', 'intermediate',
            'close'}, 'contact type {} not recognised'.format(a)
    return var


def check_index_case(var, agent_types):
	allowed_strings = agent_types[:]
	allowed_strings.extend(['continuous'])
	assert var in allowed_strings, 'unknown index case mode'
	return var


class SEIRX(Model):
    '''
    A model with a number of different agents that reproduces
    the SEIRX dynamics of pandemic spread in a facility. Note:
    all times are set to correspond to days

    G: networkx undirected graph, interaction graph between agents.

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

    subclinical_modifier: float, modifies the infectiousness of asymptomatic
    cases

    infection_risk_contact_type_weights: dictionary of the form
    {'very_far':float, 'far':float, 'intermediate':float, 'close':float}
    that sets transmission risk multipliers for different contact types of
    agents

    K1_contact_types: list of strings. Definition of contact types for which
    agents are considered "K1 contact persons" if they had contact to a
    positively tested person in a given area. Possible contact types are
    'very_far', 'far', 'intermediate', 'close'

    diagnostic_test_type: string, specifies the test technology and
    test result turnover time used for diagnostic testing. See module
    "Testing" for different implemented testing techologies

    preventive_screening_test_type: string, specifies the test technology and
    test result turnover time used for preventive sreening. See module
    "Testing" for different implemented testing techologies

    follow_up_testing_interval: positive integer, sets the time a follow-up
    screen is run after an initial screen triggered by a positive test result

    liberating_testing: boolean, flag that specifies, whether or not an agent
    is released from quarantine after returning a negative test result

	index_case: specifies whether agents have a continuing risk in
	every step of the simulation to become an index case ('continuous') or
	whether a single (randomly chosen) agent from a group will be the index
	case. In this case, index_case needs to be the name of the agent group from
	which the index case will be chosen

	agent_types: dictionary of the structure
		{
		agent type:
			{
			screening interval : integer, number of days between each preventive
			screen in this agent group

			index probability : float in the range [0, 1], sets the probability
			to become an index case in each time step

			transmission_risk : float in the range [0, 1], sets the probability
			to transmit an infection if in contact with a susceptible agent

			reception_risk : float in the range [0, 1], sets the probability to
			get infected if in contact with an infectious agnt

			symptom_probability : float in the range [0, 1], sets the probability
			for a symptomatic disease course
			}
		}

	The dictionary's keys are the names of the agent types which have to
	correspond to the node attributes in the contact graph. The screening
	interval sets the time-delay between preventive screens of this agent group,
	the index probability sets the probability of a member of this agent group
	becoming an index case in every time step

    seed: positive integer, fixes the seed of the simulation to enable
    repeatable simulation runs
    '''

    def __init__(self, G, verbosity, testing,
    	infection_duration, exposure_duration, time_until_symptoms,
        quarantine_duration, subclinical_modifier,
    	infection_risk_contact_type_weights,
        K1_contact_types, diagnostic_test_type,
        preventive_screening_test_type,
        follow_up_testing_interval, liberating_testing,
        index_case, agent_types, seed=None):

    	# sets the level of detail of text output to stdout (0 = no output)
        self.verbosity = check_positive_int(verbosity)
        # flag to turn off the testing & tracing strategy
        self.testing = check_testing(testing)
        self.running = True  # needed for the batch runner implemented by mesa
        # set the interaction mode to simultaneous activation
        self.schedule = SimultaneousActivation(self)

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

        self.infection_risk_area_weights = check_contact_type_dict(
            infection_risk_contact_type_weights)

        # modifier for infectiosness for asymptomatic cases
        self.subclinical_modifier = check_positive(subclinical_modifier)
        # modifiers for the infection risk, depending on contact type
        self.infection_risk_contact_type_weights = infection_risk_contact_type_weights

        # agents and their interactions
        # interaction graph of agents
        self.G = check_graph(G)
        # add weights as edge attributes so they can be visualised easily
        for e in G.edges(data=True):
            G[e[0]][e[1]]['weight'] = self.infection_risk_contact_type_weights\
            	[G[e[0]][e[1]]['contact_type']]

        # extract the different agent types from the contact graph
        self.agent_types = list(agent_types.keys())
   
        # set index case probabilities for each agent type
        self.index_probabilities = {t: check_probability(
        	agent_types[t]['index_probability']) for t in self.agent_types}
        # set transmission risks for each agent type
        self.transmission_risks = {t: check_probability(
        	agent_types[t]['transmission_risk']) for t in self.agent_types}
        # set reception risks for each agent type
        self.reception_risks = {t: check_probability(
        	agent_types[t]['reception_risk']) for t in self.agent_types}
        # set symptom probabilities for each agent type
        self.symptom_probabilities = {t: check_probability(
        	agent_types[t]['symptom_probability']) for t in self.agent_types}

        # testing strategy
        # extract the screening intervals for each agent type
        screening_intervals = {t: check_positive_int(
        	agent_types[t]['screening_interval']) for t in self.agent_types}

        self.Testing = Testing(self, diagnostic_test_type,
             preventive_screening_test_type,
             check_positive_int(follow_up_testing_interval),
             screening_intervals,
             check_bool(liberating_testing),
             check_K1_contact_types(K1_contact_types),
             verbosity)


        # specifies either continuous probability for index cases in agent
        # groups based on the 'index_probability' for each agent group, or a
        # single (randomly chosen) index case in the passed agent group
        self.index_case = check_index_case(index_case, self.agent_types)

        # dictionary of available agent classes with agent types and classes
        agent_classes = {'resident':resident, 'employee':employee,
                         'student':student, 'teacher':teacher,
                         'family_member':family_member}

        self.num_agents = {}

        # extract the agent nodes from the graph and add them to the scheduler
        for agent_type in self.agent_types:
            IDs = [x for x,y in G.nodes(data=True) if y['type'] == agent_type]
            self.num_agents.update({agent_type:len(IDs)})

            units = [self.G.nodes[ID]['unit'] for ID in IDs]
            for ID, unit in zip(IDs, units):
                a = agent_classes[agent_type](ID, unit, self, verbosity)
                self.schedule.add(a)

		# infect the first agent in single index case mode
        if self.index_case != 'continuous':
            infection_targets = [
                a for a in self.schedule.agents if a.type == index_case]
            # pick a random agent to infect in the selected agent group
            target = self.random.randint(0, len(infection_targets))
            infection_targets[target].exposed = True
            if self.verbosity > 0:
                print('{} exposed: {}'.format(index_case,
                    infection_targets[target].ID))
                

        # list of agents that were tested positive this turn
        self.newly_positive_agents = []
        # flag that indicates if there were new positive tests this turn
        self.new_positive_tests = False
        # dictionary of flags that indicate whether a given agent group has
        # been creened this turn
        self.screened_agents= {
            'reactive':{agent_type: False for agent_type in self.agent_types},
            'follow_up':{agent_type: False for agent_type in self.agent_types},
            'preventive':{agent_type: False for agent_type in self.agent_types}}


        # dictionary of counters that count the days since a given agent group
        # was screened. Initialized differently for different index case modes
        if (self.index_case == 'continuous') or \
      	   (not np.any(list(self.Testing.screening_intervals.values()))):
        	self.days_since_last_agent_screen = {agent_type: 0 for agent_type in
        	self.agent_types}
        # NOTE: if we initialize these variables with 0 in the case of a single
        # index case, we introduce a bias since in 'single index case mode' the
        # first index case will always become exposed in step 0. To realize
        # random states of the preventive sceening procedure with respect to the
        # incidence of the index case, we have to randomly pick the days since
        # the last screen for the agent group from which the index case is
        else:
        	self.days_since_last_agent_screen = {}
        	for agent_type in self.agent_types:
        		if self.Testing.screening_intervals[agent_type] != None:
        			self.days_since_last_agent_screen.update({
        				agent_type: self.random.choice(range(0,
        				 self.Testing.screening_intervals[agent_type] + 1))})
        		else:
        			self.days_since_last_agent_screen.update({agent_type: 0})

        # dictionary of flags that indicates whether a follow-up screen for a
        # given agent group is scheduled
        self.scheduled_follow_up_screen = {agent_type: False for agent_type in
        	self.agent_types}

        # counters
        self.number_of_diagnostic_tests = 0
        self.number_of_preventive_screening_tests = 0
        self.undetected_infections = 0
        self.predetected_infections = 0
        self.pending_test_infections = 0
        self.quarantine_counters = {agent_type:0 for agent_type in agent_types.keys()}

        # data collectors to save population counts and agent states every
        # time step
        self.datacollector = DataCollector(
            model_reporters=
            	{
            	'N_diagnostic_tests':get_N_diagnostic_tests,
                'N_preventive_screening_tests':get_N_preventive_screening_tests,
                'undetected_infections':get_undetected_infections,
                'predetected_infections':get_predetected_infections,
                'pending_test_infections':get_pending_test_infections
                },

            agent_reporters=
            	{
            	'infection_state': get_infection_state,
                'quarantine_state': get_quarantine_state
                })

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
                if self.verbosity > 0:
                    print('{} {} sent positive sample (even though not infectious yet)'
                    .format(a.type, a.ID))
                a.sample = 'positive'
                self.predetected_infections += 1
            else:
                if self.verbosity > 0: print('{} {} sent negative sample'
                    .format(a.type, a.ID))
                a.sample = 'negative'

        elif a.infectious:
            # tests that happen in the period of time in which the agent is
            # infectious and the infection is detectable by a given test
            if a.days_since_exposure >= self.Testing.tests[test_type]['time_until_testable'] and \
               a.days_since_exposure <= self.Testing.tests[test_type]['time_testable']:
                if self.verbosity > 0:
                    print('{} {} sent positive sample'.format(a.type, a.ID))
                a.sample = 'positive'

            # track the undetected infections to assess how important they are
            # for infection spread
            else:
                if self.verbosity > 0:
                    print('{} {} sent negative sample (even though infectious)'
                    .format(a.type, a.ID))
                a.sample = 'negative'
                self.undetected_infections += 1

        else:
            if self.verbosity > 0: print('{} {} sent negative sample'
                .format(a.type, a.ID))
            a.sample = 'negative'

        # for same-day testing, immediately act on the results of the test
        if a.days_since_tested >= self.Testing.tests[test_type]['time_until_test_result']:
            a.act_on_test_result()

    def screen_agents(self, agent_group, test_type, screen_type):
        # only test agents that have not been tested already in this simulation
        # step and that are not already known positive cases
        untested_agents = [a for a in self.schedule.agents if
            (a.tested == False and a.known_positive == False
                and a.type == agent_group)]

        if len(untested_agents) > 0:
            self.screened_agents[screen_type][agent_group] = True

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
        agents_with_test_results = [a for a in self.schedule.agents if
            (a.pending_test and
             a.days_since_tested >= self.Testing.tests[a.pending_test]['time_until_test_result'])]

        return agents_with_test_results

    def trace_contacts(self, a):
        if a.quarantined == False:
            a.quarantined = True
            if self.verbosity > 0:
                print('qurantined {} {}'.format(a.type, a.ID))

        # find all agents that share edges with the agent
        # that are classified as K1 contact types in the testing
        # strategy
        K1_contacts = [e[1] for e in self.G.edges(a.ID, data=True) if
            e[2]['contact_type'] in self.Testing.K1_contact_types]
        K1_contacts = [a for a in self.schedule.agents if a.ID in K1_contacts]

        for K1_contact in K1_contacts:
            if self.verbosity > 0:
                print('quarantined {} {} (K1 contact of {} {})'
                    .format(K1_contact.type, K1_contact.ID, a.type, a.ID))
            K1_contact.quarantined = True

    def step(self):
        if self.testing:
            if self.verbosity > 0: print('* testing and tracing *')

            # find symptomatic agents that have not been tested yet and are not
            # in quarantine and test them
            newly_symptomatic_agents = np.asarray([a for a in self.schedule.agents
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
                if self.verbosity > 0: print('new positive test(s) from {}'
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
            if (self.testing == 'background' or self.testing == 'preventive')\
               and self.new_positive_tests == True:

            	for agent_type in self.agent_types:
	                if self.verbosity > 0:
	                    print('initiating {} screen because of positive test(s)'
	                    	.format(agent_type))
	                self.screen_agents(
	                    agent_type, self.Testing.diagnostic_test_type, 'reactive')
	                self.days_since_last_agent_screen[agent_type] = 0
	                self.scheduled_follow_up_screen[agent_type] = True

            # (b)
            elif (self.testing == 'background' or self.testing == 'preventive') and \
                self.Testing.follow_up_testing_interval != None and \
                sum(list(self.scheduled_follow_up_screen.values())) > 0:

                for agent_type in self.agent_types:
                    if self.scheduled_follow_up_screen[agent_type] and\
                       self.days_since_last_agent_screen[agent_type] >=\
                       self.Testing.follow_up_testing_interval:

                        if self.verbosity > 0:
                            print('initiating {} follow-up screen'
                                .format(agent_type))
                        self.screen_agents(
                            agent_type, self.Testing.diagnostic_test_type, 'follow_up')
                        self.days_since_last_agent_screen[agent_type] = 0
                    else:
                        if self.verbosity > 0: 
                            print('not initiating {} follow-up screen (last screen too close)'\
                            	.format(agent_type))
                        self.screened_agents['follow_up'][agent_type] = False
                        self.days_since_last_agent_screen[agent_type] += 1

            # (c) 
            elif self.testing == 'preventive' and \
                np.any(list(self.Testing.screening_intervals.values())):
                for agent_type in self.agent_types:

                    if self.Testing.screening_intervals[agent_type] != None and\
                    self.days_since_last_agent_screen[agent_type] >=\
                    self.Testing.screening_intervals[agent_type]:
                        if self.verbosity > 0: 
                            print('initiating preventive {} screen'\
                                .format(agent_type))
                        self.screen_agents(agent_type,
                            self.Testing.preventive_screening_test_type, 'preventive')
                        self.days_since_last_agent_screen[agent_type] = 0
                    else:
                        self.screened_agents['preventive'][agent_type] = False
                        self.days_since_last_agent_screen[agent_type] += 1

            else:
                for agent_type in self.agent_types:
                    for screen_type in ['reactive', 'follow_up', 'preventive']:
                        self.screened_agents[screen_type][agent_type] = False
                    self.days_since_last_agent_screen[agent_type] += 1


        if self.verbosity > 0: print('* agent interaction *')
        self.datacollector.collect(self)
        self.schedule.step()
        self.Nstep += 1

