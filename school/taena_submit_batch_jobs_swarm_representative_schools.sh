uptime
echo -n "start: "
date
echo "representative schools"

conda activate covid

N_runs=500           
max_tasks=8                  
running_tasks=0              


for school_layout_start_index in $(seq 0 6)
	do
	school_layout_end_index=`echo $school_layout_start_index+1 | bc`
	
	for measure_start_index in $(seq 0 143)
		do
		running_tasks=`ps -C python --no-headers | wc -l`
		
		while [ "$running_tasks" -ge "$max_tasks" ]
			do
			sleep 5
			running_tasks=`ps -C python --no-headers | wc -l`
		done

		measure_end_index=`echo $measure_start_index+1 | bc`
		echo "*********************"
		echo $HOSTNAME: python run_data_creation_representative.py $school_type $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index  
		date
		uptime
		free -h
		python run_data_creation_representative.py $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index &
		echo "*********************"
		sleep 1
		
	done
done
wait

echo -n "end: "
date