#!/bin/bash
#
#SBATCH -J COVID_SEIRX_data_creation_upper_secondary_1
#SBATCH -N 1                 
#SBATCH -o output_upper_secondary_1
#SBATCH -e error_upper_secondary_1
#SBATCH --ntasks-per-core=2
#SBATCH --ntasks=16          
#SBATCH --time=36:00:00      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

uptime
echo -n "start: "
date
echo "upper_secondary 1"

module purge
module load anaconda3/5.3.0
source /opt/sw/x86_64/glibc-2.17/ivybridge-ep/anaconda3/5.3.0/etc/profile.d/conda.sh
conda deactivate
conda activate covid


N_runs=500
school_type=upper_secondary             
max_tasks=32                 ## number of tasks per node.
running_tasks=0              ## initialization


for school_layout_start_index in $(seq 0 1)
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