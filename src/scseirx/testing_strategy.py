def check_test_type(var, tests):
	if var != None:
		assert type(var) == str, 'not a string'
		assert var in tests.keys(), 'unknown test type {}'.format(var)
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

        # in the following dictionary, the parameters "time_until_testable" and
        # "time_testable" refer to a shift (in days) as compared to an agent's
        # individual exposure_duration and infection_duration. For example, if
        # an agent has an exposure duration of 5 days and an infection duration
        # of 11 days, a "same_day_antigen" Test will be able to detect an
        # infection after 5 + time_until_testable = 7 days. It will also be able
        # to detect an infection for as long as 11 + time_testable = 10 days.
        # The values chosen for the different test technologies here reflect
        # their detection thresholds with respect to viral load.
		self.tests = {
		'same_day_antigen':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.1':
	     {
	         'sensitivity':0.1,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.2':
	     {
	         'sensitivity':0.2,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.3':
	     {
	         'sensitivity':0.3,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.4':
	     {
	         'sensitivity':0.4,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.5':
	     {
	         'sensitivity':0.5,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.6':
	     {
	         'sensitivity':0.6,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.7':
	     {
	         'sensitivity':0.7,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.8':
	     {
	         'sensitivity':0.8,
	         'specificity':1,
	         'time_until_testable': 2,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
	     'same_day_antigen0.9':
	     {
	         'sensitivity':0.9,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':0
	     },
		'one_day_antigen':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':1
	     },
		'two_day_antigen':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable': 1,
	         'time_testable': -1,
	         'time_until_test_result':2
	     },
	     'same_day_PCR':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable': - 1,
	         'time_testable': 0,
	         'time_until_test_result':0
	     },
	     'one_day_PCR':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable': - 1,
	         'time_testable':0,
	         'time_until_test_result':1
	     },
	      'two_day_PCR':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable': - 1,
	         'time_testable':0,
	         'time_until_test_result':2
	     },
	    'same_day_LAMP':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':0,
	         'time_testable':0,
	         'time_until_test_result':0
	     },
	    'one_day_LAMP':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':0,
	         'time_testable':0,
	         'time_until_test_result':1
	     },
	    'two_day_LAMP':
	     {
	         'sensitivity':1,
	         'specificity':1,
	         'time_until_testable':0,
	         'time_testable':0,
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




