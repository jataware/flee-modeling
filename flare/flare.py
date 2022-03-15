import argparse

from . import Ruleset
from .country import Country


def simulate(scenario_name, scenario_path, simulation_days, window_size, output_file_name=None):
    total_windows = simulation_days // window_size

    scenario = Country(scenario_name, scenario_path, window_size)
    Ruleset.Simulation(scenario, total_windows, window_size, output_file_name=output_file_name)


if __name__ == "__main__":

    description = """
    This tool helps run the flee models for the provided scenarios.
    """

    arg_parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    arg_parser.add_argument(
        "scenario_name",
        type=str,
        help="Name of the scenario/country",
    )
    arg_parser.add_argument(
        "scenario_path",
        type=str,
        help="Path to the directory that contains the scenario",
    )
    arg_parser.add_argument(
        "days",
        type=int,
        help="Number of days to simulate.",
    )
    arg_parser.add_argument(
        "window_size",
        type=int,
        help="Window size (???)",
    )
    arg_parser.add_argument(
        "--output-file-name",
        type=str,
        help="Sets the name of the file that is output",
        default=None,
    )
    args = arg_parser.parse_args()

    simulate(
        args.scenario_name,
        args.scenario_path,
        simulation_days=args.days,
        window_size=args.window_size,
        output_file_name=args.output_file_name,
    )
