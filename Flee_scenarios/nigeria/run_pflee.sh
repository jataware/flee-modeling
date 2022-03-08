#! /bin/bash

echo 'Running the Flee agent based model'

cores=2

if [ ! -z "$1" ]; then
	cores=$1
fi

echo "Running P-FLEE with cores = " $cores

#set number of simulation days
date_file="/home/clouseau/Flee_scenarios/nigeria/input_csv/conflict_period.csv"
read -d $'\x04' arr < "$date_file"
myarray=(`echo $arr | tr ',' ' '`)
ndays=${myarray[-1]}

# Run the Flee ABM
mpirun -np $cores python3 run_par.py input_csv source_data $ndays simsetting.csv > out.csv

python3 flee_post_process.py
