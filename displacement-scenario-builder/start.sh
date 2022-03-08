#!/bin/bash

CONFIG_FILES_PATH='example' # e.g. 'ethiopia'

for config in $CONFIG_FILES_PATH;
do
	cp $config'/source_data/refugees.csv' 'refugees.csv'
        python convert_date.py refugees.csv
        cp $config'/input_csv/conflicts.csv' 'conflicts-end.csv'

done
	

