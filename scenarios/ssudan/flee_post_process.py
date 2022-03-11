#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import os
pd.options.mode.chained_assignment = None

# specify directories
#dir_data1 ='/Users/puma/GitHub_mjpuma/Flee_scenarios/ssudan/'
dir_data1 ='/home/clouseau/Flee_scenarios/'

#dir_data2 ='/Users/puma/GitHub_mjpuma/Flee_scenarios/ssudan/'
dir_data2 ='/home/clouseau/Flee_scenarios/ssudan/'
if not os.path.isdir(dir_data2+'output'):
    os.mkdir(dir_data2+'output')
if not os.path.isdir(dir_data2+'media'):
    os.mkdir(dir_data2+'media')
    
csv_file = (dir_data1 + 'out.csv')
date_file = (dir_data2 + 'input_csv/conflict_period.csv')

# Add dates to the output file
with open(date_file, "r") as period_file:
    # read file as csv file 
    periodinfo = pd.read_csv(period_file,header=None)
    datelist = pd.date_range(start=periodinfo.iloc[0,1], periods=int(periodinfo.iloc[1,1]), freq='D')

with open(csv_file, "r") as my_input_file:
    out_df = pd.read_csv(my_input_file)
    out_df.insert(1, "Date", datelist, True)

out_df.to_csv(dir_data1+'outdate.csv', index = False)

# Restructure output data
features = [i for i in out_df.columns if 'sim' in i or 'error' in i or 'data' in i]
features = [i for i in features if 'total' not in i.lower() and 'refugees' not in i]

camps = set([i.split(' ')[0] for i in features])

count = 0
for camp in camps:
    cols = ['Date']
    camp_feats = [i for i in features if camp in i]
    #camp_feats = [i for i in features if camp == i.split('_')[0]]
    cols.extend(camp_feats)
    df_ = out_df[cols]
    df_['camp'] = camp
    for cf in camp_feats:
        df_.rename(columns={cf: cf.split(' ')[1]}, inplace=True)
    df_.set_index('Date', inplace=True)
    df_ = df_.groupby([lambda x: x.year, lambda x: x.month]).sum()
    df_.reset_index(level=0, inplace=True)
    df_.rename(columns={"Date": "Year"}, inplace=True)
    df_.reset_index(level=0, inplace=True)
    df_.rename(columns={"Date": "Month"}, inplace=True)
    df_['camp']=camp
    if count == 0:
        combined = df_
    else:
        combined = combined.append(df_)
    count += 1

# Add latitude and longitude of camps to output data
locations_file = (dir_data2 + 'input_csv/locations.csv')
locations_df = pd.read_csv(locations_file, index_col=0)

# declare an empty list to store
# latitude and longitude of values 
longitude = []
latitude = []

for i in (combined["camp"]):
    latitude.append(locations_df.loc[i,"lat"])
    longitude.append(locations_df.loc[i,"lon"])

# now add this column to dataframe
combined["Longitude"] = longitude
combined["Latitude"] = latitude

# Save output to files: one for camp values, one for totals (i.e. global)
combined.to_csv(dir_data2+ 'output/camp_data.csv',index=False)

other_cols = set(out_df.columns) - set(features)

out_df[other_cols].to_csv(dir_data2+ 'output/global_data.csv', index=False)
