#!/usr/bin/env python
# coding: utf-8

import argparse
import csv
import math
import os
import pandas as pd
import shutil
import subprocess

from flare.flare import simulate


def update_csv_conf(dict_file_path: str, new_values: dict):
    data = []
    # Tracking keys so we can determine if a config value exists in the setting file or not
    config_keys = set(new_values.keys())
    updated_keys = set()
    with open(dict_file_path) as input:
        reader = csv.reader(input)
        for name, value in reader:
            data.append([name, new_values.get(name, value)])
            updated_keys.add(name)
    # Add any values from new_values that weren't in the config file
    for key in (config_keys - updated_keys):
        data.append([key, new_values.get(key)])
    with open(dict_file_path, "w") as output:
        writer = csv.writer(output, dialect="unix")
        writer.writerows(data)


def csv_config_to_dict(dict_file_path: str) -> dict:
    reader = csv.reader(open(dict_file_path))
    result = dict(reader)
    return result


# Pandas config
pd.options.mode.chained_assignment = None

scenario_dir = os.path.abspath("./scenarios")


def main(args):
    rundir = os.path.abspath(args.run_dir)
    if not os.path.exists(rundir):
        os.mkdir(rundir)

    scenario = args.scenario
    cores = str(args.cores)

    curr_dir_path = os.path.abspath('.')
    base_dir_data_path = os.path.join(scenario_dir, scenario)
    run_dir_data_path = os.path.join(rundir, scenario)
    if os.path.exists(run_dir_data_path):
        shutil.rmtree(run_dir_data_path)
    shutil.copytree(base_dir_data_path, run_dir_data_path)
    conflict_period_file = os.path.join(
        run_dir_data_path, "input_csv", "conflict_period.csv"
    )
    simsetting_file = os.path.join(run_dir_data_path, "simsetting.csv")


    # Update config files for use in Flee and pull configuration to a dictionary for use in this script
    # Since conflicts cannot extend beyond the scenario, we clamp the number of days to be no more than
    # the scenario default
    conflict_period = csv_config_to_dict(conflict_period_file)
    if args.ndays is not None and (
            args.flare
            or args.ndays <= int(conflict_period.get("Length", args.ndays))
    ):
        ndays = args.ndays
        conflict_period["Length"] = ndays
        update_csv_conf(conflict_period_file, {"Length": ndays})
    else:
        ndays = int(conflict_period.get("Length"))
    update_csv_conf(
        simsetting_file,
        {
            name: getattr(args, name)
            for name in (
                "CampMoveChance",
                "ConflictMoveChance",
                "DefaultMoveChance",
                "MaxMoveSpeed",
                "MaxWalkSpeed",
                "AgentLogLevel",
            )
            if getattr(args, name) is not None
        },
    )
    simsetting = csv_config_to_dict(simsetting_file)

    if args.flare:
        window_size = math.gcd(ndays, ndays // 20)
        simulate(
            scenario_name=scenario,
            scenario_path=run_dir_data_path,
            simulation_days=ndays,
            window_size=window_size,
            output_file_name=os.path.join(run_dir_data_path, "input_csv", "conflicts.csv"),
        )

    print("Running the Flee agent based model")
    print(f"Running P-FLEE with cores = {cores}")

    # Run the Flee ABM
    if int(cores) <= 1:
        amb_cmd = (
            f"python3 {os.path.join(curr_dir_path, 'run_par.py')} {os.path.join(run_dir_data_path, 'input_csv')} "
            f"{os.path.join(run_dir_data_path, 'source_data')} {ndays} {os.path.join(run_dir_data_path, 'simsetting.csv')}"
        )
    else:
        amb_cmd = (
            f"mpirun -np {cores} python3 {os.path.join(curr_dir_path, 'run_par.py')} {os.path.join(run_dir_data_path, 'input_csv')} "
            f"{os.path.join(run_dir_data_path, 'source_data')} {ndays} {os.path.join(run_dir_data_path, 'simsetting.csv')}"
        )


    print(amb_cmd)
    with open(os.path.join(rundir, "out.csv"), "wb") as outfile:
        subprocess.run(amb_cmd, cwd=rundir, stdout=outfile, shell=True)

    # specify directories
    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)
    if not os.path.isdir(args.media_dir):
        os.mkdir(args.media_dir)

    csv_file = os.path.join(rundir, "out.csv")

    datelist = pd.date_range(
        start=conflict_period.get("StartDate"), periods=ndays, freq="D"
    )

    with open(csv_file, "r") as my_input_file:
        out_df = pd.read_csv(my_input_file)
        print(out_df)
        out_df.insert(1, "Date", datelist, True)

    out_df.to_csv(os.path.join(rundir, "outdate.csv"), index=False)

    # Restructure output data
    features = [
        i
        for i in out_df.columns
        if ("sim" in i or "error" in i or "data" in i)
        and ("total" not in i.lower() and "refugees" not in i)
    ]

    camps = set([i.split(" ")[0] for i in features])

    count = 0
    for camp in camps:
        cols = ["Date"]
        camp_feats = [i for i in features if camp in i]
        # camp_feats = [i for i in features if camp == i.split('_')[0]]
        cols.extend(camp_feats)
        df_ = out_df[cols]
        df_["camp"] = camp
        for cf in camp_feats:
            df_.rename(columns={cf: cf.split(" ")[1]}, inplace=True)
        df_["camp"] = camp
        if count == 0:
            combined = df_
        else:
            combined = combined.append(df_)
        count += 1

    combined = combined.sort_values(by="Date", ascending=True)

    # Add latitude and longitude of camps to output data
    locations_file = os.path.join(run_dir_data_path, "input_csv/locations.csv")
    locations_df = pd.read_csv(locations_file, index_col=0)

    # declare an empty list to store
    # latitude and longitude of values
    longitude = []
    latitude = []

    print(locations_df)
    for i in combined["camp"]:
        latitude.append(locations_df.loc[i, "latitude"])
        longitude.append(locations_df.loc[i, "longitude"])

    # now add this column to dataframe
    combined["Longitude"] = longitude
    combined["Latitude"] = latitude

    # Save output to files: one for camp values, one for totals (i.e. global)
    combined.to_csv(os.path.join(args.output_dir, "camp_data.csv"), index=False)

    other_cols = set(out_df.columns) - set(features)

    out_df[other_cols].to_csv(os.path.join(args.output_dir, "global_data.csv"), index=False)

    for filename in os.listdir("."):
        if "agents.out" in filename:
            output_file_path = os.path.join(args.output_dir, filename)
            # Remove the file if already exists (perhaps from an earlier run)
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
            shutil.move(filename, output_file_path)


