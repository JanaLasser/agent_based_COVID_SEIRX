class Testing():
	def __init__(self, model, interval, target, verbosity):
		self.interval = interval
		self.target = target
		self.model = model
		self.verbosity = verbosity

	def screen(self):
		screening_targets = [a for a in self.model.schedule.agents if a.type == self.target]
		for t in screening_targets:
			if t.testable:
				t.quarantined = True
				if self.verbosity > 0: print('found infection!')
