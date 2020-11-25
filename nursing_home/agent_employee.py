from agent_SEIRX import agent_SEIRX



class employee(agent_SEIRX):
    '''
    An employee with an infection status
    '''

    def __init__(self, unique_id, unit, model, 
            exposure_duration, time_until_symptoms, infection_duration,
            verbosity):

        super().__init__(unique_id, unit, model, 
            exposure_duration, time_until_symptoms, infection_duration,
            verbosity)

        self.type = 'employee'
        self.index_probability = self.model.index_probabilities[self.type]

        self.transmission_risk = self.model.transmission_risks[self.type]
        self.reception_risk = self.model.reception_risks[self.type]
        

    def step(self):
        '''
        Infection step: if an employee is infected and not in quarantine, it 
        iterates through all other residents and employees tries to 
        infect them. Infections are staged here and only applied in the 
        "advance"-step to simulate "simultaneous" interaction
        '''
        # check for external infection in continuous index case modes
        if self.model.index_case in ['continuous'] and \
           self.index_probability > 0:
	        self.introduce_external_infection()

        # simulate contacts to other employees and residents if the agent is
        # infected and not in quarantine. Randomly transmit the infection 
        # according to the transmission risk
        if self.infectious:
            if not self.quarantined:
                # infectiousness is constant and high during the first 2 days 
                # (pre-symptomatic) and then decreases monotonically until agents 
                # are not infectious anymore at the end of the infection_duration 
                modifier = 1 - max(0, self.days_since_exposure - self.exposure_duration - 1) / \
                    (self.infection_duration - self.exposure_duration - 1)

                # if infectiousness is modified for asymptomatic cases, multiply
                # the asymptomatic modifier with the days-infected modifier 
                if self.symptomatic_course == False:
                    modifier *= self.model.subclinical_modifier

                # get employee and resident contacts according to contact rules
                # and the interaction network
                residents = self.get_employee_resident_contacts()
                employees = self.get_employee_employee_contacts()

                # code transmission to residents and transmission to employees
                # separately to allow for differences in transmission risk
                self.transmit_infection(residents, 
                    self.transmission_risk, modifier)
                self.transmit_infection(employees, 
                    self.transmission_risk, modifier)


    def get_employee_resident_contacts(self):
        # only contacts to residents in the same unit are possible
        contacts = [a for a in self.model.schedule.agents if
            (a.type == 'resident' and a.unit == self.unit)]
        return contacts

    def get_employee_employee_contacts(self):
        # only contacts to employees in the same unit
        contacts = [a for a in self.model.schedule.agents if
            (a.type == 'employee' and a.unit == self.unit)]

        # TODO: implement random cross-unit interaction of employees
        # if self.model.employee_cross_unit_interaction:
        return contacts

