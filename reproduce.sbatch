#!/bin/sh
#SBATCH --mem-per-cpu=256000MB
#SBATCH -t 120:00:00
module load python3
./reproduce_acl2018_orthographic.sh
