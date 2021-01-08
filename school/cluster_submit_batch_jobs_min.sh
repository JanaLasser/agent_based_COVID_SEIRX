#!/bin/bash
#
#SBATCH -J COVID_SEIRX_data_creation_primary_dc
#SBATCH -N 1                 
#SBATCH -o output
#SBATCH -e error
#SBATCH --ntasks-per-core=2
#SBATCH --ntasks=16          
#SBATCH --time=00:00:10      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

module purge
module load anaconda3/5.3.0
source /opt/sw/x86_64/glibc-2.17/ivybridge-ep/anaconda3/5.3.0/etc/profile.d/conda.sh
conda activate covid

echo $HOSTNAME
python cluster_test.py > stdout_min 2> stderr_min &
