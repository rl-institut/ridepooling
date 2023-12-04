import argparse
from ridepooling.simulation import Simulation


def main():
    """_summary_"""
    parser = argparse.ArgumentParser(
        prog="RidePooling",
        description="Calculates a schedule of a fleet simulation through request.",
    )
    parser.add_argument(
        "config",
        default="src/ridepooling/example/config/config.cfg",
        nargs="?",
        help="Set the scenario path from working directory (usually repository root).",
    )
    p_args = parser.parse_args()
    simulation = Simulation.from_config(p_args.config)
    simulation.run()


if __name__ == "__main__":
    main()
