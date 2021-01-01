import sys
import socket

icw = sys.argv[1]
fcw = sys.argv[2]
atd = sys.argv[3]

hostname = socket.gethostname()

with open('../data/school/calibration_results_cluster/icw-{}_fcw-{}_atd-{}_{}.txt'\
		.format(icw, fcw, atd, hostname), 'w') as f:
	print(hostname, file=f)