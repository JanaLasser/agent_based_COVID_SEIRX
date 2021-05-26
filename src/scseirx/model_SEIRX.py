import numpy as np
import networkx as nx
from math import gamma
from scipy.optimize import root_scalar

from mesa import Model
from mesa.time import RandomActivation, SimultaneousActivation
from mesa.datacollection import DataCollector

from scseirx.testing_strategy import Testing

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


def get_diagnostic_test_detected_infections_student(model):
    return model.positive_tests[model.Testing.diagnostic_test_type]['student']


def get_diagnostic_test_detected_infections_teacher(model):
    return model.positive_tests[model.Testing.diagnostic_test_type]['teacher']


def get_diagnostic_test_detected_infections_family_member(model):
    return model.positive_tests[model.Testing.diagnostic_test_type]\
        ['family_member']


def get_preventive_test_detected_infections_student(model):
    return model.positive_tests[model.Testing.preventive_screening_test_type]\
        ['student']


def get_preventive_test_detected_infections_teacher(model):
    return model.positive_tests[model.Testing.preventive_screening_test_type]\
        ['teacher']


def get_preventive_test_detected_infections_family_member(model):
    return model.positive_tests[model.Testing.preventive_screening_test_type]\
        ['family_member']


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
    assert var in ['diagnostic', 'background', 'preventive',
                   'background+preventive', False], \
        'unknown testing mode: {}'.format(var)

    return var



def check_probability(var):
	assert (type(var) == float) or (var == 0) or (var == 1), \
		 '{} not a float'.format(var)
	assert var >= 0, 'probability negative'
	assert var <= 1, 'probability larger than 1'
	return var


def check_graph(var):
    assert type(var) in [nx.Graph, nx.MultiGraph], 'not a networkx graph'
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


def check_discount(var):
    if var['slope'] != None:
        assert var['slope'] <= 0, 'slope needs to be <= 0 or None'
        assert np.abs(var['slope']) <= 1, 'absolute value of slope needs to be <= 1'
    assert var['intercept'], 'intercept needs to be positive'
    assert var['intercept'], 'intercept needs to be <= 1'
    return var


def get_weibull_shape(k, mu, var):
    '''
    Calculates the shape parameter of a Weibull distribution, given its mean
    mu and its variance var
    '''
    return var / mu**2 - gamma(1 + 2/k) / gamma(1+1/k)**2 + 1



def get_weibull_scale(mu, k):
    '''
    Calculates the scale parameter of a Weibull distribution, given its mean
    mu and its shape parameter k
    '''
    return mu / gamma(1 + 1/k)


def weibull_two_param(shape, scale):
    '''
    A two-parameter Weibull distribution, based on numpy ramdon's single
    parameter distribution. We use this distribution in the simulation to draw
    random epidemiological parameters for agents from the given distribution
    See https://numpy.org/doc/stable/reference/random/generated/numpy.random.weibull.html
    '''
    return scale * np.random.weibull(shape)


