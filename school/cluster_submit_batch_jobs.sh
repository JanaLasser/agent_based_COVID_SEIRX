#!/bin/bash
#
#SBATCH -J COVID_SEIRX_data_creation_primary_dc
#SBATCH -N 1                 
#SBATCH -o output_primary_dc
#SBATCH -e error_primary_dc
#SBATCH --ntasks-per-core=2
#SBATCH --ntasks=16          
#SBATCH --time=36:00:00      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

uptime
echo -n "start: "
date

module purge
module load anaconda3/5.3.0
source /opt/sw/x86_64/glibc-2.17/ivybridge-ep/anaconda3/5.3.0/etc/profile.d/conda.sh
conda deactivate
conda activate covid


N_runs=300
measure_step=64
school_type=primary_dc

for school_layout_start_index in $(seq 0 15)
   do
   school_layout_end_index=`echo $school_layout_start_index+1 | bc`
   
   for measure_start_index in $(seq 0 $measure_step 127)
      do
      measure_end_index=`echo $measure_start_index+$measure_step | bc`
      echo python run_data_creation.py $school_type $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index 
      echo $HOSTNAME
      python run_data_creation.py $school_type $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index &
   done

done

wait 
echo -n "end: "
date
uptime
