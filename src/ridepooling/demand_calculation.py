import pandas as pd
import numpy as np
import random
import pathlib
from datetime import timedelta

from ridepooling.request import Request


class Demand_calculation:
    """
    Represents a demand calculation module for generating synthetic ride requests based on configuration parameters.

    This class is responsible for creating and managing synthetic ride request data for simulations.

    Attributes
    ----------
    request_list : list
        A list to store generated ride request objects.
    demand : pd.DataFrame
        A DataFrame containing demand data.
    station_probability : pd.DataFrame
        A DataFrame representing station probabilities.

    Methods
    -------
    create_synthetic_demand(time_list, cfg_dict, station_probability, demand, waytime)
        Generate synthetic ride requests based on station probabilities and demand data.
    get_request_list()
        Get the list of generated ride request objects.
    """
    def __init__(self, cfg_dict, time_list, waytime):
        """
        Initialize a Demand_calculation object.

        Parameters
        ----------
        cfg_dict : dict
            A dictionary containing configuration parameters.
        time_list : list
            A list of time intervals.
        waytime : pd.DataFrame
            A DataFrame representing waytime information between stations.

        Returns
        -------
        None
        """
        self.request_list = []
        self.demand = pd.read_csv(
            pathlib.Path(
                cfg_dict["scenario_data_path"], cfg_dict["csv_paths"]["demand_path"]
            ),
            header=0,
            index_col=0,
        )

        self.station_probability = pd.read_csv(
            pathlib.Path(
                cfg_dict["scenario_data_path"],
                cfg_dict["csv_paths"]["station_probability_path"],
            ),
            header=0,
            index_col=0,
        )

        self.create_synthetic_demand(
            time_list, cfg_dict, self.station_probability, self.demand, waytime
        )

    def create_synthetic_demand(
        self, time_list, cfg_dict, station_probability, demand, waytime
    ):
        """
        Create statistic ride requests based on demand profiles from config parameters.

        Parameters
        ----------
        time_list : list
            A list of time intervals.
        cfg_dict : dict
            A dictionary containing configuration parameters.
        station_probability : pd.DataFrame
            A DataFrame containing station probabilities.
        demand : pd.DataFrame
            A DataFrame representing demand data.
        waytime : pd.DataFrame
            A DataFrame representing waytime information between stations.

        Returns
        -------
        None
        """
        id = 0
        for minute in time_list:
            timestep = cfg_dict["start_date"] + timedelta(minutes=minute)
            demand_now = demand.at[int(timestep.hour), str(timestep.weekday())]
            seed = random.random()
            if seed < demand_now * cfg_dict["order_behaviour"]["demand_factor"]:
                probability = station_probability.loc[timestep.hour]
                probability_normalized = []
                for prob in probability:
                    probability_normalized.append(prob / sum(probability))
                stations = np.random.choice(
                    station_probability.columns,
                    2,
                    replace=False,
                    p=probability_normalized,
                )
                seed_2 = random.random()
                if seed_2 < cfg_dict["order_behaviour"]["order_behaviour"]:
                    # TODO: Noch hardgecoded!
                    time = timestep - timedelta(minutes=3)
                else:
                    # TODO: was schlaues ausdenken um nach Zeit zu ordnen!!
                    ahead_list = [
                        *range(
                            int(cfg_dict["order_behaviour"]["order_ahead_max"]),
                            int(cfg_dict["order_behaviour"]["order_ahead_max"]) + 1,
                            1,
                        )
                    ]
                    delta = np.random.choice(ahead_list, 1)
                    time = timestep - timedelta(minutes=int(delta[0]))
                # TODO: random choice for passangers
                # TODO: parse with config parser
                probability_list = []
                passangers_probability = [0.61, 0.25, 0.05, 0.05, 0.025, 0.015]
                seats = []
                q = 1
                for i in passangers_probability:
                    seats.append(q)
                    probability_list.append(i / sum(passangers_probability))
                    q += 1
                passangers = np.random.choice(
                    seats, 1, replace=False, p=probability_list
                )
                request = Request(
                    stations[0],
                    stations[1],
                    id,
                    timestep,
                    passangers[0],
                    time,
                    cfg_dict["weights"]["delay_max"],
                    waytime.loc[stations[0], stations[1]],
                )
                self.request_list.append(request)
                id += 1

