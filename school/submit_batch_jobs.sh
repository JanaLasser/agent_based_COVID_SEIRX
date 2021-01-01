#!/bin/bash
#SBATCH -J COVID_SEIRX_calibration              ## name
#SBATCH -N 14                 
#SBATCH --ntasks=32          ## number of tasks per node
#SBATCH --time=00:00:05      
#SBATCH --mail-type=BEGIN, END
#SBATCH --mail-user=lasser@csh.ac.at

for icw in 0.3 0.35 0.4 0.45
   do

   for fcw in 0.3 0.35 0.4 0.45
   do

      for atd in -0.04, -0.035, -0.03, -0.025
         do

         python test_cluster.py $icw $fcw $atd
      done

   done

done