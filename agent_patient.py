from mesa import Agent


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
        self.recovered = False
        self.testable = False

        # staging states
        self.contact_to_infected = False

        # counters
        self.days_exposed = 0
        self.days_infected = 0
        self.transmissions = 0
        

    def step(self):
        '''
        Infection step: if a patient is infected, it iterates through all
        other patients it has contact with and tries to infect them. Infections
        are staged and only applied in the "advance"-step
        '''
        if self.infected:
            # get a list of neighbor IDs from the interaction network
            neighbors = [tup[1] for tup in list(self.model.G.edges(self.ID))]
            # get the neighboring agents from the scheduler using their IDs
            neighbors = [a for a in self.model.schedule.agents if a.ID in neighbors]

            for a in neighbors:
                if (a.exposed == False) and (a.infected == False) and \
                   (a.recovered == False) and (a.contact_to_infected == False):
                    # draw random number for transmission
                    transmission = self.random.random()
                    # get link strength from the interaction network
                    transmission = transmission * self.model.G[self.ID][a.ID]['weight']

                    if self.verbose > 1: 
                        print('checking gransmission from {} to {}'\
                            .format(self.unique_id, a.unique_id))
                        print('tranmission prob {}'.format(transmission))
                    if transmission <= self.model.infection_risk:
                        a.contact_to_infected = True
                        self.transmissions += 1
                        if self.verbose > 0: print('transmission: {} -> {}'\
                            .format(self.unique_id, a.unique_id))

    '''
    Advancing step: applies infections, checks counters and sets infection 
    states accordingly
    '''
    def advance(self):
        if self.infected:
            # determine if patient is testable
            if (self.days_infected >= self.model.time_until_testable and\
               (self.days_infected) <= self.model.time_testable):
                self.testable = True

            # determine if patient has recovered
            if self.days_infected >= self.model.infection_duration:
                self.infected = False
                self.recovered = True
                if self.verbose > 0: print('recovered {}'.format(self.unique_id))
            else:
                self.days_infected += 1

        # determine if patient has transitioned from exposed to infected
        if self.exposed:
            if self.verbose > 0: print('exposed: {}'.format(self.unique_id))
            if self.days_exposed >= self.model.exposure_duration:
                if self.verbose > 0: print('infected {}'.format(self.unique_id))
                self.exposed = False
                self.infected = True
            else:
                self.days_exposed += 1

        # determine if a transmission to the infected occurred
        if self.contact_to_infected == True:
            self.exposed = True
            self.contact_to_infected = False


            


            


            
        