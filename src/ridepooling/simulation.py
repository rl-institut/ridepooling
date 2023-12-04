import configparser as cp
import json
import pathlib
import pprint

import pandas as pd
from datetime import datetime
from ridepooling.request import Request
from ridepooling.pooling import Pooling
from ridepooling.vehicle import Vehicle
from ridepooling.demand_calculation import Demand_calculation


class Simulation:
    """
    Represents a simulation of a ride pooling system.

    This class simulates ride requests, vehicle schedules, and pooling strategies based on configuration parameters.

    Attributes:
        cfg_dict (dict): A dictionary containing configuration data for the simulation.
        waytime (pandas.DataFrame): A DataFrame representing waytime data between stations.
        distance (pandas.DataFrame): A DataFrame containing distance data between stations.
        vehicle_list (list): A list of vehicle objects to be used in the simulation.
        station_list (list): A list of stations created based on distance data.
        time_list (list): A list of time-related data created based on the configuration.
        request_list (list): An empty list to hold ride request data.
        result_path (pathlib.Path): The path to the results directory.

    Methods:
        create_vehicle_objects(vehicles):
            Create a list of vehicle objects based on input data.
        create_station_list(distance):
            Create a list of unique station names from distance data.
        create_time_list(cfg_dict):
            Create a list of time-related data based on configuration.
        run():
            Run the entire simulation process.
        from_csv(cfg_dict):
            Populate the request list with data from a CSV file.
        export(Pooling_simulation):
            Export simulation results to files and folders.
        from_config(config_path):
            Create a Simulation object from the specified scenario configuration file.
    """

    def __init__(self, cfg_dict, vehicles):
        """
        Initialize the Simulation class.

        This constructor sets up the simulation with provided configuration and data.

        Parameters
        ----------
        cfg_dict : dict
            A dictionary containing configuration data for the simulation.
        vehicles : list
            A list of vehicle objects to be used in the simulation.

        Attributes
        ----------
        cfg_dict : dict
            The configuration dictionary for the simulation.
        waytime : pandas.DataFrame
            A DataFrame containing waytime data between stations.
        distance : pandas.DataFrame
            A DataFrame containing distance data between stations.
        vehicle_list : list
            A list of vehicle objects.
        station_list : list
            A list of stations created based on distance data.
        time_list : list
            A list of time-related data created based on the configuration.
        request_list : list
            An empty list to hold ride request data.
        result_path : pathlib.Path
            The path to the results directory.

        Returns
        -------
        None

        """
        self.cfg_dict = cfg_dict
        self.waytime = pd.read_csv(
            pathlib.Path(
                cfg_dict["scenario_data_path"], cfg_dict["csv_paths"]["waytime_path"]
            ),
            header=0,
            index_col=0,
        )
        self.distance = pd.read_csv(
            pathlib.Path(
                cfg_dict["scenario_data_path"], cfg_dict["csv_paths"]["distance_path"]
            ),
            header=0,
            index_col=0,
        )

        self.vehicle_list = self.create_vehicle_objects(vehicles)
        self.station_list = self.create_station_list(self.distance)
        self.time_list = self.create_time_list(cfg_dict)

        self.request_list = []
        self.result_path = pathlib.Path(cfg_dict["scenario_data_path"], "results")
        self.result_path.mkdir(parents=True, exist_ok=True)

    def create_vehicle_objects(self, vehicles):
        """
        Create a list of vehicle objects based on input data.

        This function takes a list of vehicle data and constructs a list of Vehicle objects
        from the provided information.

        Parameters
        ----------
        vehicles : list of dict
            A list of dictionaries, each containing information about a vehicle.

        Returns
        -------
        list of Vehicle
            A list of Vehicle objects created from the input data.
        """
        # create vehicle objects
        vehicle_list = []
        for v in vehicles:
            name = vehicles[v]["name"]
            id = vehicles[v]["id"]
            seats = vehicles[v]["seats"]
            type = vehicles[v]["type"]
            vehicle = Vehicle(id, name, seats, type)
            vehicle_list.append(vehicle)
        return vehicle_list

    def create_station_list(self, distance):
        """
        Create a list of unique station names from distance data.

        This function extracts a list of unique station names from the provided distance data.

        Parameters
        ----------
        distance : pandas.DataFrame
            A DataFrame representing the distance between stations. The station names are
            assumed to be in the index of the DataFrame.

        Returns
        -------
        list of str
            A list of unique station names.
        """
        station_list = []
        for station_name in distance.index.unique():
            station_list.append(station_name)
        return station_list

    def create_time_list(self, cfg_dict):
        minutes = int(
            (cfg_dict["end_date"] - cfg_dict["start_date"]).total_seconds() // 60
        )
        time_list = list(range(0, minutes + 1))
        return time_list

    def run(self):
        """
        Run the simulation.

        This method orchestrates the entire simulation process, including request creation,
        pooling simulation, and result export.

        The function first checks the configuration to determine whether to create requests
        from CSV data or calculate them. After creating the requests, it initializes a
        pooling simulation with the provided data. If specified in the configuration, it
        exports simulation results.

        Returns
        -------
        None

        """
        # create requests
        print("===== creating requests =====")
        if self.cfg_dict["requests_from_csv"] == True:
            self.from_csv(self.cfg_dict)
            # csv_import = From_CSV(self.cfg_dict)
            # self.request_list = csv_import.get_request_list()
        else:
            requests = Demand_calculation(self.cfg_dict, self.time_list, self.waytime)
            self.request_list = requests.request_list

        print("===== pooling =====")
        Pooling_simulation = Pooling(
            self.vehicle_list,
            self.request_list,
            self.cfg_dict,
            self.waytime,
            self.distance,
        )

        if self.cfg_dict["outputs"]["outputs"] == True:
            self.export(Pooling_simulation)

        print("\r===== done =====")

    def from_csv(self, cfg_dict):
        """
        Populate the request list with data from a CSV file.

        This method reads request data from a CSV file specified in the configuration
        and populates the request list with Request objects.

        Parameters
        ----------
        cfg_dict : dict
            A dictionary containing configuration data for the simulation.

        Returns
        -------
        None
        """
        requests_frame = pd.read_csv(
            pathlib.Path(
                cfg_dict["scenario_data_path"], cfg_dict["csv_paths"]["requests_path"]
            )
        )
        requests_frame = requests_frame.sort_values(by=["time"])
        for index in requests_frame.index:
            if (
                cfg_dict["start_date"]
                <= datetime.fromisoformat(requests_frame.at[index, "start_time"])
                <= cfg_dict["end_date"]
            ):
                request = Request(
                    requests_frame.at[index, "start_id"],
                    requests_frame.at[index, "destination_id"],
                    requests_frame.at[index, "id"],
                    datetime.fromisoformat(requests_frame.at[index, "start_time"]),
                    requests_frame.at[index, "passangers"],
                    datetime.fromisoformat(requests_frame.at[index, "time"]),
                    cfg_dict["weights"]["delay_max"],
                    float(
                        self.waytime.loc[
                            requests_frame.at[index, "start_id"],
                            requests_frame.at[index, "destination_id"],
                        ]
                    ),
                )
                self.request_list.append(request)

    def export(self, Pooling_simulation):
        """
        Export simulation results to files and folders.

        This method exports various simulation results to CSV files and directories based
        on the specified configuration parameters.

        Parameters
        ----------
        Pooling_simulation : Pooling
            An instance of the Pooling class containing simulation results.

        Returns
        -------
        None
        """
        # export schedule
        now = datetime.now()
        folder_name = now.strftime("%Y-%m-%d-%H-%M-%S")
        results_folder = pathlib.Path(self.result_path, folder_name)
        results_folder.mkdir(parents=True, exist_ok=True)
        if self.cfg_dict["outputs"]["outputs"] == True:
            export_schedule = pd.DataFrame(
                columns=[
                    "vehicle_id",
                    "departure_name",
                    "departure_time",
                    "arrival_time",
                    "arrival_name",
                    "distance",
                    "driving_time",
                    "pause",
                    "vehicle_type",
                    "request_ids",
                    "boarding",
                ]
            )
            for vehicle in self.vehicle_list:
                export_schedule = pd.concat(
                    [
                        export_schedule,
                        vehicle.export_schedule(self.waytime, self.distance),
                    ]
                )
            schedule_path = pathlib.Path(results_folder, "schedule.csv")
            export_schedule.to_csv(schedule_path)

        if self.cfg_dict["outputs"]["vehicle_outputs"] == True:
            for vehicle in self.vehicle_list:
                vehicle.export_summary(results_folder)

        # export requests
        if self.cfg_dict["outputs"]["requests_output"] == True:
            request_frame = pd.DataFrame(
                columns=[
                    "time",
                    "start_time",
                    "start_id",
                    "destination_id",
                    "passangers",
                    "id",
                ]
            )
            for request in self.request_list:
                frame = pd.DataFrame(
                    [
                        [
                            request.time,
                            request.start_time,
                            request.start,
                            request.destination,
                            request.passangers,
                            request.request_id,
                        ]
                    ],
                    columns=[
                        "time",
                        "start_time",
                        "start_id",
                        "destination_id",
                        "passangers",
                        "id",
                    ],
                )
                request_frame = pd.concat([request_frame, frame])
            requests_path = pathlib.Path(results_folder, "requests.csv")
            request_frame.to_csv(requests_path)

        # export denied requests
        if self.cfg_dict["outputs"]["requests_denied_output"] == True:
            request_frame = pd.DataFrame(
                columns=[
                    "time",
                    "start_time",
                    "start_id",
                    "destination_id",
                    "passangers",
                    "id",
                ]
            )
            for request in Pooling_simulation.requests_denied_list:
                frame = pd.DataFrame(
                    [
                        [
                            request.time,
                            request.start_time,
                            request.start,
                            request.destination,
                            request.passangers,
                            request.request_id,
                        ]
                    ],
                    columns=[
                        "time",
                        "start_time",
                        "start_id",
                        "destination_id",
                        "passangers",
                        "id",
                    ],
                )
                request_frame = pd.concat([request_frame, frame])
            requests_path = pathlib.Path(results_folder, "requests_denied.csv")
            request_frame.to_csv(requests_path)

        # summary
        if self.cfg_dict["outputs"]["summary"] == True:
            summary_dict = {}
            vehicles = {"vehicles": {}}
            for vehicle in self.vehicle_list:
                schedule_veh = export_schedule.loc[
                    export_schedule["vehicle_id"] == vehicle.id
                ]
                distance_total = sum(schedule_veh["distance"])
                distance_occupied = sum(
                    schedule_veh.loc[schedule_veh["occupation"] > 0]["distance"]
                )
                passanger_distance = (
                    schedule_veh.loc[schedule_veh["occupation"] > 0]["distance"]
                    * schedule_veh.loc[schedule_veh["occupation"] > 0]["occupation"]
                )
                entry = {
                    vehicle.id: {
                        "distance_total": distance_total,
                        "distance_occupied": distance_occupied,
                        "passanger_distance": sum(passanger_distance),
                    }
                }
                vehicles["vehicles"].update(entry)

            distance_total = sum(export_schedule["distance"])
            distance_occupied = sum(
                export_schedule.loc[export_schedule["occupation"] > 0]["distance"]
            )
            passanger_distance = (
                export_schedule.loc[export_schedule["occupation"] > 0]["distance"]
                * export_schedule.loc[export_schedule["occupation"] > 0]["occupation"]
            )
            total = {
                "total": {
                    "distance_total": distance_total,
                    "distance_occupied": distance_occupied,
                    "passanger_distance": sum(passanger_distance),
                }
            }
            summary_dict.update(total)
            summary_dict.update(vehicles)

            # json_file = json.dump(summary_dict, indent=4)
            summary_path = pathlib.Path(results_folder, "summary.json")
            pretty_print_json = pprint.pformat(summary_dict)
            with open(summary_path, "w") as outfile:
                outfile.write(pretty_print_json)

    @classmethod
    def from_config(cls, config_path):
        """Creates a Simulation object from the specified scenario.
        A scenario consists of various input data like vehicles, station information, and
        pooling parameters, all defined in a configuration file. This method reads and
        processes the scenario configuration to create a Simulation object.
        ----------
        config_path : str
            Path to the scenario config.

        Returns
        -------
        Simulation
            Simulation object
        Raises
        ------
        FileNotFoundError
            If the scenario is not found in the given directory.
            If the config file scenario.cfg is not found or can't be read..
        """

        # set config_path
        config_path = pathlib.Path(config_path)

        # get
        cfg = cp.ConfigParser()
        if not config_path.is_file():
            raise FileNotFoundError(f"Config file {config_path} not found.")
        try:
            cfg.read(config_path)
        except Exception:
            raise FileNotFoundError(
                f"Cannot read config file {config_path} - malformed?"
            )

        # get scenario_data_path from config path
        scenario_data_path = config_path.parent.parent

        # get scenario data  from config
        start_date = datetime.fromisoformat(cfg.get("basic", "start_date"))
        end_date = datetime.fromisoformat(cfg.get("basic", "end_date"))
        requests_from_csv = cfg.getboolean("basic", "requests_from_csv")

        vehicles_file_path = cfg["files"]["vehicles"]
        ext = vehicles_file_path.split(".")[-1]
        if ext != "json":
            print("File extension mismatch: vehicles should be .json")
        with open(pathlib.Path(scenario_data_path, cfg["files"]["vehicles"])) as f:
            vehicles = json.load(f)
        vehicles = vehicles["vehicles"]

        weights = {
            "balance_factor": cfg["pooling"].getfloat("balance_factor", fallback = 0.0),
            "delay_factor": cfg.getfloat("pooling", "delay_factor", fallback=0.0),
            "pooling_factor": cfg.getfloat("pooling", "pooling_factor", fallback=0.0),
            "distance_factor": cfg.getfloat("pooling", "distance_factor", fallback=0.0),
            "delay_max": cfg.getfloat("basic", "delay_max", fallback=10.0),
            "standing_time": cfg.getfloat("basic", "standing_time", fallback=1.0)
        }

        order_behaviour = {
            "order_behaviour": cfg.getfloat("order_behaviour", "order_behaviour", fallback=0.1),
            "order_ahead_min": cfg.getfloat("order_behaviour", "order_ahead_min", fallback=20.0),
            "order_ahead_max": cfg.getfloat("order_behaviour", "order_ahead_max", fallback= 60.0),
            "demand_factor": cfg.getfloat("order_behaviour", "demand_factor", fallback=1.0),
        }

        if cfg.getboolean("basic", "requests_from_csv") == True:
            requests_path = cfg["files"]["requests"]
            station_probability_path = None
            demand_path = None
        else:
            requests_path = None
            station_probability_path = cfg["files"]["station_probability"]
            demand_path = cfg["files"]["demand"]
        csv_paths = {
            "distance_path": cfg["files"]["distance"],
            "waytime_path": cfg["files"]["waytime"],
            "station_probability_path": station_probability_path,
            "demand_path": demand_path,
            "requests_path": requests_path,
        }

        outputs = {
            "outputs": cfg.getboolean("outputs", "outputs", fallback = True),
            "summary": cfg.getboolean("outputs", "summary", fallback = True),
            "vehicle_outputs": cfg.getboolean("outputs", "vehicle_outputs", fallback = True),
            "requests_output": cfg.getboolean("outputs", "requests_output", fallback= True),
            "requests_denied_output": cfg.getboolean(
                "outputs", "requests_denied_output", fallback=True
            ),
        }

        cfg_dict = {
            "start_date": start_date,
            "end_date": end_date,
            "requests_from_csv": requests_from_csv,
            "weights": weights,
            "scenario_data_path": scenario_data_path,
            "config_path": config_path,
            "order_behaviour": order_behaviour,
            "csv_paths": csv_paths,
            "outputs": outputs,
        }

        return Simulation(cfg_dict, vehicles)
