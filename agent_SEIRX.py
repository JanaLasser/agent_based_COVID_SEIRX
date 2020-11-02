from mesa import Agent

# NOTE: "patients" and "inhabitants" are used interchangeably in the documentation


class agent_SEIRX(Agent):
    '''
    An agent with an infection status
    '''

    def __init__(self, unique_id, quarter, model, verbosity):
        super().__init__(unique_id, model)
        self.verbose = verbosity
        self.ID = unique_id
        self.quarter = quarter

        # infection states
        self.exposed = False
        self.infected = False
        self.symptomatic_course = False
        self.symptoms = False
        self.recovered = False
        self.tested = False
        self.pending_test_result = False
        self.known_positive = False
        self.quarantined = False

        # sample given for test
        self.sample = None

        # staging states
        self.contact_to_infected = False

        # counters
        self.days_exposed = 0
        self.days_infected = 0
        self.days_quarantined = 0
        self.days_since_tested = 0
        self.transmissions = 0
        self.transmission_targets = {}

    # generic helper functions
    def introduce_external_infection(self):
        if (self.infected == False) and (self.exposed == False) and\
           (self.recovered == False):
            index_transmission = self.random.random()
            if index_transmission <= self.index_probability:
                self.contact_to_infected = True
                if self.verbose > 0:
                    print('{} {} is index case'.format(
                        self.type, self.unique_id))

    def get_employee_patient_contacts(self):
        # only contacts to patients in the same quarter are possible
        contacts = [a for a in self.model.schedule.agents if
            (a.type == 'patient' and a.quarter == self.quarter)]
        return contacts

    def get_employee_employee_contacts(self):
        # only contacts to employees in the same quarter
        contacts = [a for a in self.model.schedule.agents if
            (a.type == 'employee' and a.quarter == self.quarter)]

        # TODO: implement random cross-quarter interaction of employees
        # if self.model.employee_cross_quarter_interaction:
        return contacts

    def get_patient_employee_contacts(self):
        # only contacts to employees in the same quarter are possible
        contacts = [a for a in self.model.schedule.agents if
            (a.type == 'employee' and a.quarter == self.quarter)]
        return contacts

    def get_patient_patient_contacts(self):
        # patient <-> patient contacts are determined by the contact network
        # get a list of neighbor IDs from the interaction network
        contacts = [tup[1] for tup in list(self.model.G.edges(self.ID))]
        # get the neighboring agents from the scheduler using their IDs
        contacts = [a for a in self.model.schedule.agents if a.ID in contacts]
        return contacts

    def transmit_infection(self, contacts, transmission_risk, modifier):
        for c in contacts:
            if (c.exposed == False) and (c.infected == False) and \
               (c.recovered == False) and (c.contact_to_infected == False):

                # draw random number for transmission
                transmission = self.random.random() * modifier

                if transmission > 1 - transmission_risk:
                    c.contact_to_infected = True
                    self.transmissions += 1

                    # track the state of the agent pertaining to testing at the
                    # moment of transmission to count how many transmissions
                    # occur in which states
                    if self.tested and self.pending_test_result and \
                        self.sample == 'positive':
                        self.model.pending_test_infections += 1

                    self.transmission_targets.update({c.ID:self.model.Nstep})

                    if self.verbose > 0:
                        print('transmission: {} {} -> {} {}'
                        .format(self.type, self.unique_id, c.type, c.unique_id))

    def act_on_test_result(self):
        self.pending_test_result = False

        if self.sample == 'positive':

            # true positive
            if self.model.Testing.sensitivity >= self.model.random.random():
                self.model.newly_positive_agents.append(self)
                self.known_positive = True

                if self.model.verbosity > 0:
                    print('{} {} returned a positive test (true positive)'
                        .format(self.type, self.ID))

                if self.quarantined == False:
                    self.quarantined = True
                    if self.model.verbosity > 0:
                        print('quarantined {} {}'.format(self.type, self.ID))

            # false negative
            else:
                if self.model.verbosity > 0:
                    print('{} {} returned a negative test (false negative)'\
                        .format(self.type, self.ID))
                self.known_positive = False

                if self.model.Testing.liberating_testing:
                    self.quarantined = False
                    if self.model.verbosity > 0:
                        print('{} {} left quarantine prematurely'\
                        .format(self.type, self.ID))

            self.days_since_tested = 0
            self.tested = False
            self.sample = None

        elif self.sample == 'negative':

            # false positive
            if self.model.Testing.specificity <= self.model.random.random():
                self.model.newly_positive_agents.append(self)
                self.known_positive = True

                if self.model.verbosity > 0:
                    print('{} {} returned a positive test (false positive)'\
                        .format(self.type, self.ID))

                if self.quarantined == False:
                    self.quarantined = True
                    if self.model.verbosity > 0:
                        print('quarantined {} {}'.format(self.type, self.ID))

            # true negative
            else:
                if self.model.verbosity > 0:
                    print('{} {} returned a negative test (true negative)'\
                        .format(self.type, self.ID))
                self.known_positive = False

                if self.model.Testing.liberating_testing:
                    self.quarantined = False
                    if self.model.verbosity > 0:
                        print('{} {} left quarantine prematurely'\
                        .format(self.type, self.ID))

            self.days_since_tested = 0
            self.sample = None

    def recover(self):
        self.infected = False
        self.symptoms = False
        self.recovered = True
        if self.verbose > 0:
            print('{} recovered: {}'.format(self.type, self.unique_id))

    def check_exposure_duration(self):
        if self.days_exposed >= self.model.exposure_duration:
            self.exposed = False
            self.infected = True
            if self.verbose > 0:
                print('{} infectious: {}'.format(self.type, self.unique_id))

            # determine if infected agent ẃill show symptoms
            if self.random.random() <= self.model.symptom_probability:
                self.symptomatic_course = True

        else:
            self.days_exposed += 1

    def check_symptoms(self):
        # determine if agent shows symptoms
        if (self.symptomatic_course and \
            self.days_infected >= self.model.time_until_symptoms and \
            self.days_infected < self.model.infection_duration and \
            not self.symptoms):

            self.symptoms = True
            if self.model.verbosity > 0:
                print('{} {} shows symptoms'.format(self.type, self.ID))

    def check_quarantine_duration(self):
        if self.days_quarantined >= self.model.quarantine_duration:
            if self.verbose > 0:
                print('{} released from quarantine: {}'.format(
                    self.type, self.unique_id))
            self.quarantined = False
        else:
            self.days_quarantined += 1

    def become_exposed(self):
        if self.verbose > 0:
            print('{} exposed: {}'.format(self.type, self.unique_id))
        self.exposed = True
        self.contact_to_infected = False


    def advance(self):
        '''
        Advancing step: applies infections, checks counters and sets infection 
        states accordingly
        '''

        # determine if there is a test result and act accordingly. Test
        # results depend on whether the agent has submitted a sample that
        # is testable (i.e. contains a detectable amount of virus) and on
        # the sensitivity/specificity of the chosen test
        if self.pending_test_result:

            if self.days_since_tested >= self.model.Testing.time_until_test_result:
                self.act_on_test_result()
            else:
                self.days_since_tested += 1

        # determine if agent has transitioned from exposed to infected
        if self.exposed:
            self.check_exposure_duration()

        if self.infected:
            self.check_symptoms()

            # determine if agent has recovered
            if self.days_infected >= self.model.infection_duration:
                self.recover()
            else:
                self.days_infected += 1

        # determine if agent is released from quarantine
        if self.quarantined:
            self.check_quarantine_duration()

        # determine if a transmission to the agent occurred
        if self.contact_to_infected == True:
            self.become_exposed()

        # set tested flag to false at the end of the agent step
        self.tested = False
