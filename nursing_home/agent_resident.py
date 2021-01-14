from agent_SEIRX import agent_SEIRX



class resident(agent_SEIRX):
    '''
    An inhabitant with an infection status
    '''

    def __init__(self, unique_id, unit, model, 
            exposure_duration, time_until_symptoms, infection_duration,
            verbosity):

        self.type = 'resident'

        super().__init__(unique_id, unit, model, 
            exposure_duration, time_until_symptoms, infection_duration,
            verbosity)
        

    def step(self):
        '''
        Infection step: if a teacher is infected and not in quarantine, it 
        interacts with other students and teachers trough the specified 
        contact network and can pass a potential infection.
        Infections are staged here and only applied in the 
        "advance"-step to simulate "simultaneous" interaction
        '''

        # check for external infection in continuous index case modes
        if self.model.index_case in ['continuous'] and \
           self.index_probability > 0:
            self.introduce_external_infection()

        # simulate contacts to other agents if the agent is
        # infected and not in quarantine. Randomly transmit the infection 
        # according to the transmission risk
        if self.infectious:
            if not self.quarantined:

                # get contacts to other agent groups according to the
                # interaction network
                employees = self.get_contacts('employee')
                residents = self.get_contacts('resident')

                # code transmission to other agent groups
                # separately to allow for differences in transmission risk
                self.transmit_infection(employees)
                self.transmit_infection(residents)


