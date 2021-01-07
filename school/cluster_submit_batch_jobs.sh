#!/bin/bash
#SBATCH -J COVID_SEIRX_data_creation_primary_dc
#SBATCH -N 2                 
#SBATCH -o output
#SBATCH -e error
#SBATCH --ntasks-per-core=2
#SBATCH --ntasks=32          
#SBATCH --time=0      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

module purge
module module load anaconda3/5.3.0
source /opt/sw/x86_64/glibc-2.17/ivybridge-ep/anaconda3/5.3.0/etc/profile.d/conda.sh
conda activate covid


N_runs=300
measure_step=64
school_type=primary

for school_layout_start_index in $(seq 0 14)
   do
   school_layout_end_index=`echo $school_layout_start_index+1 | bc`
   
   for measure_start_index in $(seq 0 $measure_step 127)
      do
      measure_end_index=`echo $measure_start_index+$measure_step | bc`
      echo python3 run_data_creation.py $school_type $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index 
      echo hostname
      python3 run_data_creation.py $school_type $N_runs $school_layout_start_index $school_layout_end_index $measure_start_index $measure_end_index &

   done

done