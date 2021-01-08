#!/bin/bash
#
#SBATCH -J COVID_SEIRX_data_creation_primary_dc
#SBATCH -N 1                 
#SBATCH -o output
#SBATCH -e error
#SBATCH --ntasks-per-core=2
#SBATCH --ntasks=16          
#SBATCH --time=00:05:00      
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=lasser@csh.ac.at

module purge
module load anaconda3/5.3.0
source /opt/sw/x86_64/glibc-2.17/ivybridge-ep/anaconda3/5.3.0/etc/profile.d/conda.sh
conda activate covid

echo $HOSTNAME
python test.py 1 &
python test.py 2 &
