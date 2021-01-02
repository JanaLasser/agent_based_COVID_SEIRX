import numpy as np
np.random.seed(42)

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import networkx as nx
import pandas as pd
import scipy as sp
from scipy.stats import lognorm
from scipy.optimize import root_scalar
from scipy.special import gamma
import numpy as np
from os.path import join

# agent based model classes & functionality
import sys
sys.path.insert(0,'../school')
sys.path.insert(0,'../nursing_home')
from model_school import SEIRX_school
import analysis_functions as af



target_base_transmission_risk = 0.0737411844049918

def calculate_distribution_difference(school_type, ensemble_results):
    '''
    Calculates the difference between the expected distribution of outbreak
    sizes and the observed outbreak sizes in an ensemble of simulation runs
    with the same parameters. The data-frame ensemble_results holds the number
    of infected students and the number of infected teachers. NOTE: the index
    case is already subtracted from these numbers.
    '''
    # calculate the total number of follow-up cases (outbreak size)
    ensemble_results['infected_total'] = ensemble_results['infected_teachers'] +\
                    ensemble_results['infected_students']
    
    ensemble_results = ensemble_results.astype(int)
    
    # censor runs with no follow-up cases as we also do not observe these in the
    # empirical data
    ensemble_results = ensemble_results[ensemble_results['infected_total'] > 0].copy()
    observed_outbreaks = ensemble_results['infected_total'].value_counts()
    observed_outbreaks = observed_outbreaks / observed_outbreaks.sum()
    obs_dict = {size:ratio for size, ratio in zip(observed_outbreaks.index,
                                                   observed_outbreaks.values)}
    
    # since we only have aggregated data for schools with and without daycare,
    # we map the daycare school types to their corresponding non-daycare types,
    # which are also the labels of the schools in the emirical data
    type_map = {'primary':'primary', 'primary_dc':'primary',
                'lower_secondary':'lower_secondary',
                'lower_secondary_dc':'lower_secondary',
                'upper_secondary':'upper_secondary',
                'secondary':'secondary', 'secondary_dc':'secondary'}
    school_type = type_map[school_type]
    
    expected_outbreaks = pd.read_csv(\
                        '../data/school/calibration_data/outbreak_sizes.csv')
    expected_outbreaks = expected_outbreaks[\
                            expected_outbreaks['type'] == school_type].copy()
    expected_outbreaks.index = expected_outbreaks['size']
    
    exp_dict = {s:c for s, c in zip(expected_outbreaks.index, 
                                     expected_outbreaks['ratio'])}
    
    # add zeroes for both the expected and observed distributions in cases 
    # (sizes) that were not observed
    if len(observed_outbreaks) == 0:
        obs_max = 0
    else:
        obs_max = observed_outbreaks.index.max()
    
    for i in range(1, max(obs_max + 1,
                          expected_outbreaks.index.max() + 1)):
        if i not in observed_outbreaks.index:
            obs_dict[i] = 0
        if i not in expected_outbreaks.index:
            exp_dict[i] = 0
            
    obs = np.asarray([obs_dict[i] for i in range(1, len(obs_dict) + 1)])
    exp = np.asarray([exp_dict[i] for i in range(1, len(exp_dict) + 1)])
    
    chi2_distance = ((exp + 1) - (obs + 1))**2 / (exp + 1)
    chi2_distance = chi2_distance.sum()
    
    sum_of_squares = ((exp - obs)**2).sum()
    
    return chi2_distance, sum_of_squares

