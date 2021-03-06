#!/usr/bin/env python
# coding: utf-8

import argparse
import copy
import os

import numpy as np
import pandas as pd
import shutil
import multiprocessing

import run_flee

# Pandas config
pd.options.mode.chained_assignment = None


def main(args):
    arg_set = []
    output_files = []
    media_dirs = []
    concurrency = args.concurrency
    run_count = args.runs

    if not os.path.exists(args.run_dir):
        os.mkdir(args.run_dir)
    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)
    if not os.path.isdir(args.media_dir):
        os.mkdir(args.media_dir)

    # Create a list of arguments to pass in to the run_flee.py command, overwriting as needed
    for i in range(run_count):
        run_args = copy.copy(args)
        del run_args.concurrency
        del run_args.runs
        run_args.cores = 1
        run_args.run_dir = os.path.join(run_args.run_dir, str(i))
        run_args.output_dir = os.path.join(run_args.run_dir, "output")
        run_args.media_dir = os.path.join(run_args.run_dir, "media")
        arg_set.append(run_args)
        output_files.append(os.path.join(run_args.output_dir, "camp_data.csv"))
        media_dirs.append(run_args.media_dir)
    with multiprocessing.Pool(processes=concurrency) as pool:
        pool.map(run_flee.main, arg_set)

    df = pd.concat(pd.read_csv(file_path) for file_path in output_files)
    grouped_df = df.drop(columns=['error']).groupby([
        'Date',
        'camp',
        'data',
        'Longitude',
        'Latitude'
    ])
    aggregated_df = grouped_df.aggregate(
        [
            "min", "max", "median", "mean"
        ]
    ).droplevel(axis=1, level=0).reset_index()

    final_df = aggregated_df.reset_index().assign(
        error=lambda agg: np.round(np.absolute(agg["median"] - agg["data"]) / agg["data"], 4),
        median=lambda agg: np.round(agg["median"], 2),
        mean=lambda agg: np.round(agg["mean"], 2),
    ).drop(columns=["index"])
    final_df["error"][np.isinf(final_df["error"])] = np.NAN

    # Export aggregated ensemble data to single camp_data.csv
    final_df.to_csv(os.path.join(args.output_dir, "camp_data.csv"), index=False)

    # for media_dir in media_dirs:
    #     shutil.copytree(media_dir, os.path.join(args.media_dir, "/"))

    # generate movie if specified
    # only import FleeVisualization in this case to avoid complex dependencies when they are not needed
    if args.movie:
        from run_visualization import FleeVisualization
        viz = FleeVisualization(final_df, args.scenario)
        viz.create_movie()


if __name__ == "__main__":
    # Get list of defined scenarios
    scenario_dir = "./scenarios"
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
        "runs",
        type=int,
        help="Number of model runs to aggregate and assemble",
        default=10,
    )
    arg_parser.add_argument(
        "--concurrency",
        type=int,
        help="Number of runs to process at the same time",
        default=None,
    )
    arg_parser.add_argument(
        "--cores",
        type=int,
        help="Number of cores to use per run when running",
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
    arg_parser.add_argument(
        "--movie",
        action="store_true",
        help="Generate Flee movie",
    )

    args = arg_parser.parse_args()
    main(args)

