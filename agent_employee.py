from mesa import Agent

class Employee(Agent):
    '''
    A patient with a health status
    '''
    def __init__(self, unique_id, model, verbosity):
        super().__init__(unique_id, model)
        self.verbose = verbosity
        self.ID = unique_id
        self.type = 'employee'

        # infection states
        self.exposed = False
        self.infected = False
        self.recovered = False
        self.testable = False
        self.quarantined = False

        # staging states
        self.contact_to_infected = False

        # counters
        self.days_exposed = 0
        self.days_infected = 0
        self.days_quarantined = 0
        self.transmissions = 0

    def step(self):
        '''
        Infection step: if an employee is infected, it iterates through all
        other employees and patients and tries to infect them. Infections
        are staged and only applied in the "advance"-step
        '''
        # check for external infection
        if (self.infected == False) and (self.exposed == False) and\
           (self.recovered == False):
            index_transmission = self.random.random()
            if index_transmission <= self.model.index_probability:
                self.contact_to_infected = True
                if self.verbose > 0:
                    print('employee {} is index case'.format(self.unique_id))

        if self.infected:
            # determine if patient is in quarantine
            if not self.quarantined:
                # get a list of patients
                patients = [a for a in self.model.schedule.agents if a.type == 'patient']
                # get a list of employees
                employees = [a for a in self.model.schedule.agents if a.type == 'employee']

                # code transmission to employees and transmission to patients separately
                # to allow for differences in transmissions later

                # transmission from patients to patients
                for p in patients:
                    if (p.exposed == False) and (p.infected == False) and \
                       (p.recovered == False) and (p.contact_to_infected == False):
                        # draw random number for transmission
                        transmission = self.random.random()
                        
                        if self.verbose > 1: 
                            print('checking gransmission from employee {} to patient {}'\
                                .format(self.unique_id, p.unique_id))
                            print('tranmission prob {}'.format(transmission))
                        if transmission <= self.model.transmission_risk_employee_patient:
                            p.contact_to_infected = True
                            self.transmissions += 1
                            if self.verbose > 0: print('transmission: employee {} -> patient {}'\
                                .format(self.unique_id, p.unique_id))

                # transmission from employees to employees
                for e in employees:
                    if (e.exposed == False) and (e.infected == False) and\
                       (e.recovered == False) and (e.contact_to_infected == False):
                        transmission = self.random.random()

                        if self.verbose > 1: 
                            print('checking gransmission from employee {} to employee {}'\
                                .format(self.unique_id, e.unique_id))
                            print('tranmission prob {}'.format(transmission))
                        if transmission <= self.model.transmission_risk_employee_employee:
                            e.contact_to_infected = True
                            self.transmissions += 1
                            if self.verbose > 0: print('transmission: employee {} -> patient {}'\
                                .format(self.unique_id, e.unique_id))

        '''
        Advancing step: applies infections, checks counters and sets infection 
        states accordingly
        '''
    def advance(self):
        if self.infected:
            # determine if employee has recovered
            if self.days_infected >= self.model.infection_duration:
                self.infected = False
                self.recovered = True
                if self.verbose > 0: print('employee recovered {}'.format(self.unique_id))
            else:
                self.days_infected += 1

        # determine if employee is testable
        if (self.infected == True) and (self.days_infected >= self.model.time_until_testable and\
           (self.days_infected) <= self.model.time_testable):
            if self.verbose > 0: print('employee testable {}'.format(self.unique_id))
            self.testable = True
        else:
            self.testable = False

        # determine if employee has transitioned from exposed to infected
        if self.exposed:
            if self.days_exposed >= self.model.exposure_duration:
                if self.verbose > 0: print('employee infected {}'.format(self.unique_id))
                self.exposed = False
                self.infected = True
            else:
                self.days_exposed += 1

        # determine if employee is released from quarantine
        if self.quarantined:
            if self.days_quarantined >= self.model.quarantine_duration:
                if self.verbose > 0: print('employee released from quarantine {}'.format(self.unique_id))
                self.quarantined = False
            else:
                self.days_quarantined += 1

        # determine if a transmission to the infected occurred
        if self.contact_to_infected == True:
            if self.verbose > 0: print('employee exposed: {}'.format(self.unique_id))
            self.exposed = True
            self.contact_to_infected = False
    