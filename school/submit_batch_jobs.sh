#!/bin/bash
#SBATCH -J COVID_SEIRX_calibration              ## name
#SBATCH -N 2                 
#SBATCH --ntasks=32          ## number of tasks per node
#SBATCH --time=00:00:05      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

for school_type in primary primary_dc lower_secondary lower_secondary_dc upper_secondary secondary secondary_dc
   do
   
   for icw in 0.3 0.35 0.4 0.45
      do

      for fcw in 0.3 0.35 0.4 0.45
      do

         for atd in -0.04, -0.035, -0.03, -0.025
            do

            python test_cluster.py $school_type $icw $fcw $atd &

         done

      done

   done

done