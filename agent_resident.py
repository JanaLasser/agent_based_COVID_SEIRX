from agent_SEIRX import agent_SEIRX


# NOTE: "residents" and "inhabitants" are used interchangeably in the documentation


class resident(agent_SEIRX):
    '''
    An inhabitant with an infection status
    '''

    def __init__(self, unique_id, quarter, model, verbosity):
        super().__init__(unique_id, quarter, model, verbosity)
        self.type = 'resident'
        self.index_probability = self.model.index_probability_resident
        

    def step(self):
        '''
        Infection step: if a resident is infected and not in quarantine, it 
        iterates through all other residents and employees tries to 
        infect them. Infections are staged here and only applied in the 
        "advance"-step to simulate "simultaneous" interaction
        '''
        # check for external infection in continuous index case modes
        if self.model.index_case_mode in ['continuous_resident',\
                                          'continuous_both']:
            self.introduce_external_infection()

        # simulate contacts to other employees and residents if the agent is
        # infected and not in quarantine. Randomly transmit the infection 
        # according to the transmission risk
        if self.infectious:
            if not self.quarantined:
                # infectiousness is constant and high during the first 2 days 
                # (pre-symptomatic) and then decreases monotonically for 8 days 
                # until agents are not infectious anymore 10 days after the 
                # onset of infectiousness
                modifier = 1 - max(0, self.days_since_exposure - self.model.exposure_duration - 1) / 10

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
                    self.model.transmission_risk_resident_resident, modifier)
                self.transmit_infection(employees, 
                    self.model.transmission_risk_resident_employee, modifier)