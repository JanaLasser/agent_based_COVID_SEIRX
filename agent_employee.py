from mesa import Agent

# NOTE: "patients" and "inhabitants" are used interchangeably in the documentation


class Employee(Agent):
    '''
    An employee with an infection status
    '''

    def __init__(self, unique_id, model, verbosity):
        super().__init__(unique_id, model)
        self.verbose = verbosity
        self.ID = unique_id
        self.type = 'employee'

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
        Infection step: if an employee is infected and not in quarantine, it 
        iterates through all other patients and employees tries to 
        infect them. Infections are staged here and only applied in the 
        "advance"-step to simulate "simultaneous" interaction
        '''
        # check for external infection in continuous index case modes
        if self.model.index_case_mode in ['continuous_employee', 'continuous_both']:
	        if (self.infected == False) and (self.exposed == False) and\
	           (self.recovered == False):
	            index_transmission = self.random.random()
	            if index_transmission <= self.model.index_probability_employee:
	                self.contact_to_infected = True
	                if self.verbose > 0:
	                    print('employee {} is index case'.format(self.unique_id))


        if self.infected:
            # determine if patient is in quarantine
            if not self.quarantined:
                # infectiousness is constant and high during the first 2 days (pre-symptomatic)
                # and then decreases monotonically for 8 days until agents are not infectious 
                # anymore 10 days after the onset of infectiousness
                modifier = 1 - max(0, self.days_infected - 2) / 8

                # if infectiousness is modified for asymptomatic cases, moltiply the asymptomatic
                # modifier with the days-infected modifier 
                if self.symptomatic_course == False:
                    modifier *= self.model.subclinical_modifier

                # get a list of patients
                patients = [
                    a for a in self.model.schedule.agents if a.type == 'patient']
                # get a list of employees
                employees = [
                    a for a in self.model.schedule.agents if a.type == 'employee']

                # code transmission to employees and transmission to patients separately
                # to allow for differences in transmissions later

                # transmission from patients to patients
                for p in patients:
                    if (p.exposed == False) and (p.infected == False) and \
                       (p.recovered == False) and (p.contact_to_infected == False):
                        # draw random number for transmission
                        transmission = self.random.random() * modifier

                        if transmission > 1 - self.model.transmission_risk_employee_patient:
                            p.contact_to_infected = True
                            self.transmissions += 1
                            self.transmission_targets.update({self.model.Nstep:p.ID})
                            if self.verbose > 0:
                                print('transmission: employee {} -> patient {}'
                                      .format(self.unique_id, p.unique_id))

                # transmission from employees to employees
                for e in employees:
                    if (e.exposed == False) and (e.infected == False) and\
                       (e.recovered == False) and (e.contact_to_infected == False):
                        transmission = self.random.random()* modifier

                        if transmission > 1 - self.model.transmission_risk_employee_employee:
                            e.contact_to_infected = True
                            self.transmissions += 1
                            self.transmission_targets.update({self.model.Nstep:e.ID})
                            if self.verbose > 0:
                                print('transmission: employee {} -> employee {}'
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
            # determine if employee shows symptoms
            if self.symptomatic_course and self.days_infected >= self.model.time_until_symptoms and\
                    self.days_infected < self.model.infection_duration:
                self.symptoms = True
            # determine if employee has recovered
            if self.days_infected >= self.model.infection_duration:
                self.infected = False
                self.symptoms = False
                self.recovered = True
                if self.verbose > 0:
                    print('employee recovered: {}'.format(self.unique_id))
            else:
                self.days_infected += 1

        # determine if employee is testable
        if (self.infected == True) and (self.days_infected >= self.model.time_until_symptoms and
                                        (self.days_infected) <= self.model.time_testable):
            if self.testable == False:
                if self.verbose > 0:
                    if self.symptomatic_course:
                        print('employee {} testable (symptoms)'.format(
                            self.unique_id))
                    else:
                        print('employee {} testable (no symptoms)'.format(
                            self.unique_id))
                self.testable = True
        else:
            self.testable = False

        # determine if employee has transitioned from exposed to infected
        if self.exposed:
            if self.days_exposed >= self.model.exposure_duration:
                if self.verbose > 0:
                    print('employee infectious: {}'.format(self.unique_id))
                self.exposed = False
                self.infected = True
                # determine if infected employee shows symptoms
                if self.random.random() <= self.model.symptom_probability:
                    self.symptomatic_course = True
            else:
                self.days_exposed += 1

        # determine if employee is released from quarantine
        if self.quarantined:
            if self.days_quarantined >= self.model.quarantine_duration:
                if self.verbose > 0:
                    print('employee released from quarantine: {}'.format(
                        self.unique_id))
                self.quarantined = False
            else:
                self.days_quarantined += 1

        # determine if a transmission to the infected occurred
        if self.contact_to_infected == True:
            if self.verbose > 0:
                print('employee exposed: {}'.format(self.unique_id))
            self.exposed = True
            self.contact_to_infected = False
