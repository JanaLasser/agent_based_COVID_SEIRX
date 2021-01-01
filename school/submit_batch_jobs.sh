#!/bin/bash
#SBATCH -J COVID_SEIRX_calibration              ## name
#SBATCH -N 4                 
#SBATCH --ntasks=32          ## number of tasks per node
#SBATCH --time=03:00:00      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

N_runs=2000

for school_type in primary primary_dc
   do
   
   for icw in 0.3 0.35 0.4 0.45
      do

      for fcw in 0.3 0.35 0.4 0.45
      do

         for atd in -0.04 -0.035 -0.03 -0.025
            do

            python run_calibration_cluster.py $school_type $N_runs $icw $fcw $atd &

         done

      done

   done

done