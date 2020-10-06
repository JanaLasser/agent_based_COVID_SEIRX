from mesa import Agent

class Patient(Agent):
    '''
    A patient with a health status
    '''
    def __init__(self, unique_id, model, verbosity):
        super().__init__(unique_id, model)
        self.exposed = False
        self.infected = False
        self.recovered = False
        self.days_exposed = 0
        self.days_infected = 0
        self.transmissions = 0
        self.verbose = verbosity
        
    def step(self):
        #print('Activated patient {}'.format(self.unique_id))
        if self.exposed:
            if self.verbose > 0: print('exposed: {}'.format(self.unique_id))
            if self.days_exposed >= self.model.exposure_duration:
                if self.verbose > 0: print('infected {}'.format(self.unique_id))
                self.exposed = False
                self.infected = True
            else:
                self.days_exposed += 1
            
        
        if self.infected:
            # check if the patient has already recovered
            if self.days_infected >= self.model.infection_duration:
                self.infected = False
                self.recovered = True
                if self.verbose > 0: print('recovered {}'.format(self.unique_id))
                return
            
            for a in self.model.schedule.agents:
                if (a.exposed == False) and (a.infected == False) and \
                   (a.recovered == False):
                    transmission = self.random.random()
                    if self.verbose > 1: 
                        print('checking gransmission from {} to {}'.format(self.unique_id, a.unique_id))
                        print('tranmission prob {}'.format(transmission))
                    if transmission <= self.model.infection_risk:
                        a.exposed = True
                        self.transmissions += 1
                        if self.verbose > 0: print('transmission: from {} to {}'.format(self.unique_id, a.unique_id))
                    
            self.days_infected += 1
            
        