import sys
import socket

school_type = sys.argv[1]
icw = sys.argv[2]
fcw = sys.argv[3]
atd = sys.argv[4]

print('in test_cluster')

hostname = socket.gethostname()

with open('../data/school/calibration_results_cluster/school_type-{}_icw-{}_fcw-{}_atd-{}_{}.txt'\
		.format(school_type, icw, fcw, atd, hostname), 'w') as f:
	print(hostname, file=f)