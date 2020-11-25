from agent_SEIRX import agent_SEIRX



class resident(agent_SEIRX):
    '''
    An inhabitant with an infection status
    '''

    def __init__(self, unique_id, unit, model, 
            exposure_duration, time_until_symptoms, infection_duration,
            verbosity):

        super().__init__(unique_id, unit, model, 
            exposure_duration, time_until_symptoms, infection_duration,
            verbosity)

        self.type = 'resident'
        self.index_probability = self.model.index_probabilities[self.type]

        self.transmission_risk = self.model.transmission_risks[self.type]
        self.reception_risk = self.model.reception_risks[self.type]
        

    def step(self):
        '''
        Infection step: if a resident is infected and not in quarantine, it 
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
                residents = self.get_resident_resident_contacts()
                employees = self.get_resident_employee_contacts()

                # code transmission to residents and transmission to employees
                # separately to allow for differences in transmission risk
                self.transmit_infection(residents, 
                    self.transmission_risk, modifier)
                self.transmit_infection(employees, 
                    self.transmission_risk, modifier)


    def get_resident_employee_contacts(self):
        # only contacts to employees in the same unit are possible
        contacts = [a for a in self.model.schedule.agents if
            (a.type == 'employee' and a.unit == self.unit)]
        return contacts

    def get_resident_resident_contacts(self):
        # resident <-> resident contacts are determined by the contact network
        # get a list of neighbor IDs from the interaction network
        contacts = [tup[1] for tup in list(self.model.G.edges(self.ID))]
        # get the neighboring agents from the scheduler using their IDs
        contacts = [a for a in self.model.schedule.agents if a.ID in contacts]
        return contacts


