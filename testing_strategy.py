class Testing():
	def __init__(self, model, interval, verbosity):
		self.interval = interval
		self.model = model
		self.verbosity = verbosity
		self.K1_areas = ['zimmer', 'tisch']

	def screen(self, target='employee'):
		screening_targets = [a for a in self.model.schedule.agents if a.type == target]
		cases = 0
		for t in screening_targets:
			if t.testable:
				t.quarantined = True
				cases += 1
				if self.verbosity > 0: print('found infection!')

		return cases
