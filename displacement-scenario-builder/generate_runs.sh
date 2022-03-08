#!/bin/bash

# USER PARAMETERS
CONFIG_FILES_PATH='example' 
INTENSITY_SET=( 10 20 30) 
SCENARIOS=('east' 'west') 
SWEEP_RUNS_NUMBER=2 
#-----------------------------------------------------------------------------

# PROGRAM PARAMETERS
SWEEP_dir=$CONFIG_FILES_PATH"/SWEEP"
# remove SWEEP folder from config_files dir is exists 
if [ -d "$SWEEP_dir" ]
then
	rm -rf $SWEEP_dir
fi
mkdir $SWEEP_dir



for scenario in "${SCENARIOS[@]}";
do
	for intensity in "${INTENSITY_SET[@]}";
	do
		for runID in `seq 1 $SWEEP_RUNS_NUMBER`;
		do

			# create target RUN folder inside SWEEP dir
			run_dir_name=$scenario'_'$intensity'_'$runID
			echo "SWEEP_RUN_DIR = $run_dir_name"

			mkdir -p $SWEEP_dir'/'$run_dir_name'/input_csv'
			mkdir -p $SWEEP_dir'/'$run_dir_name'/source_data'


			# generate conflicts.csv file
			python scenario-maker.py $scenario $intensity
			# move conflicts.csv to SWEEP/RUN_DIR_NAME/input_csv
			mv conflicts.csv $SWEEP_dir'/'$run_dir_name'/input_csv/'


			# generate refugees.csv file in SWEEP/RUN_DIR_NAME/source_data/
			python3 pdisp.py $SWEEP_dir'/'$run_dir_name'/input_csv/conflicts.csv' > $SWEEP_dir'/'$run_dir_name'/source_data/refugees.csv'
			
			
			
		done
	done
done
