import pandas as pd
from datetime import date, datetime, timedelta
import os
import pathlib


class Vehicle:
    """
    Represents a vehicle with attributes and methods related to ride scheduling.

    This class manages vehicle attributes and schedules, such as location, passengers, and planned schedules.

    Attributes
    ----------
    id : int
        A unique identifier for the vehicle.
    name : str
        The name or identifier for the vehicle.
    seats : int
        The number of available seats in the vehicle.
    type : str
        The type or category of the vehicle.
    location : int
        The current location of the vehicle.
    passangers : int
        The number of passengers in the vehicle.
    schedule : pd.DataFrame
        A DataFrame representing the planned schedule of the vehicle.

    Methods
    -------
    update_schedule(schedule_new)
        Update the vehicle's schedule with a new schedule.
    calculating_time(id_start, id_end, timetable)
        Calculate the travel time between two stations.
    export_schedule(waytime, distance)
        Export the vehicle's schedule as a DataFrame.
    export_summary(path)
        Export a summary of the vehicle's schedule to a CSV file.
    """

    def __init__(self, id, name, seats, type):
        """
        Initialize a Vehicle object with the provided information.

        Parameters
        ----------
        id : int
            The vehicle's unique identifier.
        name : str
            The name of the vehicle.
        seats : int
            The number of seats available in the vehicle.
        type : str
            The type of the vehicle.

        Returns
        -------
        None

        """
        self.id = id
        self.name = name
        self.seats = seats
        self.type = type
        self.location = 1
        self.passangers = 0
        self.schedule = pd.DataFrame(
            columns=[
                "station",
                "boarding",
                "promissed_time",
                "request_id",
                "planed",
                "delay",
                "occupation",
                "max_delay",
            ]
        )

    def update_schedule(self, schedule_new):
        """
        Update the vehicle's schedule with a new schedule.

        Parameters
        ----------
        schedule_new : pd.DataFrame
            A new schedule to be merged with the vehicle's existing schedule.

        Returns
        -------
        None

        """
        self.schedule = pd.concat(
            [self.schedule[~self.schedule.index.isin(schedule_new.index)], schedule_new]
        )

    def calculating_time(self, id_start, id_end, timetable):
        """
        Calculate travel time between two station IDs.

        Parameters
        ----------
        id_start : int
            The ID of the starting station.
        id_end : int
            The ID of the destination station.
        timetable : pd.DataFrame
            A DataFrame containing travel time information between stations.

        Returns
        -------
        float
            The calculated travel time in minutes.

        """
        self.traveltime = timetable.at[id_start, str(id_end)]
        return self.traveltime

    def export_schedule(self, waytime, distance):
        """
        Export the vehicle's schedule with additional details.

        Parameters
        ----------
        waytime : pd.DataFrame
            A DataFrame representing waytime data between stations.
        distance : pd.DataFrame
            A DataFrame representing distance data between stations.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the exported schedule with added details.

        """
        path = os.path.dirname(__file__)
        timetable = waytime
        distance_table = distance

        # creating Data Frame
        exp_schedule = pd.DataFrame(
            columns=[
                "vehicle_id",
                "boarding_start",
                "departure_name",
                "departure_time",
                "arrival_time",
                "arrival_name",
                "boarding_dest",
                "distance",
                "driving_time",
                "pause",
                "vehicle_type",
                "request_ids",
                "occupation",
            ]
        )

        # initializing variables
        request_ids = ""

        # looping schedule
        for index in self.schedule.index:
            if index != max(self.schedule.index):
                if (
                    self.schedule.at[index, "station"]
                    == self.schedule.at[index + 1, "station"]
                ):
                    request_ids = (
                        request_ids + str(self.schedule.at[index, "request_id"]) + "-"
                    )
                else:
                    vehicle_id = self.id
                    boarding_start = self.schedule.at[index, "boarding"]
                    departure_name = self.schedule.at[index, "station"]
                    arrival_name = self.schedule.at[index + 1, "station"]
                    boarding_dest = self.schedule.at[index + 1, "boarding"]
                    driving_time = self.calculating_time(
                        departure_name, arrival_name, timetable
                    )
                    departure_time = (
                        self.schedule.at[index + 1, "planed"]
                        - timedelta(minutes=float(driving_time))
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    arrival_time = self.schedule.at[index + 1, "planed"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    distance = distance_table.at[departure_name, str(arrival_name)]
                    pause = None
                    vehicle_type = self.type
                    request_ids = (
                        request_ids + str(self.schedule.at[index, "request_id"]) + "-"
                    )
                    occupation = self.schedule.at[index, "occupation"]
                    export_line = pd.DataFrame(
                        [
                            [
                                vehicle_id,
                                boarding_start,
                                departure_name,
                                departure_time,
                                arrival_time,
                                arrival_name,
                                boarding_dest,
                                distance,
                                driving_time,
                                pause,
                                vehicle_type,
                                request_ids,
                                occupation,
                            ]
                        ],
                        columns=[
                            "vehicle_id",
                            "boarding_start",
                            "departure_name",
                            "departure_time",
                            "arrival_time",
                            "arrival_name",
                            "boarding_dest",
                            "distance",
                            "driving_time",
                            "pause",
                            "vehicle_type",
                            "request_ids",
                            "occupation",
                        ],
                    )
                    # set variables 0
                    request_ids = ""

                    # fit together
                    exp_schedule = pd.concat(
                        [exp_schedule, export_line], ignore_index=True
                    )

        # Calculating pause times
        for index in exp_schedule.index:
            if index != max(exp_schedule.index):
                if datetime.fromisoformat(
                    exp_schedule.loc[index + 1]["departure_time"]
                ) == datetime.fromisoformat(exp_schedule.loc[index]["arrival_time"]):
                    pause_time = 0
                elif datetime.fromisoformat(
                    exp_schedule.loc[index + 1]["departure_time"]
                ) < datetime.fromisoformat(exp_schedule.loc[index]["arrival_time"]):
                    pause_time = 0
                else:
                    pause_time = (
                        datetime.fromisoformat(
                            exp_schedule.at[index + 1, "departure_time"]
                        )
                        - datetime.fromisoformat(exp_schedule.at[index, "arrival_time"])
                    ).seconds // 60
                exp_schedule.loc[[index], ["pause"]] = pause_time
            exp_schedule.loc[[max(exp_schedule.index)], "pause"] = 0
        return exp_schedule

    def export_summary(self, path):
        """
        Export a summary of the vehicle's schedule to a file.

        Parameters
        ----------
        path : str
            The directory path where the summary file will be saved.

        Returns
        -------
        None

        """
        filename = pathlib.Path(path, "vehicle_id" + str(self.id) + ".csv")
        self.schedule.to_csv(filename)
