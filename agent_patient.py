from mesa import Agent

# NOTE: "patients" and "inhabitants" are used interchangeably in the documentation

class Patient(Agent):
    '''
    A patient with a health status
    '''
    def __init__(self, unique_id, model, verbosity):
        super().__init__(unique_id, model)
        self.verbose = verbosity
        self.ID = unique_id
        self.type = 'patient'

        # infection states
        self.exposed = False
        self.infected = False
        self.symptomatic_course = False
        self.symptoms = False
        self.recovered = False
        self.testable = False
        self.tested = False
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
        

    def step(self):
        '''
        Infection step: if a patient is infected and not in quarantine, it 
        iterates through all other patients it has contact with and tries to 
        infect them. Infections are staged here and only applied in the 
        "advance"-step to simulate "simultaneous" interaction
        '''
        # check for external infection in continuous index case modes
        if self.model.index_case_mode in ['continuous_patient', 'continuous_both']:
            if (self.infected == False) and (self.exposed == False) and\
               (self.recovered == False):
                index_transmission = self.random.random()
                if index_transmission <= self.model.index_probability_patient:
                    self.contact_to_infected = True
                    if self.verbose > 0:
                        print('{} {} is index case'.format(self.type, self.unique_id))

        if self.infected:
            if not self.quarantined:
                # infectiousness is constant and high during the first 2 days (pre-symptomatic)
                # and then decreases monotonically for 8 days until agents are not infectious 
                # anymore 10 days after the onset of infectiousness
                modifier = 1 - max(0, self.days_infected - 2) / 8

                # if infectiousness is modified for asymptomatic cases, moltiply the asymptomatic
                # modifier with the days-infected modifier 
                if self.symptomatic_course == False:
                    modifier *= self.model.subclinical_modifier

                # get a list of neighbor IDs from the interaction network
                neighbors = [tup[1] for tup in list(self.model.G.edges(self.ID))]
                # get the neighboring agents from the scheduler using their IDs
                neighbors = [a for a in self.model.schedule.agents if a.ID in neighbors]

                for a in neighbors:
                    if (a.exposed == False) and (a.infected == False) and \
                       (a.recovered == False) and (a.contact_to_infected == False):
                        # draw random number for transmission
                        transmission = self.random.random() * modifier
                        # get link strength from the interaction network
                        area = self.model.G[self.ID][a.ID]['area']
                        transmission = transmission * self.model.infection_risk_area_weights[area]

                        if transmission > 1 - self.model.transmission_risk_patient_patient:
                            a.contact_to_infected = True
                            self.transmissions += 1
                            self.transmission_targets.update({self.model.Nstep:a.ID})
                            if self.verbose > 0: print('transmission: patient {} -> patient {}'\
                                .format(self.unique_id, a.unique_id))

                # transmission from patients to employees
                employees = [
                    a for a in self.model.schedule.agents if a.type == 'employee']
                for e in employees:
                    if (e.exposed == False) and (e.infected == False) and\
                       (e.recovered == False) and (e.contact_to_infected == False):
                        transmission = self.random.random() * modifier

                        if transmission > 1 - self.model.transmission_risk_employee_employee:
                            e.contact_to_infected = True
                            self.transmissions += 1
                            self.transmission_targets.update({self.model.Nstep:e.ID})
                            if self.verbose > 0:
                                print('transmission: patient {} -> employee {}'
                                      .format(self.unique_id, e.unique_id))

    '''
    Advancing step: applies infections, checks counters and sets infection 
    states accordingly
    '''
    def advance(self):
 # determine if there is a test result and act accordingly. Test
        # results depend on whether the agent has submitted a sample that
        # is testable (i.e. contains a detectable amount of virus) and on
        # the sensitivity/specificity of the chosen test
        if self.tested and self.days_since_tested >= self.model.Testing.time_until_test_result:
            if self.sample == 'positive':

                # true positive
                if self.model.Testing.sensitivity >= self.model.random.random(): 
                    if self.model.verbosity > 0:
                        print('{} {} returned a positive test (true positive)'\
                            .format(self.type, self.ID))
                    self.model.newly_positive_agents.append(self)
                    self.quarantine = True
                    self.known_positive = True

                # false negative
                else:
                    if self.model.verbosity > 0:
                        print('{} {} returned a negative test (false negative)'\
                            .format(self.type, self.ID))
                    self.known_positive = False

                self.days_since_tested = 0
                self.tested = False
                self.sample = None

            elif self.sample == 'negative':

                # false positive
                if self.model.Testing.specificity <= self.model.random.random():
                    if self.model.verbosity > 0:
                        print('{} {} returned a positive test (false positive)'\
                            .format(self.type, self.ID))

                    self.model.newly_positive_agents.append(self)
                    self.quarantine = True
                    self.known_positive = True

                # true negative
                else:
                    if self.model.verbosity > 0:
                        print('{} {} returned a negative test (true negative)'\
                            .format(self.type, self.ID))
                    self.quarantine = False
                    self.known_positive = False

                self.days_since_tested = 0
                self.tested = False
                self.sample = None

        elif self.tested and self.days_since_tested < self.model.Testing.time_until_test_result:
            self.days_since_tested += 1
        else:
            pass


        if self.infected:
            # determine if patient shows symptoms
            if self.symptomatic_course and self.days_infected >= self.model.time_until_symptoms and\
                self.days_infected < self.model.infection_duration:
                self.symptoms = True
            # determine if patient has recovered
            if self.days_infected >= self.model.infection_duration:
                self.infected = False
                self.symptoms = False
                self.recovered = True
                if self.verbose > 0: print('{} recovered: {}'.format(self.type, self.unique_id))
            else:
                self.days_infected += 1

        # determine if patient is testable
        if (self.infected == True) and (self.days_infected >= self.model.time_until_symptoms and \
            (self.days_infected) <= self.model.time_testable):
            if self.testable == False:
                if self.verbose > 0:
                    if self.symptomatic_course:
                        print('{} {} testable (symptoms)'.format(self.type, self.unique_id))
                    else:
                        print('{} {} testable (no symptoms)'.format(self.type, self.unique_id))
                self.testable = True
        else:
            self.testable = False


        # determine if patient has transitioned from exposed to infected
        if self.exposed:
            #if self.verbose > 0: print('exposed: {}'.format(self.unique_id))
            if self.days_exposed >= self.model.exposure_duration:
                if self.verbose > 0: print('{} infectious: {}'.format(self.type, self.unique_id))
                self.exposed = False
                self.infected = True
                # determine if infected patient will have symptomatic infection
                if self.random.random() <= self.model.symptom_probability:
                    self.symptomatic_course = True
            else:
                self.days_exposed += 1

        # determine if patient is released from quarantine
        if self.quarantined:
            if self.days_quarantined >= self.model.quarantine_duration:
                if self.verbose > 0: print('{} released from quarantine {}'.format(self.type, self.unique_id))
                self.quarantined = False
            else:
                self.days_quarantined += 1

        # determine if a transmission to the infected occurred
        if self.contact_to_infected == True:
            if self.verbose > 0: print('{} exposed: {}'.format(self.type, self.unique_id))
            self.exposed = True
            self.contact_to_infected = False


            


            


            
        