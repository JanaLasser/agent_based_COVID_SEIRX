from agent_SEIRX import agent_SEIRX

class teacher(agent_SEIRX):
    '''
    A teacher with an infection status
    '''

    def __init__(self, unique_id, unit, model, 
        exposure_duration, time_until_symptoms, infection_duration,
        verbosity):

        self.type = 'teacher'

        super().__init__(unique_id, unit, model, 
            exposure_duration, time_until_symptoms, infection_duration,
            verbosity) 

        self.age = 30


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
                family_members = self.get_contacts('family_member')
                teachers = self.get_contacts('teacher')
                students = self.get_contacts('student')

                # code transmission to other agent groups
                # separately to allow for differences in transmission risk
                self.transmit_infection(family_members)
                self.transmit_infection(teachers)
                self.transmit_infection(students)