#!/bin/bash
#SBATCH -J COVID_SEIRX_calibration              ## name
#SBATCH -N 1                 
#SBATCH -o output
#SBATCH -e error
#SBATCH --ntasks=32          ## number of tasks per node
#SBATCH --time=00:00:05      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

python test_cluster_output.py &