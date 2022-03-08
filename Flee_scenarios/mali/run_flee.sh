#! /bin/bash

echo 'Running the Flee agent based model'

#set number of simulation days
date_file="/home/clouseau/Flee_scenarios/mali/input_csv/conflict_period.csv"
read -d $'\x04' arr < "$date_file"
myarray=(`echo $arr | tr ',' ' '`)
ndays=${myarray[-1]}

# Run the Flee ABM
python3 run.py input_csv source_data $ndays simsetting.csv > out.csv
#python3 ssudan_whole_revised/run.py ssudan_whole_revised/input_csv ssudan_whole_revised/source_data 426 ssudan_whole_revised/simsetting.csv > out.csv

#Adjust out.csv to have dates
#python3 adjust_outcsv.py
python3 flee_post_process.py
