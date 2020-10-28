def check_test_type(var):
	assert type(var) == str, 'not a string'
	assert var in tests.keys(), 'unknown test type'
	return var

tests = {'antigen_NADAL':
         {
             'sensitivity':0.9756,
             'specificity':0.999
         },
         'antigen_ROCHE':
         {
             'sensitivity':0.9652,
             'specificity':0.9968
         },
         'antigen_ABBOT':
         {
             'sensitivity':0.971,
             'specificity':0.985
         },
         # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7350782/
        'PCR_throat_swab':
         {
             'sensitivity':0.733, 
             'specificity':1
         },
        'PCR_sputum':
         {
             'sensitivity':0.972, 
             'specificity':1
         },
        'PCR_salvia':
         {
             'sensitivity':0.623, 
             'specificity':1
         },
         # https://abbott.mediaroom.com/2020-10-07-Abbott-Releases-ID-NOW-TM-COVID-19-Interim-Clinical-Study-Results-from-1-003-People-to-Provide-the-Facts-on-Clinical-Performance-and-to-Support-Public-Health#:~:text=ID%20NOW%20demonstrated%2079.8%25%20positive,lab%2Dbased%20molecular%20PCR%20tests.
        'LAMP_ABBOT':
         {
             'sensitivity':0.798,
             'specificity':0.943
         }
        }


class Testing():
	def __init__(self, model, test_type, time_until_test_result, follow_up_testing_interval,
		screening_interval_patients, screening_interval_employees, K1_areas, verbosity):

		self.follow_up_testing_interval = follow_up_testing_interval
		self.screening_interval_patients = screening_interval_patients
		self.screening_interval_employees = screening_interval_employees
		self.model = model
		self.verbosity = verbosity
		self.K1_areas = K1_areas
		self.time_until_test_result = time_until_test_result
		self.test_type = check_test_type(test_type)
		self.sensitivity = tests[self.test_type]['sensitivity']
		self.specificity = tests[self.test_type]['specificity']




# antigentests
# https://antigentest.bfarm.de/ords/antigen/r/antigentests-auf-sars-cov-2/liste-der-antigentests?session=23281379113534&tz=1:00


