import sys
import pandas as pd
import scipy
import numpy as np
import random

co_df = pd.read_csv("conflicts-end.csv")

row_sums = co_df.sum(axis=1)

print("All sums:", co_df.sum(axis=1).sum(axis=0))


def insert_conflict(name, day, length):
    co_df.loc[day:day + length, name] = 1


s = sys.argv[1]
intensity = int(sys.argv[2])

# Specify locations by regions
names = []
names_east = ["East1", "East2", "East3"]

names_west = ["West1", "West2", "West3"]

names_south = ["South1", "South2", "South3"]

names_north = ["North1", "North2", "North3"]

# Provide regions as follows
if s == "east":
    names = names_east
elif s == "west":
    names = names_west
elif s == "south":
    names = names_south
elif s == "north":
    names = names_northwest


for i in range(0, intensity):
    loc = names[random.randint(0, len(names) - 1)]
    # Provide simulation days for forecasting conflicts
    insert_conflict(loc, random.randint(25, 50), random.randint(5, 30))


co_df.to_csv("conflicts.csv", index=False)