def calculate_group_case_difference(school_type, ensemble_results):
    '''
    Calculates the difference between the expected number of infected teachers
    / infected students and the observed number of infected teachers / students
    in an ensemble of simulation runs with the same parameters. The data-frame 
    ensemble_results holds the number of infected students and the number of 
    infected teachers. NOTE: the index case is already subtracted from these
    numbers.
    '''
    
    # calculate the total number of follow-up cases (outbreak size)
    ensemble_results['infected_total'] = ensemble_results['infected_teachers'] +\
                    ensemble_results['infected_students']
    
    # censor runs with no follow-up cases as we also do not observe these in the
    # empirical data
    ensemble_results = ensemble_results[ensemble_results['infected_total'] > 0].copy()
    
    # calculate ratios of infected teachers and students
    ensemble_results['teacher_ratio'] = ensemble_results['infected_teachers'] / \
                                        ensemble_results['infected_total'] 
    ensemble_results['student_ratio'] = ensemble_results['infected_students'] / \
                                        ensemble_results['infected_total'] 
    
    observed_distro = pd.DataFrame({'group':['student', 'teacher'],
                                    'ratio':[ensemble_results['student_ratio'].mean(),
                                             ensemble_results['teacher_ratio'].mean()]})

    # since we only have aggregated data for schools with and without daycare,
    # we map the daycare school types to their corresponding non-daycare types,
    # which are also the labels of the schools in the emirical data
    type_map = {'primary':'primary', 'primary_dc':'primary',
                'lower_secondary':'lower_secondary',
                'lower_secondary_dc':'lower_secondary',
                'upper_secondary':'upper_secondary',
                'secondary':'secondary', 'secondary_dc':'secondary'}
    school_type = type_map[school_type]
    
    expected_distro = pd.read_csv(\
                        '../data/school/calibration_data/group_distributions.csv')
    expected_distro = expected_distro[\
                                expected_distro['type'] == school_type].copy()
    expected_distro.index = expected_distro['group']
    
    obs = observed_distro['ratio'].values
    exp = expected_distro['ratio'].values
    
    chi2_distance = ((exp + 1) - (obs + 1))**2 / (exp + 1)
    chi2_distance = chi2_distance.sum()
    
    sum_of_squares = ((exp - obs)**2).sum()
    
    return chi2_distance, sum_of_squares


# empirically observed index case ratios for different school types
agent_index_ratios = {
    'primary':            {'teacher':0.939394, 'student':0.060606},
    'primary_dc':         {'teacher':0.939394, 'student':0.060606},
    'lower_secondary':    {'teacher':0.568, 'student':0.432},
    'lower_secondary_dc': {'teacher':0.568, 'student':0.432},
    'upper_secondary':    {'teacher':0.182796, 'student':0.817204},
    'secondary':          {'teacher':0.362319, 'student':0.637681},
    'secondary_dc':       {'teacher':0.362319, 'student':0.637681},
}

# intercept: ratio of symptomatic courses for adults (at age >= 20.5)
# slope: reduction of the ratio of symptomatic courses for every year an
# agent is younger than 20.5. Values stem from a fit to empirical data of
# symptomatic courses stratified by age group (see script calibration_info.ipynb)
age_symptom_discount = {'slope':-0.02868, 'intercept':0.7954411542069012}

