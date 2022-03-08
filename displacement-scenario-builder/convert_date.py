import pandas as pd
import datetime

days = pd.read_csv('./refugees.csv')

simulation_start = datetime.datetime.strptime(days['Date'][0], '%Y-%m-%d')

for i in days.index:
    if i == 0:
        days.at[i, 'day'] = 0
    else:
        simulation_end = datetime.datetime.strptime(days.at[i, 'Date'], '%Y-%m-%d') + datetime.timedelta(days=1)
        diff = (simulation_end - simulation_start)
        diff_days = str(diff).split(" ")[0]
        days.at[i, 'day'] = str(diff_days)

sim_days = days[['day', 'Date', 'refugee_numbers']]
sim_days.to_csv('./refugees.csv', sep=',', index=False)
