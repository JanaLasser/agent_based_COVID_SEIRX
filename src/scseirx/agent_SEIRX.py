from mesa import Agent


class agent_SEIRX(Agent):
    '''
    An agent with an infection status. NOTe: this agent is not
    functional on it's own, as it does not implement a step()
    function. Therefore, every agent class that inherits from this
    generic agent class needs to implement their own step() function
    '''

    def __init__(self, unique_id, unit, model,
        exposure_duration, time_until_symptoms, infection_duration, vaccinated,
        voluntary_testing, verbosity):
        super().__init__(unique_id, model)
        self.verbose = verbosity
        self.ID = unique_id
        self.unit = unit
        self.voluntary_testing = voluntary_testing

        ## epidemiological parameters drawn from distributions
        # NOTE: all durations are inclusive, i.e. comparison are "<=" and ">="
        # number of days agents stay infectuous

        # days after transmission until agent becomes infectuous
        self.exposure_duration = exposure_duration
        # days after becoming infectuous until showing symptoms
        self.time_until_symptoms = time_until_symptoms
        # number of days agents stay infectuous
        self.infection_duration = infection_duration
        # vaccinated true or false (depending on chosen probability)
        self.vaccinated = vaccinated


        ## agent-group wide parameters that are stored in the model class
        self.index_probability = self.model.index_probabilities[self.type]
        self.mask = self.model.masks[self.type]

        # try to set the agent's age from information in the graph. The age info
        # is later needed to adjust transmission risk and the probability to
        # develop a symptomatic course. If the age information doees not exist,
        # age is set to 0, the transmission risk remains unmodified and the
        # probability to develop a symptomatic course is set to the intercept
        # specified at model setup
        try: 
            self.age = model.G.nodes(data=True)[self.unique_id]['age']
        except KeyError:
            self.age = 0

        ## age adjustments
        # adjust symptom probability based on age
        self.symptom_probability = \
                        self.age * self.model.age_symptom_modification['slope'] + \
                        self.model.age_symptom_modification['intercept']


        ## infection states
        self.exposed = False
        self.infectious = False
        self.symptomatic_course = False

        if not self.vaccinated and \
            self.model.random.random() <= self.symptom_probability:
            self.symptomatic_course = True


        self.symptoms = False
        self.recovered = False
        self.tested = False
        self.pending_test = False
        self.known_positive = False
        self.quarantined = False

        # sample given for test
        self.sample = None

        # staging states
        self.contact_to_infected = False

        # counters
        self.days_since_exposure = 0
        self.days_quarantined = 0
        self.days_since_tested = 0
        self.transmissions = 0
        self.transmission_targets = {}



    ### generic helper functions that are inherited by other agent classes

    def get_contacts(self, agent_group):
        contacts = [a for a in self.model.schedule.agents if
            (a.type == agent_group and self.model.G.has_edge(self.ID, a.ID))]
        return contacts


    def introduce_external_infection(self):
        if (self.infectious == False) and (self.exposed == False) and\
           (self.recovered == False):
            index_transmission = self.model.random.random()
            if index_transmission <= self.index_probability:
                self.contact_to_infected = True
                if self.verbose > 0:
                    print('{} {} is index case'.format(
                        self.type, self.unique_id))


    def transmit_infection(self, contacts):
        # the basic transmission risk is that between two members of the 
        # same household and has been calibrated to reproduce empirical 
        # household secondary attack rates.
        base_risk = self.model.base_transmission_risk

        for target in contacts:
            if (target.exposed == False) and (target.infectious == False) and \
               (target.recovered == False) and (target.contact_to_infected == False):

                # determine if a transmission occurrs
                p = self.model.calculate_transmission_probability(\
                                self, target, base_risk)
                transmission = self.model.random.random()

                if self.verbose > 1:
                    print('target: {} {}, p: {}'\
                        .format(target.type, target.ID, p))

                if transmission < p:
                    target.contact_to_infected = True
                    self.transmissions += 1

                    # track the state of the agent pertaining to testing at the
                    # moment of transmission to count how many transmissions
                    # occur in which states
                    if self.tested and self.pending_test and \
                        self.sample == 'positive':
                        self.model.pending_test_infections += 1

                    self.transmission_targets.update({target.ID:self.model.Nstep})

                    if self.verbose > 0:
                        print('transmission: {} {} -> {} {} (p: {})'
                        .format(self.type, self.unique_id, \
                                target.type, target.unique_id, p))


    def act_on_test_result(self):
        '''
        Function that gets called by the infection dynamics model class if a
        test result for an agent is returned. The function sets agent states
        according to the result of the test (positive or negative). Adds agents
        with positive tests to the newly_positive_agents list that will be
        used to trace and quarantine close (K1) contacts of these agents. Resets
        the days_since_tested counter and the sample as well as the 
        pending_test flag
        '''

        # the type of the test used in the test for which the result is pending
        # is stored in the pending_test variable
        test_type = self.pending_test

        if self.sample == 'positive':

            # true positive
            if self.model.Testing.tests[test_type]['sensitivity'] >= self.model.random.random():
                self.model.newly_positive_agents.append(self)
                self.known_positive = True

                if self.model.verbosity > 1:
                    print('{} {} returned a positive test (true positive)'
                        .format(self.type, self.ID))

                if self.quarantined == False:
                    self.quarantined = True
                    if self.model.verbosity > 0:
                        print('quarantined {} {}'.format(self.type, self.ID))

            # false negative
            else:
                if self.model.verbosity > 1:
                    print('{} {} returned a negative test (false negative)'\
                        .format(self.type, self.ID))
                self.known_positive = False
                self.model.false_negative += 1

                if self.model.Testing.liberating_testing:
                    self.quarantined = False
                    if self.model.verbosity > 0:
                        print('{} {} left quarantine prematurely'\
                        .format(self.type, self.ID))

            self.days_since_tested = 0
            self.pending_test = False
            self.sample = None

        elif self.sample == 'negative':

            # false positive
            if self.model.Testing.tests[test_type]['specificity'] <= self.model.random.random():
                self.model.newly_positive_agents.append(self)
                self.known_positive = True

                if self.model.verbosity > 1:
                    print('{} {} returned a positive test (false positive)'\
                        .format(self.type, self.ID))

                if self.quarantined == False:
                    self.quarantined = True
                    if self.model.verbosity > 0:
                        print('quarantined {} {}'.format(self.type, self.ID))

            # true negative
            else:
                if self.model.verbosity > 1:
                    print('{} {} returned a negative test (true negative)'\
                        .format(self.type, self.ID))
                self.known_positive = False

                if self.model.Testing.liberating_testing:
                    self.quarantined = False
                    if self.model.verbosity > 0:
                        print('{} {} left quarantine prematurely'\
                        .format(self.type, self.ID))

            self.days_since_tested = 0
            self.pending_test = False
            self.sample = None

    def become_exposed(self):
        if self.verbose > 0:
            print('{} exposed: {}'.format(self.type, self.unique_id))
        self.exposed = True
        self.contact_to_infected = False


    def become_infected(self):
        self.exposed = False
        self.infectious = True

        if self.verbose > 0:
            if self.symptomatic_course:
                print('{} infectious: {} (symptomatic course)'\
                    .format(self.type, self.unique_id))
            else:
                print('{} infectious: {} (asymptomatic course)'\
                    .format(self.type, self.unique_id))


    def show_symptoms(self):
        # determine if agent shows symptoms
        if self.symptomatic_course:
            self.symptoms = True
            if self.model.verbosity > 0:
                print('{} {} shows symptoms'.format(self.type, self.ID))


    def recover(self):
        self.infectious = False
        self.symptoms = False
        self.recovered = True
        self.days_since_exposure = self.infection_duration + 1
        if self.verbose > 0:
            print('{} recovered: {}'.format(self.type, self.unique_id))


    def leave_quarantine(self):
        if self.verbose > 0:
            print('{} released from quarantine: {}'.format(
                self.type, self.unique_id))
        self.quarantined = False
        self.days_quarantined = 0


    def advance(self):
        '''
        Advancing step: applies infections, checks counters and sets infection 
        states accordingly
        '''

        # determine if a transmission to the agent occurred
        if self.contact_to_infected == True:
            self.become_exposed()

        # determine if agent has transitioned from exposed to infected
        if self.days_since_exposure == self.exposure_duration:
            self.become_infected()

        if self.days_since_exposure == self.time_until_symptoms:
            self.show_symptoms()

        if self.days_since_exposure == self.infection_duration:
            self.recover()

        # determine if agent is released from quarantine
        if self.days_quarantined == self.model.quarantine_duration:
            self.leave_quarantine()

        # if there is a pending test result, increase the days the agent has
        # waited for the result by 1 (NOTE: results are collected by the 
        # infection dynamics model class according to days passed since the test)
        if self.pending_test:
            self.days_since_tested += 1

        if self.quarantined:
            self.days_quarantined += 1
            self.model.quarantine_counters[self.type] += 1

        if self.exposed or self.infectious:
            self.days_since_exposure += 1

        # reset tested flag at the end of the agent step
        self.tested = False
        