# List of prevention measures that were in place in schools in the weeks 36-45
# of the year 2020 in Austrian schools. This list was compiled from information
# collected in interviews with teachers of different school types. NOTE: so far
# there are no recorded differences between school types.
prevention_measures = {
    'primary':     
                   {'testing':'diagnostic', 
                    'follow_up_testing_interval':None,
                    'diagnostic_test_type':'two_day_PCR',
                    'preventive_screening_test_type':None,
                    'student_screen_interval':None,
                    'teacher_screen_interval':None,
                    'family_member_screen_interval':None,
                    'K1_contact_types':['intermediate', 'close'],
                    'quarantine_duration':10,
                    'half_classes':False,
                    'teacher_mask':False,
                    'student_mask':False,
                    'family_member_mask':False,
                    'student_index_probability':0,
                    'teacher_index_probability':0,
                    'family_member_index_probability':0,
                    'liberating_testing':False
                    },
    'primary_dc':     
                   {'testing':'diagnostic', 
                    'follow_up_testing_interval':None,
                    'diagnostic_test_type':'two_day_PCR',
                    'preventive_screening_test_type':None,
                    'student_screen_interval':None,
                    'teacher_screen_interval':None,
                    'family_member_screen_interval':None,
                    'K1_contact_types':['intermediate', 'close'],
                    'quarantine_duration':10,
                    'half_classes':False,
                    'teacher_mask':False,
                    'student_mask':False,
                    'family_member_mask':False,
                    'student_index_probability':0,
                    'teacher_index_probability':0,
                    'family_member_index_probability':0,
                    'liberating_testing':False
                    },
    'lower_secondary':
                   {'testing':'diagnostic', 
                    'follow_up_testing_interval':None,
                    'diagnostic_test_type':'two_day_PCR',
                    'preventive_screening_test_type':None,
                    'student_screen_interval':None,
                    'teacher_screen_interval':None,
                    'family_member_screen_interval':None,
                    'K1_contact_types':['intermediate', 'close'],
                    'quarantine_duration':10,
                    'half_classes':False,
                    'teacher_mask':False,
                    'student_mask':False,
                    'family_member_mask':False,
                    'student_index_probability':0,
                    'teacher_index_probability':0,
                    'family_member_index_probability':0,
                    'liberating_testing':False
                    },
    'lower_secondary_dc':
                   {'testing':'diagnostic', 
                    'follow_up_testing_interval':None,
                    'diagnostic_test_type':'two_day_PCR',
                    'preventive_screening_test_type':None,
                    'student_screen_interval':None,
                    'teacher_screen_interval':None,
                    'family_member_screen_interval':None,
                    'K1_contact_types':['intermediate', 'close'],
                    'quarantine_duration':10,
                    'half_classes':False,
                    'teacher_mask':False,
                    'student_mask':False,
                    'family_member_mask':False,
                    'student_index_probability':0,
                    'teacher_index_probability':0,
                    'family_member_index_probability':0,
                    'liberating_testing':False
                    },
    'upper_secondary':
                   {'testing':'diagnostic', 
                    'follow_up_testing_interval':None,
                    'diagnostic_test_type':'two_day_PCR',
                    'preventive_screening_test_type':None,
                    'student_screen_interval':None,
                    'teacher_screen_interval':None,
                    'family_member_screen_interval':None,
                    'K1_contact_types':['intermediate', 'close'],
                    'quarantine_duration':10,
                    'half_classes':False,
                    'teacher_mask':False,
                    'student_mask':False,
                    'family_member_mask':False,
                    'student_index_probability':0,
                    'teacher_index_probability':0,
                    'family_member_index_probability':0,
                    'liberating_testing':False
                    },
    'secondary':
                   {'testing':'diagnostic', 
                    'follow_up_testing_interval':None,
                    'diagnostic_test_type':'two_day_PCR',
                    'preventive_screening_test_type':None,
                    'student_screen_interval':None,
                    'teacher_screen_interval':None,
                    'family_member_screen_interval':None,
                    'K1_contact_types':['intermediate', 'close'],
                    'quarantine_duration':10,
                    'half_classes':False,
                    'teacher_mask':False,
                    'student_mask':False,
                    'family_member_mask':False,
                    'student_index_probability':0,
                    'teacher_index_probability':0,
                    'family_member_index_probability':0,
                    'liberating_testing':False
                    },
    'secondary_dc':
                   {'testing':'diagnostic', 
                    'follow_up_testing_interval':None,
                    'diagnostic_test_type':'two_day_PCR',
                    'preventive_screening_test_type':None,
                    'student_screen_interval':None,
                    'teacher_screen_interval':None,
                    'family_member_screen_interval':None,
                    'K1_contact_types':['intermediate', 'close'],
                    'quarantine_duration':10,
                    'half_classes':False,
                    'teacher_mask':False,
                    'student_mask':False,
                    'family_member_mask':False,
                    'student_index_probability':0,
                    'teacher_index_probability':0,
                    'family_member_index_probability':0,
                    'liberating_testing':False
                    },
}

# characteristics of the "average" school, depending on school type. These 
# characteristics were determined in interviews with Austrian teachers and from
# statistics about Austrian schools 
# (year 2017/18, page 10: https://www.bmbwf.gv.at/Themen/schule/schulsystem/gd.html)
# NOTE: "students" indicates the number of students per class

school_characteristics = {
    # Volksschule: Schulen: 3033, Klassen: 18245, Schüler*innen: 339382
    'primary':            {'classes':8, 'students':19},
    'primary_dc':         {'classes':8, 'students':19},
    
    # Hauptschulen: 47, Klassen 104, Schüler*innen: 1993
    # Neue Mittelschule: Schulen 1131, Klassen: 10354, Schüler*innen: 205905
    # Sonderschulen: 292, Klassen: 1626, Schüler*innen: 14815
    # Gesamt: Schulen: 1470, Klassen: 12084, Schüler*innen: 222713
    'lower_secondary':    {'classes':8, 'students':18},
    'lower_secondary_dc': {'classes':8, 'students':18},
    
    # Oberstufenrealgymnasium: Schulen 114, Klassen 1183, Schüler*innen: 26211
    # BMHS: schulen 734, Klassen 8042, Schüler*innen 187592
    # Gesamt: Schulen: 848, Klassen 9225, Schüler*innen: 213803
    'upper_secondary':    {'classes':10, 'students':23}, # rounded down from 10.8 classes
    
    # AHS Langform: Schulen 281, Klassen 7610, schüler*innen 179633
    'secondary':          {'classes':28, 'students':24}, # rounded up from 27.1 classes
    'secondary_dc':       {'classes':28, 'students':24} # rounded up from 27.1 classes
}

