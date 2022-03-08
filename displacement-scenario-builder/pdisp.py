import sys
import pandas as pd
import scipy
import numpy as np
from datetime import datetime, timedelta

co_df = pd.read_csv(sys.argv[1])
del co_df['#Day']

loc_df = pd.read_csv("locations.csv")
rf_df = pd.read_csv("refugees.csv")  # assumed to be sorted ascending by day.

row_sums = co_df.sum(axis=1)

# Specify simulation period
t_end = 50 

recorded_refs = [np.nan] * 50

for index, row in rf_df.iterrows():
    recorded_refs[int(row["day"])] = row["refugee_numbers"]

val_data = pd.DataFrame(recorded_refs)
val_data = val_data.interpolate(method='linear', axis=0).astype(int)


def get_offseted_value(i, array, offset=2):

    if len(array) < offset:
        print("ERROR: array too short for get_offseted_values(). Array = ",
              array)
        sys.exit()

    if i == 0:
        value = 0
        for i in range(0, offset):
            value += array[offset]
        return value

    if i >= len(array) - offset:
        return array[len(array) - 1]

    else:
        return array[i + offset]


def inc_agents(t, conflict_row_sums):
    number_of_conflicts = get_offseted_value(t, conflict_row_sums)

    return 9900 * number_of_conflicts


t = 0
refugees = 10000 # the number of refugees

total_validation_score = 0

for t in range(0, t_end):
    # print(row_sums[t], file=sys.stderr)
    refugees += inc_agents(t, row_sums)

    validation_score = abs(
        (refugees - val_data.iloc[t][0]) / val_data.iloc[t][0])
    total_validation_score += validation_score

    # Specify the start of the simulation period (e.g. 2020-11-04)
    new_date = (datetime(2020, 11, 4) + timedelta(t)).strftime('%Y-%m-%d')
    print("{},{}".format(new_date, refugees,
                         val_data.iloc[t][0], validation_score))

    # print("{},{},{},{}".format(type(t), type(refugees),
    #                            type(val_data.iloc[t][0]),
    #                            type(validation_score)))

# total_validation_score /= t_end
# print("Validation score: ", total_validation_score, file=sys.stderr)
