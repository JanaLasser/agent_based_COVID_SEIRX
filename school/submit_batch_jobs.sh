#!/bin/bash
#SBATCH -J COVID_SEIRX_calibration_primary
#SBATCH -N 4                 
#SBATCH -o output
#SBATCH -e error
#SBATCH --ntasks-per-core=2
#SBATCH --ntasks=32          
#SBATCH --time=01:00:00      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

module load python/3.7.4
module load numpy/1.15.4
module load scipy/1.3.1

N_runs=2000

for school_type in primary
   do
   
   for icw in 0.3 0.35 0.4 0.45
      do

      for fcw in 0.3 0.35 0.4 0.45
      do

         for atd in -0.04 -0.035 -0.03 -0.025
            do

            python3 run_calibration_cluster.py $school_type $N_runs $icw $fcw $atd &
            hostname &



         done

      done

   done

done