school_types = ['primary', 'primary_dc', 'lower_secondary', 'lower_secondary_dc',
                'upper_secondary', 'secondary', 'secondary_dc']



def compose_agents(prevention_measures, transmission_risk, reception_risk):
    agent_types = {
            'student':{
                'screening_interval':prevention_measures['student_screen_interval'],
                'index_probability':prevention_measures['student_index_probability'],
                'transmission_risk':transmission_risk,
                'reception_risk':reception_risk},

            'teacher':{
                'screening_interval': prevention_measures['teacher_screen_interval'],
                'index_probability': prevention_measures['student_index_probability'],
                'transmission_risk':transmission_risk,
                'reception_risk':reception_risk},

            'family_member':{
                'screening_interval':prevention_measures['family_member_screen_interval'],
                'index_probability':prevention_measures['family_member_index_probability'],
                'transmission_risk':transmission_risk,
                'reception_risk':reception_risk}
    }
    
    return agent_types


# paths for data I/O
src = '../data/school/calibration_schools'
dst = '../data/school/calibration_results'


# set the simulation parameters that are not used in this investigation to
# default values
base_reception_risk = 1 # is adjusted by age for students
verbosity = 0 # only needed for debug output
subclinical_modifier = 0.6 # sublinical cases are 40% less infectious than symptomatic cases


## statistics parameters
# number of maximum steps per run. This is a very conservatively chosen value
# that ensures that an outbreak will always terminate within the allotted time.
# Most runs are terminated way earlier anyways, as soon as the outbreak is over.
N_steps = 1000 
# number of runs per ensemble
N_runs = int(sys.argv[3])
# number of points in the parameter grid that will be randomly sampled
N_samples = sys.argv[2]
if not N_samples == 'all':
	N_samples = int(N_samples)
school_type = sys.argv[1]

N_low = int(sys.argv[4])
N_high = int(sys.argv[5])


## grid of parameters that need to be calibrated
# the contact weight is the modifier by which the base transmission risk (for
# household transmissions) is multiplied for contacts of type "intermediate" 
# and of type "far"
intermediate_contact_weights = np.arange(0.1, 0.8, 0.02)

far_contact_weights = np.arange(0.1, 0.8, 0.02)

# the age_transmission_discount sets the slope of the age-dependence of the 
# transmission risk. Transmission risk for adults (age 18+) is always base 
# transmission risk. For every year an agent is younger than 18 years, the
# transmission risk is reduced
age_transmission_discounts = np.arange(-0.4, 0, 0.02)

# list of all possible parameter combinations from the grid
params = [(i, j, k) for i in intermediate_contact_weights \
                    for j in far_contact_weights\
                    for k in age_transmission_discounts if i > j]
# randomly drawn list of parameter combination indices of size N_samples. For 
# every parameter combination an ensemble of simulations will be run and 
# evaluated.

if N_samples == 'all':
    samples = range(len(params))
else:
    samples = np.random.choice(range(len(params)), N_samples, replace=False)

print('indices {} to {}'.format(N_low, N_high))
samples = samples[N_low:N_high]

#print()