class SEIRX(Model):
    '''
    A model with a number of different agents that reproduces
    the SEIRX dynamics of pandemic spread in a facility. Note:
    all times are set to correspond to days

    G: networkx undirected graph, interaction graph between agents. Edges have
    to have edge the edge attribute 'contact_type' specifying the closeness of
    contacts, which can be ['very far', 'far', 'intermediate' and 'close'].
    Nodes have to have the node attribute 'type' which specifies the agent type
    of the given node (for example 'student' or 'teacher' in a school scenario).
    In addition, nodes can have the attribute 'unit', which assigns them to a
    unit in space (for example a 'class' in a school scenario).

    verbosity: integer in [0, 1, 2], controls text output to std out to track
    simulation progress and transmission dynamics. Default = 0.

    testing, default = 'diagnostic'
        'diagnostic':   only diagnostic tests for symptomatic agents
        'background':   adds background screens of all agents after a positive
                        diagnostic test
        'preventive':   adds preventive screens of agent groups to diagnostic
                        testing. Screens happen in time intervals specified 
                        separately for each agent group in the variable 
                        'screening_interval'.
        'background+preventive': preventive screens AND background screens on
                        top of diagnostic testing.

    infection_duration, default = 11 NOTE: includes the time an agent is exposed
    but not yet infectious at the beginning of an infection
        positive integer:   mean or median of the infection duration in days
        list of two floats: mean and standard deviation of a distribution
                            specifying the infection duration in days. These
                            numbers will be used to construct a Weibull
                            distribution from which the infection duration will
                            be drawn for every agent individually

    exposure_duration, default = 4. Sets the time from transmission to becoming
    infectious
        positive integer:   mean or median of the exposure duration in days
        list of two floats: mean and standard deviation of a distribution
                            specifying the exposure duration in days. These
                            numbers will be used to construct a Weibull
                            distributoin from which the exposure duration will
                            be drawn for every agent individually.

    time_until_symptoms, default = 6. Sets the time from transmission to
    (potentially) developing symptoms. Symptom probability has to be set for
    each agent group individually using the parameter 'symptom_probability'
        positive integer:   mean or median of the time until symptoms in days
        list of two floats: mean and standard deviation of a distribution
                            specifying the time until symptoms in days. These
                            numbers will be used to construct a Weibull
                            distribution from which the time until symptoms will
                            be drawn for every agent individually.

    quarantine_duration, default = 14. Positive integer, sets the time a
    positively tested agent is quarantined in days

    infection_risk_contact_type_weights: dictionary of the form
    {'very_far':float, 'far':float, 'intermediate':float, 'close':float}
    that sets transmission risk multipliers for different contact types of
    agents specified in the contact network G. Default: {'very_far': 0.1,
    'far': 0.5, 'intermediate': 1, 'close': 3}

    subclinical_modifier: default = 1.0. Float, modifies the infectiousness of
    asymptomatic cases. Example: if subclinical_modifier = 0.5, the
    infectiousness of an asymptomatic case will be reduced to 50%.

    K1_contact_types: list of strings from ['very_far', 'far', 'intermediate',
    'close']. Definition of contact types for which agents are considered
    "K1 contact persons" if they had contact to a positively tested person wtith
    a specified contact intensity. Default = ['close'].

    diagnostic_test_type, default = 'one_day_PCR'. String, specifies the test
    technology and test result turnover time used for diagnostic testing. For
    example 'same_day_antigen' or 'two_day_PCR'. See module "Testing" for
    different implemented testing techologies.

    preventive_screening_test_type:, default = 'one_day_PCR', String, specifies
    the test technology and test result turnover time used for preventive
    sreening. For example 'same_day_antigen' or 'two_day_PCR'. See module
    "Testing" for different implemented testing techologies.

    follow_up_testing_interval, default = None. Positive integer, sets the time
    a follow-up screen (background screen) is initiated after an initial screen
    triggered by a positive test result. Only applies if the testing strategy is
    'background' or preventive.

    liberating_testing, default = False. Boolean, flag that specifies, whether
    or not an agent is released from quarantine after returning a negative test
    result.

	index_case, default = 'employee' (nursing home scenario) or 'teacher'
    (school scenario). Specifies how infections are introduced into the facility.
        agent_type:     If an agent type (for example 'student' or 'teacher' in
                        the school scenario) is specified, a single randomly
                        chosen agent from this agent group will become the index
                        case and no further index cases will be introduced into
                        the scenario.
        'continuous':   In this case, agents have a continuous risk to become
                        index cases in every simulation step. The risk has to
                        be specified for every agent group individually, using
                        the 'index_probability' parameter. If only a single
                        agent group has a non-zero index probability, then only
                        agents from this group can become index cases.


    agent_types: dictionary of the structure
        {
        agent type:
            {
            screening interval : integer, number of days between each preventive
            screen in this agent group

            index probability : float in the range [0, 1], sets the probability
            to become an index case in each time step

            mask : bool
                whether or not the agent type is wearing a mask
            }
        }

    The dictionary's keys are the names of the agent types which have to
    correspond to the node attributes in the contact graph. The screening
    interval sets the time-delay between preventive screens of this agent group,
    the index probability sets the probability of a member of this agent group
    becoming an index case in every time step

    seed: positive integer, fixes the seed of the simulation to enable
    repeatable simulation runs. If seed = None, the simulation will be
    initialized at random.
    '''

    def __init__(self, G,
        verbosity = 0,
        base_transmission_risk = 0.05,
        testing='diagnostic',
        exposure_duration = [5.0, 1.9],
        time_until_symptoms = [6.4, 0.8],
        infection_duration = [10.91, 3.95],
        vaccinated = False,
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
                             'vaccination_ratio': 0},
            'student':      {'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_ratio': 0},
            'family_member':{'screening_interval': None,
                             'index_probability': 0,
                             'mask':False,
                             'vaccination_ratio': 0}},
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

        # mesa models already implement fixed seeds through their own random
        # number generations. Sadly, we need to use the Weibull distribution
        # here, which is not implemented in mesa's random number generation
        # module. Therefore, we need to initialize the numpy random number
        # generator with the given seed as well
        if seed != None:
            np.random.seed(seed)

        # sets the (daily) transmission risk for a household contact without
        # any precautions. Target infection ratios are taken from literature
        # and the value of the base_transmission_risk is calibrated such that
        # the simulation produces the correct infection ratios in a household
        # setting with the given distributions for epidemiological parameters
        # of agents
        self.base_transmission_risk = base_transmission_risk
    	# sets the level of detail of text output to stdout (0 = no output)
        self.verbosity = check_positive_int(verbosity)
        # flag to turn off the testing & tracing strategy
        self.testing = check_testing(testing)
        self.running = True  # needed for the batch runner implemented by mesa
        # set the interaction mode to simultaneous activation
        self.schedule = SimultaneousActivation(self)


        # internal step counter used to launch screening tests
        self.Nstep = 0

        # since we may have weekday-specific contact networks, we need
        # to keep track of the day of the week. Since the index case
        # per default is introduced at step 0 in index case mode, we
        # need to offset the starting weekday by a random number of weekdays
        # to prevent artifacts from always starting on the same day of the week

        self.weekday_offset = self.random.randint(1, 8)
        self.weekday = self.Nstep + self.weekday_offset

        ## epidemiological parameters: can be either a single integer or the
        # mean and standard deviation of a distribution
        self.epi_params = {}
        # counter to track the number of pathological parameter combinations
        # that had to be re-rolled (only here for debugging and control reasons)
        self.param_rerolls = 0

        for param, param_name in zip([exposure_duration, time_until_symptoms,
                infection_duration],['exposure_duration', 'time_until_symptoms',
                'infection_duration']):

            if isinstance(param, int):
                self.epi_params[param_name] = check_positive_int(param)

            elif isinstance(param, list) and len(param) == 2:

                mu = check_positive(param[0])
                var = check_positive(param[1]**2)
                shape = root_scalar(get_weibull_shape, args=(mu, var),
                            method='toms748', bracket=[0.2, 500]).root
                scale = get_weibull_scale(mu, shape)

                self.epi_params[param_name] = [shape, scale]
            else:
                print('{} format not recognized, should be either a single '+\
                  'int or a tuple of two positive numbers'.format(param_name))


        # duration of quarantine
        self.quarantine_duration = check_positive_int(quarantine_duration)

        self.infection_risk_area_weights = check_contact_type_dict(
            infection_risk_contact_type_weights)

        # modifier for infectiosness for asymptomatic cases
        self.subclinical_modifier = check_positive(subclinical_modifier)
        # modifiers for the infection risk, depending on contact type
        self.infection_risk_contact_type_weights = infection_risk_contact_type_weights

        # modifications for age-dependent transmission and reception risks and
        # symptom probabilities
        self.age_transmission_risk_discount = \
            check_discount(age_transmission_risk_discount)

        self.age_symptom_modification = age_symptom_modification
            #check_discount(age_symptom_modification)

        self.mask_filter_efficiency = mask_filter_efficiency
        self.transmission_risk_ventilation_modifier = \
            transmission_risk_ventilation_modifier
        self.transmission_risk_vaccination_modifier = \
            transmission_risk_vaccination_modifier
        ## agents and their interactions
        # interaction graph of agents
        self.G = check_graph(G)
        # add weights as edge attributes so they can be visualised easily
        if type(self.G) == nx.MultiGraph:
            for (u, v, key, contact_type) in self.G.edges(keys=True,
                    data='contact_type'):
                self.G[u][v][key]['weight'] = \
                    self.infection_risk_contact_type_weights[contact_type]
        else:
            for e in G.edges(data=True):
                G[e[0]][e[1]]['weight'] = self.infection_risk_contact_type_weights\
                	[G[e[0]][e[1]]['contact_type']]

        # extract the different agent types from the contact graph
        self.agent_types = list(agent_types.keys())
        # dictionary of available agent classes with agent types and classes
        self.agent_classes = {}
        if 'resident' in agent_types:
            from scseirx.agent_resident import resident
            self.agent_classes['resident'] = resident
        if 'employee' in agent_types:
            from scseirx.agent_employee import employee
            self.agent_classes['employee'] = employee
        if 'student' in agent_types:
            from scseirx.agent_student import student
            self.agent_classes['student'] = student
        if 'teacher' in agent_types:
            from scseirx.agent_teacher import teacher
            self.agent_classes['teacher'] = teacher
        if 'family_member' in agent_types:
            from scseirx.agent_family_member import family_member
            self.agent_classes['family_member'] = family_member

        ## set agent characteristics for all agent groups
        # list of agent characteristics
        params = ['screening_interval','index_probability', 'mask' ,'vaccination_ratio',
                  'voluntary_testing_rate']

        # default values that are used in case a characteristic is not specified
        # for an agent group
        defaults = {'screening_interval':None,
                    'index_probability':0,
                    'mask':False,
                    'vaccination_ratio':0,
                    'voluntary_testing_rate':1
                    }

        # sanity checks that are applied to parameters passed to the class
        # constructor to make sure they conform to model expectations
        check_funcs = [check_positive_int, check_probability, check_bool,
                       check_probability, check_probability]

        # member dicts that store the parameter values for each agent group
        self.screening_intervals = {}
        self.index_probabilities = {}
        self.masks = {}
        self.vaccination_probabilities = {}
        self.voluntary_testing_rates = {}


        param_dicts = [self.screening_intervals, self.index_probabilities,
                    self.masks, self.vaccination_probabilities, self.voluntary_testing_rates]

        # iterate over all possible agent parameters and agent groups: set the
        # respective value to the value passed through the constructor or to
        # the default value if no value has been passed
        for param,param_dict,check_func in zip(params,param_dicts,check_funcs):
            for at in self.agent_types:
                try:
                    param_dict.update({at:check_func(agent_types[at][param])})
                except KeyError:
                    param_dict.update({at:defaults[param]})

        # pass all parameters relevant for the testing strategy to the testing
        # class. NOTE: this separation is not a strictly necessary design
        # decision but I like to keep the parameters related to testing and
        # tracing in a separate place
        self.Testing = Testing(self, diagnostic_test_type,
             preventive_screening_test_type,
             check_positive_int(follow_up_testing_interval),
             self.screening_intervals,
             check_bool(liberating_testing),
             check_K1_contact_types(K1_contact_types),
             verbosity)


        # specifies either continuous probability for index cases in agent
        # groups based on the 'index_probability' for each agent group, or a
        # single (randomly chosen) index case in the passed agent group
        self.index_case = check_index_case(index_case, self.agent_types)

        self.num_agents = {}

        ## add agents
        # extract the agent nodes from the graph and add them to the scheduler
        for agent_type in self.agent_types:
            IDs = [x for x,y in G.nodes(data=True) if y['type'] == agent_type]
            self.num_agents.update({agent_type:len(IDs)})

            # get the agent locations (units) from the graph node attributes
            units = [self.G.nodes[ID]['unit'] for ID in IDs]

            # determine the agents that will be vaccinated, given the 
            # vaccination ratio of the respective agent group
            vaccination_status = np.asarray([False] * len(IDs))
            if self.vaccination_probabilities[agent_type] > 0:
                n = round(self.vaccination_probabilities[agent_type] * len(IDs))
                idx = list(range(len(IDs)))
                rnd_idx = np.asarray(self.random.sample(idx, n))
                vaccination_status[rnd_idx] = True


            for ID, unit, vaccinated in zip(IDs, units, vaccination_status):

                tmp_epi_params = {}
                # for each of the three epidemiological parameters, check if
                # the parameter is an integer (if yes, pass it directly to the
                # agent constructor), or if it is specified by the shape and
                # scale parameters of a Weibull distribution. In the latter
                # case, draw a new number for every agent from the distribution
                # NOTE: parameters drawn from the distribution are rounded to
                # the nearest integer
                while True:
                    for param_name, param in self.epi_params.items():
                        if isinstance(param, int):
                            tmp_epi_params[param_name] = param

                        else:
                            tmp_epi_params[param_name] = \
                                round(weibull_two_param(param[0], param[1]))

                    if tmp_epi_params['exposure_duration'] > 0 and \
                       tmp_epi_params['time_until_symptoms'] >= \
                       tmp_epi_params['exposure_duration'] and\
                       tmp_epi_params['infection_duration'] > \
                       tmp_epi_params['exposure_duration']:
                       break
                    else:
                        self.param_rerolls += 1
                        if verbosity > 1:
                            print('pathological epi-param case found!')
                            print(tmp_epi_params)

                # check if the agent participates in voluntary testing
                p = self.voluntary_testing_rates[agent_type]
                voluntary_testing = np.random.choice([True, False],
                         p=[p, 1-p])

                # construct the agent object
                a = self.agent_classes[agent_type](ID, unit, self,
                    tmp_epi_params['exposure_duration'],
                    tmp_epi_params['time_until_symptoms'],
                    tmp_epi_params['infection_duration'],
                    vaccinated,
                    voluntary_testing,
                    verbosity)
                self.schedule.add(a)


		# infect the first agent in single index case mode
        if self.index_case != 'continuous':
            infection_targets = [
                a for a in self.schedule.agents if a.type == index_case]
            # pick a random agent to infect in the selected agent group
            target = self.random.randint(0, len(infection_targets) - 1)
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
        self.positive_tests = {self.Testing.preventive_screening_test_type:
                            {agent_type:0 for agent_type in self.agent_types},
                               self.Testing.diagnostic_test_type:
                            {agent_type:0 for agent_type in self.agent_types}}

        self.undetected_infections = 0
        self.predetected_infections = 0
        self.pending_test_infections = 0
        self.quarantine_counters = {agent_type:0 for agent_type in agent_types.keys()}
        self.false_negative = 0

        # data collectors to save population counts and agent states every
        # time step
        self.datacollector = DataCollector(
            model_reporters=
            	{
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
                },

            agent_reporters=
            	{
            	'infection_state': get_infection_state,
                'quarantine_state': get_quarantine_state
                })


    ## transmission risk modifiers
    def get_transmission_risk_contact_type_modifier(self, source, target):
        # construct the edge key as combination between agent IDs and weekday
        n1 = source.ID
        n2 = target.ID
        tmp = [n1, n2]
        tmp.sort()
        n1, n2 = tmp
        key = n1 + n2 + 'd{}'.format(self.weekday)
        contact_weight = self.G.get_edge_data(n1, n2, key)['weight']

        # the link weight is a multiplicative modifier of the link strength.
        # contacts of type "close" have, by definition, a weight of 1. Contacts
        # of type intermediate, far or very far have a weight < 1 and therefore
        # are less likely to transmit an infection. For example, if the contact
        # type far has a weight of 0.2, a contact of type far has only a 20%
        # chance of transmitting an infection, when compared to a contact of
        # type close. To calculate the probability of success p in the Bernoulli
        # trial, we need to reduce the base risk (or base probability of success)
        # by the modifications introduced by preventive measures. These
        # modifications are formulated in terms of "probability of failure", or
        # "q". A low contact weight has a high probability of failure, therefore
        # we return q = 1 - contact_weight here.
        q1 = 1 - contact_weight

        return q1


    def get_transmission_risk_age_modifier_transmission(self, source):
        '''linear function such that at age 18 the risk is that of an adult (=1).
        The slope of the line needs to be calibrated.
        '''
        age = source.age
        max_age = 18
        if age <= max_age:
            age_weight = self.age_transmission_risk_discount['slope'] * \
                 np.abs(age - max_age) + self.age_transmission_risk_discount['intercept']

            # The age weight can be interpreted as multiplicative factor that
            # reduces the chance for transmission with decreasing age. The slope
            # of the age_transmission_discount function is the decrease (in % of
            # the transmission risk for an 18 year old or above) of transmission
            # risk with every year a person is younger than 18 (the intercept is
            # 1 by definition).
            # To calculate the probability of success p in the Bernoulli
            # trial, we need to reduce the base risk (or base probability of success)
            # by the modifications introduced by preventive measures. These
            # modifications are formulated in terms of "probability of failure", or
            # "q". A low age weight has a high probability of failure, therefore
            # we return q = 1 - age_weight here.
            q2 = 1 - age_weight
        else:
            q2 = 0

        return q2


    def get_transmission_risk_age_modifier_reception(self, target):
        '''linear function such that at age 18 the risk is that of an adult (=1).
        The slope of the line needs to be calibrated.
        '''
        age = target.age
        max_age = 18
        if age <= max_age:
            age_weight = self.age_transmission_risk_discount['slope'] * \
            np.abs(age - max_age) + self.age_transmission_risk_discount['intercept']
            # see description in get_transmission_risk_age_modifier_transmission
            q3 = 1 - age_weight
        else:
            q3 = 0

        return q3


    # infectiousness is constant and high until symptom onset and then
    # decreases monotonically until agents are not infectious anymore
    # at the end of the infection_duration
    def get_transmission_risk_progression_modifier(self, source):
        if source.days_since_exposure < source.exposure_duration:
            progression_weight = 0
        elif source.days_since_exposure <= source.time_until_symptoms:
            progression_weight = 1
        elif source.days_since_exposure > source.time_until_symptoms and \
             source.days_since_exposure <= source.infection_duration:
            # we add 1 in the denominator, such that the source is also
            # (slightly) infectious on the last day of the infection_duration
            progression_weight = \
                 (source.days_since_exposure - source.time_until_symptoms) / \
                 (source.infection_duration - source.time_until_symptoms + 1)
        else:
            progression_weight = 0
        # see description in get_transmission_risk_age_modifier_transmission
        q4 = 1 - progression_weight

        return q4

    def get_transmission_risk_subclinical_modifier(self, source):
        if source.symptomatic_course == False:
            subclinical_weight = self.subclinical_modifier
        else:
            subclinical_weight = 1
        # see description in get_transmission_risk_age_modifier_transmission
        q5 = 1 - subclinical_weight
        return q5

    def get_transmission_risk_exhale_modifier(self, source):
        if source.mask:
            exhale_weight = self.mask_filter_efficiency['exhale']
        else:
            exhale_weight = 1
        # see description in get_transmission_risk_age_modifier_transmission
        q6 = 1 - exhale_weight
        return q6


    def get_transmission_risk_inhale_modifier(self, target):
        if target.mask:
            inhale_weight = self.mask_filter_efficiency['inhale']
        else:
            inhale_weight = 1
        # see description in get_transmission_risk_age_modifier_transmission
        q7 = 1 - inhale_weight
        return q7


    def get_transmission_risk_ventilation_modifier(self):
        ventilation_weight = self.transmission_risk_ventilation_modifier
        # see description in get_transmission_risk_age_modifier_transmission
        q8 = 1 - ventilation_weight
        return q8

    def get_transmission_risk_vaccination_modifier_reception(self, a):
        if a.vaccinated:
            q9 = self.transmission_risk_vaccination_modifier['reception']
        else:
            q9 = 0
        return q9

    def get_transmission_risk_vaccination_modifier_transmission(self, a):
        if a.vaccinated:
            q10 = self.transmission_risk_vaccination_modifier['transmission']
        else:
            q10 = 0
        return q10

    def test_agent(self, a, test_type):
        a.tested = True
        a.pending_test = test_type
        if test_type == self.Testing.diagnostic_test_type:
            self.number_of_diagnostic_tests += 1
        else:
            self.number_of_preventive_screening_tests += 1

        if a.exposed:
            # tests that happen in the period of time in which the agent is
            # exposed but not yet infectious. 
            # Note: tests[test_type]['time_until_testable'] is negative for
            # tests that can detect an infection before agents become infectious
            if a.days_since_exposure >= a.exposure_duration + \
                    self.Testing.tests[test_type]['time_until_testable']:
                
                if self.verbosity > 1:
                    print('{} {} sent positive sample (even though not infectious yet)'
                    .format(a.type, a.ID))
                a.sample = 'positive'
                self.predetected_infections += 1
                self.positive_tests[test_type][a.type] += 1
            else:
                if self.verbosity > 1: print('{} {} sent negative sample'
                    .format(a.type, a.ID))
                a.sample = 'negative'

        elif a.infectious:
            # tests that happen in the period of time in which the agent is
            # infectious and the infection is detectable by a given test
            # Note: tests[test_type]['time_until_testable'] is negative for 
            # tests that can detect an infection before agents become 
            # infectious. tests[test_type]['time_testable'] is negative for
            # tests that cease to detect an infection before agents stop being
            # infectious
            if a.days_since_exposure >= a.exposure_duration + \
                    self.Testing.tests[test_type]['time_until_testable'] and \
               a.days_since_exposure <= a.infection_duration + \
                    self.Testing.tests[test_type]['time_testable']:
                if self.verbosity > 1:
                    print('{} {} sent positive sample'.format(a.type, a.ID))
                a.sample = 'positive'
                self.positive_tests[test_type][a.type] += 1

            # track the undetected infections to assess how important they are
            # for infection spread
            else:
                if self.verbosity > 1:
                    print('{} {} sent negative sample (even though infectious)'
                    .format(a.type, a.ID))
                a.sample = 'negative'
                self.undetected_infections += 1

        else:
            if self.verbosity > 1: print('{} {} sent negative sample'
                .format(a.type, a.ID))
            a.sample = 'negative'

        # for same-day testing, immediately act on the results of the test
        if a.days_since_tested >= self.Testing.tests[test_type]['time_until_test_result']:
            a.act_on_test_result()

    def screen_agents(self, agent_group, test_type, screen_type):
        # only test agents that have not been tested already in this simulation
        # step and that are not already known positive cases

        if self.verbosity > 0:
            print('initiating {} {} screen'\
                                .format(screen_type, agent_group))

        untested_agents = [a for a in self.schedule.agents if
            (a.tested == False and a.known_positive == False
                and a.type == agent_group)]

        if len(untested_agents) > 0:
            self.screened_agents[screen_type][agent_group] = True
            self.days_since_last_agent_screen[agent_group] = 0

            # only test agents if they participate in voluntary testing
            if screen_type == 'preventive':
                for a in untested_agents:
                    if a.voluntary_testing:
                        self.test_agent(a, test_type)
                    else:
                        if self.verbosity > 1:
                            print('not testing {} {}, not participating in voluntary testing'\
                                .format(agent_group, a.ID))
            else:
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
            a.quarantine_start = self.Nstep

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
            K1_contact.quarantine_start = self.Nstep

    def test_symptomatic_agents(self):
        # find symptomatic agents that have not been tested yet and are not
        # in quarantine and test them
        newly_symptomatic_agents = np.asarray([a for a in self.schedule.agents
            if (a.symptoms == True and a.tested == False and a.quarantined == False)])

        for a in newly_symptomatic_agents:
            # all symptomatic agents are quarantined by default
            if self.verbosity > 0:
                print('quarantined: {} {}'.format(a.type, a.ID))
            a.quarantined = True
            a.quarantine_start = self.Nstep

            self.test_agent(a, self.Testing.diagnostic_test_type)

    def quarantine_contacts(self):
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


    def step(self):
        self.weekday = (self.Nstep + self.weekday_offset) % 7 + 1
        # if the connection graph is time-resloved, set the graph that is
        # used to determine connections in this step to the sub-graph corres-
        # ponding to the current day of the week
        if self.dynamic_connections:
            self.G = self.weekday_connections[self.weekday]

        if self.verbosity > 0:
            print('weekday {}'.format(self.weekday))

        if self.testing:
            for agent_type in self.agent_types:
                for screen_type in ['reactive', 'follow_up', 'preventive']:
                    self.screened_agents[screen_type][agent_type] = False

            if self.verbosity > 0:
                print('* testing and tracing *')

            self.test_symptomatic_agents()


            # collect and act on new test results
            agents_with_test_results = self.collect_test_results()
            for a in agents_with_test_results:
                a.act_on_test_result()

            self.quarantine_contacts()

            # screening:
            # a screen should take place if
            # (a) there are new positive test results
            # (b) as a follow-up screen for a screen that was initiated because
            # of new positive cases
            # (c) if there is a preventive screening policy and it is time for
            # a preventive screen in a given agent group

            # (a)
            if (self.testing == 'background' or self.testing == 'background+preventive')\
               and self.new_positive_tests == True:
                for agent_type in self.screening_agents:
                    self.screen_agents(
                        agent_type, self.Testing.diagnostic_test_type, 'reactive')
                    self.scheduled_follow_up_screen[agent_type] = True

            # (b)
            elif (self.testing == 'background' or self.testing == 'background+preventive') and \
                self.Testing.follow_up_testing_interval != None and \
                sum(list(self.scheduled_follow_up_screen.values())) > 0:
                for agent_type in self.screening_agents:
                    if self.scheduled_follow_up_screen[agent_type] and\
                       self.days_since_last_agent_screen[agent_type] >=\
                       self.Testing.follow_up_testing_interval:
                        self.screen_agents(
                            agent_type, self.Testing.diagnostic_test_type, 'follow_up')
                    else:
                        if self.verbosity > 0:
                            print('not initiating {} follow-up screen (last screen too close)'\
                                .format(agent_type))

            # (c) 
            elif (self.testing == 'preventive' or self.testing == 'background+preventive')and \
                np.any(list(self.Testing.screening_intervals.values())):

                for agent_type in self.screening_agents:
                    interval = self.Testing.screening_intervals[agent_type]
                    assert interval in [7, 3, 2, None], \
                        'testing interval {} for agent type {} not supported!'\
                        .format(interval, agent_type)

                    # (c.1) testing every 7 days = testing on Mondays
                    if interval == 7 and self.weekday == 1:
                        self.screen_agents(agent_type,
                            self.Testing.preventive_screening_test_type,\
                             'preventive')
                    # (c.2) testing every 3 days = testing on Mo & Turs
                    elif interval == 3 and self.weekday in [1, 4]:
                            self.screen_agents(agent_type,
                            self.Testing.preventive_screening_test_type,\
                             'preventive')
                    # (c.3) testing every 2 days = testing on Mo, Wed & Fri
                    elif interval == 2 and self.weekday in [1, 3, 5]:
                            self.screen_agents(agent_type,
                            self.Testing.preventive_screening_test_type,\
                             'preventive')
                    # No interval specified = no testing, even if testing
                    # mode == preventive
                    elif interval == None:
                        pass
                    else:
                        if self.verbosity > 0:
                            print('not initiating {} preventive screen (wrong weekday)'\
                                    .format(agent_type))
            else:
                # do nothing
                pass

            for agent_type in self.agent_types:
                if not (self.screened_agents['reactive'][agent_type] or \
                        self.screened_agents['follow_up'][agent_type] or \
                        self.screened_agents['preventive'][agent_type]):
                        self.days_since_last_agent_screen[agent_type] += 1


        if self.verbosity > 0: print('* agent interaction *')
        self.datacollector.collect(self)
        self.schedule.step()
        self.Nstep += 1
