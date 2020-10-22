class Testing():
	def __init__(self, model, follow_up_testing_interval, screening_interval_patients, 
		screening_interval_employees, verbosity):
		self.follow_up_testing_interval = follow_up_testing_interval
		self.screening_interval_patients = screening_interval_patients
		self.screening_interval_employees = screening_interval_employees
		self.model = model
		self.verbosity = verbosity
		self.K1_areas = ['zimmer', 'tisch']