results = pd.DataFrame()
for k, sample_index in enumerate(samples):
    print('{}: {}/{}'.format(school_type, k, len(samples)))
    # get the values of the calibration parameters
    intermediate_contact_weight, far_contact_weight, age_transmission_discount = \
            params[sample_index]
    
    # since we only use contacts of type "close", "intermediate" and "far" in 
    # this setup, we set the contact type "very far" to 0. The contact type
    # "close" corresponds to household transmissions and is set to 1 (= base 
    # transmission risk). We therefore only calibrate the weight of the 
    # "intermediate"  and "far" contacts with respect to household contacts
    infection_risk_contact_type_weights = {
            'very_far': 0, 
            'far': far_contact_weight, 
            'intermediate': intermediate_contact_weight,
            'close': 1}
    

    # get the respective parameters for the given school type
    measures = prevention_measures[school_type]
    characteristics = school_characteristics[school_type]
    agent_index_ratio = agent_index_ratios[school_type]

    school_name = '{}_classes-{}_students-{}'.format(school_type,
                characteristics['classes'], characteristics['students'])
    school_src = join(src, school_type)
    
    # create the agent dictionaries based on the given parameter values and
    # prevention measures
    agent_types = compose_agents(measures, target_base_transmission_risk,
                             base_reception_risk)

    # conduct all runs for an ensemble with a given set of parameters
    ensemble_results = pd.DataFrame()
    for run in range(1, N_runs + 1):
        
        # load the contact graph: since households and sibling contacts
        # are random, there are a number of randomly created instances of 
        # calibration schools from which we can chose. We use a different
        # calibration school instance for every run here
        try:
        	G = nx.readwrite.gpickle.read_gpickle(join(school_src,\
                        '{}_{}.gpickle'.format(school_name, run % 1000)))
        except FileNotFoundError:
        	G = nx.readwrite.gpickle.read_gpickle(join(school_src,\
                        '{}_{}.gpickle'.format(school_name, run % 1000 + 1)))
        
        # pick an index case according to the probabilities for the school type
        index_case = np.random.choice(list(agent_index_ratio.keys()),
                                      p=list(agent_index_ratio.values()))

        # initialize the model
        model = SEIRX_school(G, verbosity, 
                  testing = measures['testing'],
                  exposure_duration = [5.0, 1.9], # literature values
                  time_until_symptoms = [6.4, 0.8], # literature values
                  infection_duration = [10.91, 3.95], # literature values
                  quarantine_duration = measures['quarantine_duration'],
                  subclinical_modifier = subclinical_modifier,
                  infection_risk_contact_type_weights = \
                             infection_risk_contact_type_weights,
                  K1_contact_types = measures['K1_contact_types'],
                  diagnostic_test_type = measures['diagnostic_test_type'],
                  preventive_screening_test_type = \
                             measures['preventive_screening_test_type'],
                  follow_up_testing_interval = \
                             measures['follow_up_testing_interval'],
                  liberating_testing = measures['liberating_testing'],
                  index_case = index_case,
                  agent_types = agent_types, 
                  age_transmission_risk_discount = \
                             {'slope':age_transmission_discount, 'intercept':1},
                  age_symptom_discount = age_symptom_discount)

        # run the model until the outbreak is over
        for i in range(N_steps):
            # break if first outbreak is over
            if len([a for a in model.schedule.agents if \
                (a.exposed == True or a.infectious == True)]) == 0:
                break
            model.step()

        # collect the observables needed to calculate the difference to the
        # expected values
        infected_teachers = af.count_infected(model, 'teacher')
        infected_students = af.count_infected(model, 'student')
        # subtract the index case from the number of infected teachers/students
        # to arrive at the number of follow-up cases
        if index_case == 'teacher':
            infected_teachers -= 1
        else:
            infected_students -= 1

        ensemble_results = ensemble_results.append({
            'infected_teachers':infected_teachers,
            'infected_students':infected_students}, ignore_index=True)

    # calculate the differences between the expected and observed outbreak sizes
    # and the distribution of cases to the two agent groups
    chi2_distance_size, sum_of_squares_size = \
        calculate_distribution_difference(school_type, ensemble_results)
    chi2_distance_distro, sum_of_squares_distro = \
        calculate_group_case_difference(school_type, ensemble_results)

    results = results.append({
        'school_type':school_type,
        'intermediate_contact_weight':intermediate_contact_weight,
        'far_contact_weight':far_contact_weight,
        'age_transmission_discount':age_transmission_discount,
        'chi2_distance_size':chi2_distance_size,
        'sum_of_squares_size':sum_of_squares_size,
        'chi2_distance_distro':chi2_distance_distro,
        'sum_of_squares_distro':sum_of_squares_distro,
        'chi2_distance_total':chi2_distance_size + chi2_distance_distro,
        'sum_of_squares_total':sum_of_squares_size + sum_of_squares_distro
    }, ignore_index=True)

    results.to_csv(join(dst, 'calibration_results_{}_samples{}_random_{}-{}.csv'\
		.format(school_type, len(samples), N_runs, N_low, N_high)), index=False)
    
results.to_csv(join(dst, 'calibration_results_{}_samples{}_runs{}_random_{}-{}.csv'\
		.format(school_type, len(samples), N_runs, N_low, N_high)), index=False)