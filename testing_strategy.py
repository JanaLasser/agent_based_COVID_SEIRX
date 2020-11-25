def check_test_type(var, tests):
	if var != None:
		assert type(var) == str, 'not a string'
		assert var in tests.keys(), 'unknown test type'
	return var



class Testing():
	def __init__(self, model, diagnostic_test_type, 
		preventive_screening_test_type, follow_up_testing_interval,
		screening_intervals, liberating_testing, 
		K1_contact_types, verbosity):

		self.follow_up_testing_interval = follow_up_testing_interval
		self.screening_intervals = screening_intervals
		self.liberating_testing = liberating_testing
		self.model = model
		self.verbosity = verbosity
		self.K1_contact_types = K1_contact_types

		# mean parameters for exposure and infection duration to base
		# estimates for test detection thresholds on
		exposure_duration = 4
		infection_duration = 11

		self.tests = {
		'same_day_antigen':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':exposure_duration + 2,
	         'time_testable':exposure_duration + 6,
	         'time_until_test_result':0
	     },
		'one_day_antigen':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':exposure_duration + 2,
	         'time_testable':exposure_duration + 6,
	         'time_until_test_result':1
	     },
		'two_day_antigen':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':exposure_duration + 2,
	         'time_testable':exposure_duration + 6,
	         'time_until_test_result':2
	     },
	     'same_day_PCR':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':4,
	         'time_testable':infection_duration,
	         'time_until_test_result':0
	     },
	     'one_day_PCR':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':4,
	         'time_testable':infection_duration,
	         'time_until_test_result':1
	     },
	      'two_day_PCR':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':4,
	         'time_testable':infection_duration,
	         'time_until_test_result':2
	     },
	    'same_day_LAMP':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':exposure_duration,
	         'time_testable':infection_duration,
	         'time_until_test_result':0
	     },
	    'one_day_LAMP':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':exposure_duration,
	         'time_testable':infection_duration,
	         'time_until_test_result':1
	     },
	    'two_day_LAMP':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':exposure_duration,
	         'time_testable':infection_duration,
	         'time_until_test_result':2
	     }
	    }

		self.diagnostic_test_type = check_test_type(diagnostic_test_type, self.tests)
		self.preventive_screening_test_type = check_test_type(preventive_screening_test_type, self.tests)
		#self.sensitivity = self.tests[self.test_type]['sensitivity']
		#self.specificity = self.tests[self.test_type]['specificity']
		#self.time_until_testable = self.tests[self.test_type]['time_until_testable']
		#self.time_testable = self.tests[self.test_type]['time_testable']
		#self.time_until_test_result = self.tests[self.test_type]['time_until_test_result']




