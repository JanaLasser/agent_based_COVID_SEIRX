#!/bin/bash

uptime
echo -n "start: "
date

N_runs=500
school_type=secondary             
max_tasks=32                 ## number of tasks per node.
running_tasks=0              ## initialization


for school_layout_start_index in $(seq 0 19)
	do
	school_layout_end_index=`echo $school_layout_start_index+1 | bc`
	
	for measure_start_index in $(seq 0 287)
		do
		running_tasks=`ps -C python --no-headers | wc -l`
		
		while [ "$running_tasks" -ge "$max_tasks" ]
			do
			sleep 5
			running_tasks=`ps -C python --no-headers | wc -l`
		done

		measure_end_index=`echo $measure_start_index+1 | bc`
		echo "*********************"
		echo $HOSTNAME: python run_data_creation.py $school_type $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index  
		date
		uptime
		free -h
		python run_data_creation.py $school_type $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index &
		echo "*********************"
		sleep 1
		
	done
done
wait

echo -n "end: "
date