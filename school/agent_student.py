from agent_SEIRX import agent_SEIRX

class student(agent_SEIRX):
    '''
    A student with an infection status
    '''

    def __init__(self, unique_id, unit, model, verbosity):
        super().__init__(unique_id, unit, model, verbosity)
        self.type = 'student'
        self.index_probability = self.model.index_probabilities[self.type]

        self.age = model.G.nodes(data=True)[self.unique_id]['age']

        self.transmission_risk = self.age_adjust_risk(self.model.transmission_risks[self.type], self.age)
        self.reception_risk = self.age_adjust_risk(self.model.reception_risks[self.type], self.age)


    def age_adjust_risk(self, base_risk, age):
        '''linear interpolation such that at age 6 the risk is 50% and at age 18
        the risk is that of an adult (=base risk)'''
        max_age = 18
        min_age = 6
        risk = base_risk * (1 - (0.5- 1/((max_age - min_age) * 2) * (age - 6)))
        return risk
            

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

                # infectiousness is constant and high during the first 2 days 
                # (pre-symptomatic) and then decreases monotonically for 8 days 
                # until agents are not infectious anymore 10 days after the 
                # onset of infectiousness
                modifier = 1 - max(0, self.days_since_exposure - self.model.exposure_duration - 1) / 10

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