if __name__ == "__main__":
    # Get list of defined scenarios
    scenarios = [
        entry.name
        for entry in os.scandir(path=scenario_dir)
        if entry.is_dir() and not entry.name.startswith(".")
    ]


    description = """
    This tool helps run the flee models for the provided scenarios.
    """

    arg_parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    arg_parser.add_argument(
        "scenario",
        type=str,
        choices=scenarios,
        help="Predefined scenario to run",
    )
    arg_parser.add_argument(
        "--cores",
        type=int,
        help="Number of cores to use when running.",
        default=2,
    )
    arg_parser.add_argument(
        "--ndays",
        type=int,
        help="Number of days to simulate.",
        default=None,
    )
    arg_parser.add_argument(
        "--MaxMoveSpeed",
        type=int,
        help="",
        default=None,
    )
    arg_parser.add_argument(
        "--CampMoveChance",
        type=float,
        help="Chance for a camp to move. (0-1)",
        default=None,
    )
    arg_parser.add_argument(
        "--ConflictMoveChance",
        type=float,
        help="",
        default=None,
    )
    arg_parser.add_argument(
        "--DefaultMoveChance",
        type=float,
        help="",
        default=None,
    )
    arg_parser.add_argument(
        "--MaxWalkSpeed",
        type=int,
        help="",
        default=None,
    )
    arg_parser.add_argument(
        "--AgentLogs",
        action="store_const",
        const=1,
        help="",
        default=None,
        dest="AgentLogLevel",
    )
    arg_parser.add_argument(
        "--run-dir",
        action="store",
        help="",
        default="./run/",
    )
    arg_parser.add_argument(
        "--output-dir",
        action="store",
        help="",
        default="./run/output",
    )
    arg_parser.add_argument(
        "--media-dir",
        action="store",
        help="",
        default="./run/media",
    )
    arg_parser.add_argument(
        "--flare",
        action="store_true",
        help="Use conflict generated by Flare",
    )
    args = arg_parser.parse_args()
    main(args)

