from agent_SEIRX import agent_SEIRX

class student(agent_SEIRX):
    '''
    A student with an infection status
    '''

    def __init__(self, unique_id, unit, model, 
        exposure_duration, time_until_symptoms, infection_duration,
        verbosity):

        self.type = 'student'

        super().__init__(unique_id, unit, model, 
            exposure_duration, time_until_symptoms, infection_duration,
            verbosity)

        self.age = model.G.nodes(data=True)[self.unique_id]['age']
        

        ## age adjustments
        # adjust symptom probability based on age
        self.symptom_probability = \
                        self.age * self.model.age_symptom_discount['slope'] + \
                        self.symptom_probability

        # modulate transmission and reception risk based on age 
        age_modifier = model.get_risk_age_modifier(self.age)
        self.transmission_risk = self.transmission_risk * age_modifier
        self.reception_risk = self.reception_risk * age_modifier

            

    def step(self):
        '''
        Infection step: if a student is infected and not in quarantine, it 
        interacts with other students, family members and teachers trough 
        the specified contact network and can pass a potential infection.
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

                # infectiousness is constant and high until symptom onset and then
                # decreases monotonically until agents are not infectious anymore 
                # at the end of the infection_duration 
                modifier = self.get_transmission_risk_time_modifier()

                # if infectiousness is modified for asymptomatic cases, multiply
                # the asymptomatic modifier with the days-infected modifier 
                if self.symptomatic_course == False:
                    modifier *= self.model.subclinical_modifier

                # TODO: add modification for student age

                # get contacts to other agent groups according to the
                # interaction network
                family_members = self.get_contacts('family_member')
                teachers = self.get_contacts('teacher')
                students = self.get_contacts('student')

                # code transmission to other agent groups
                # separately to allow for differences in transmission risk
                self.transmit_infection(family_members, 
                    self.transmission_risk, modifier)
                self.transmit_infection(teachers, 
                    self.transmission_risk, modifier)
                self.transmit_infection(students, 
                    self.transmission_risk, modifier)

