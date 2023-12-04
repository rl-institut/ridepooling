import pandas as pd
from datetime import timedelta


class Pooling:
    """
    Represents a ride pooling system that manages ride schedules.

    This class calculates and optimizes ride schedules, taking into account various factors like delay, balance, pooling, and distance.

    Attributes
    ----------
    distance : pd.DataFrame
        A DataFrame containing distance information.
    requests_denied_list : list
        A list to store ride requests that have been denied during scheduling.

    Methods
    -------
    creating_possible_schedules(vehicle_list, request, schedule_dictionary, cfg_dict)
        Create possible ride schedules for a given request.
    check_occupation_delay(schedule_dictionary, waytime, cfg_dict)
        Check the occupation and delay for ride schedules.
    calculate_score(schedule_dictionary, cfg_dict)
        Calculate a score for each ride schedule.
    calculating_distance(schedule)
        Calculate the distance traveled for a given schedule.
    """
    def __init__(self, vehicle_list, request_list, cfg_dict, waytime, distance):
        """
        Initialize a Pooling simulation with given data.

        Parameters
        ----------
        vehicle_list : list
            A list of vehicle objects participating in the simulation.
        request_list : list
            A list of ride request objects.
        cfg_dict : dict
            A dictionary containing configuration data for the simulation.
        waytime : pd.DataFrame
            A DataFrame representing waytime data between stations.
        distance : pd.DataFrame
            A DataFrame representing distance data between stations.

        Returns
        -------
        None

        """
        self.distance = distance
        self.waytime_max = waytime.values.max()
        self.requests_denied_list = []
        counter = 0
        for request in request_list:
            print(
                "\r"
                + str(int(counter / (len(request_list) - 1) * 100))
                + " % completed   ",
                end=" ",
                flush=True,
            ),
            self.schedule_dictionary = {}
            self.schedule_dictionary = self.creating_possible_schedules(
                vehicle_list, request, self.schedule_dictionary, cfg_dict
            )
            self.schedule_dictionary = self.check_occupation_delay(
                self.schedule_dictionary, waytime, cfg_dict
            )
            if len(self.schedule_dictionary) != 0:
                self.best_schedule = self.calculate_score(
                    self.schedule_dictionary, cfg_dict
                )
                self.best_schedule["vehicle"].update_schedule(
                    self.best_schedule["schedule"]
                )
            else:
                self.requests_denied_list.append(request)
            counter += 1

    def creating_possible_schedules(
        self, vehicle_list, request, schedule_dictionary, cfg_dict
    ):
        """
        Create possible schedules for ride requests.

        This function generates possible schedules for a given ride request and updates
        the schedule dictionary.

        Parameters
        ----------
        vehicle_list : list
            A list of vehicle objects participating in the simulation.
        request : Request
            A ride request object.
        schedule_dictionary : dict
            A dictionary storing schedule entries.
        cfg_dict : dict
            A dictionary containing configuration data for the simulation.

        Returns
        -------
        dict
            Updated schedule dictionary.

        """
        id = 0
        for vehicle in vehicle_list:
            # getting relevant schedule
            schedule = vehicle.schedule.loc[
                vehicle.schedule["planed"]
                > (request.start_time - timedelta(minutes=float(float(self.waytime_max) + 5.0)))
            ]

            # creating start and destination frame
            start_frame = pd.DataFrame(
                [
                    [
                        request.start,
                        request.passangers,
                        request.start_time,
                        request.request_id,
                        request.start_time,
                        0,
                        request.passangers,
                        request.delay_max,
                    ]
                ],
                columns=[
                    "station",
                    "boarding",
                    "promissed_time",
                    "request_id",
                    "planed",
                    "delay",
                    "occupation",
                    "max_delay",
                ],
                index=[1],
            )
            destination_frame = pd.DataFrame(
                [
                    [
                        request.destination,
                        -request.passangers,
                        request.start_time + timedelta(minutes=request.waytime) + timedelta(minutes=cfg_dict["weights"]["standing_time"]),
                        request.request_id,
                        request.start_time,
                        0,
                        -request.passangers,
                        request.delay_max,
                    ]
                ],
                columns=[
                    "station",
                    "boarding",
                    "promissed_time",
                    "request_id",
                    "planed",
                    "delay",
                    "occupation",
                    "max_delay",
                ],
                index=[2],
            )

            # putting together a schedule
            if len(schedule) == 0:
                schedule = pd.concat([start_frame, destination_frame])
                schedule.sort_index()
                index_final = pd.Series(
                    [len(vehicle.schedule) + 1, len(vehicle.schedule) + 2]
                )
                schedule = schedule.set_index(index_final)
                entry = {
                    id: {
                        "vehicle": vehicle,
                        "delay_old": 0,
                        "distance_old": 0,
                        "schedule": schedule,
                        "balance": len(vehicle.schedule),
                        "pooling_rate": 0,
                        "delay": 0,
                        "distance": 0,
                        "delay_score": 0,
                        "pooling_score": 0,
                        "balance_score": 0,
                        "distance_score": 0,
                        "score": 0,
                    }
                }
                id += 1

                schedule_dictionary.update(entry)
            else:
                # getting relevant index:
                index_final_start = min(schedule.index)
                index_new = [*range(1, len(schedule) + 1, 1)]
                delay_old = schedule["delay"].sum()
                distance_old = self.calculating_distance(schedule)
                new_list = []
                for i in index_new:
                    new_list.append(i * 3)
                index_new = new_list
                schedule = schedule.set_index(pd.Series(index_new))
                index_relevant = []
                for i in schedule.index:
                    if schedule.at[i, "promissed_time"] < (
                        request.start_time
                        + timedelta(minutes=request.waytime)
                        + timedelta(minutes=cfg_dict["weights"]["delay_max"])
                    ):
                        index_relevant.append(i)
                start_loop = 1
                if len(index_relevant) == 0:
                    break
                while start_loop < (max(index_relevant) + 3):
                    destination_loop = start_loop + 1
                    while destination_loop < (max(index_relevant) + 3):
                        entry = {
                            id: {
                                "vehicle": vehicle,
                                "delay_old": delay_old,
                                "distance_old": distance_old,
                                "schedule": schedule,
                                "balance": len(vehicle.schedule),
                                "pooling_rate": 0,
                                "delay": 0,
                                "distance": 0,
                                "delay_score": 0,
                                "pooling_score": 0,
                                "balance_score": 0,
                                "distance_score": 0,
                                "score": 0,
                            }
                        }

                        # give new index
                        start_frame = start_frame.set_index(pd.Series([start_loop]))
                        destination_frame = destination_frame.set_index(
                            pd.Series([destination_loop])
                        )

                        # put together
                        schedule_1 = pd.concat(
                            [schedule, start_frame, destination_frame]
                        )
                        schedule_1 = schedule_1.sort_index()
                        # index_final = pd.Series(
                        # list(range(len(vehicle.schedule), len(schedule) + 2))
                        # )
                        index_final = [
                            *range(
                                index_final_start,
                                len(schedule_1) + index_final_start,
                                1,
                            )
                        ]
                        schedule_1 = schedule_1.set_index(pd.Series(index_final))
                        entry[id]["schedule"] = schedule_1
                        schedule_dictionary.update(entry)
                        id += 1
                        destination_loop += 3
                    start_loop += 3
        return schedule_dictionary

    def check_occupation_delay(self, schedule_dictionary, waytime, cfg_dict):
        """
        Check vehicle occupation and delay for generated schedules.

        This function checks the occupation and delay of vehicles in generated schedules
        and removes schedules that exceed maximum occupation or delay.

        Parameters
        ----------
        schedule_dictionary : dict
            A dictionary storing schedule entries.
        waytime : pd.DataFrame
            A DataFrame representing waytime data between stations.
        cfg_dict : dict
            A dictionary containing configuration data for the simulation.

        Returns
        -------
        dict
            Updated schedule dictionary.

        """
        delete_array = []
        for entry in schedule_dictionary:
            schedule = schedule_dictionary[entry]["schedule"]
            index_list = schedule.index
            for index in schedule.index:
                if index == index_list[0]:
                    schedule.at[index, "occupation"] = schedule.at[index, "occupation"]
                    schedule.at[index, "delay"] = int(
                        (
                            schedule.at[index, "planed"]
                            - schedule.at[index, "promissed_time"]
                        ).seconds
                        // 60
                    )
                else:
                    schedule.at[index, "occupation"] = (
                        schedule.at[index - 1, "occupation"]
                        + schedule.at[index, "boarding"]
                    )
                    time_delta = timedelta(
                        minutes=float(
                            waytime.loc[
                                schedule.at[index - 1, "station"],
                                schedule.at[index, "station"],
                            ]
                        )
                    )
                    standing_time = timedelta(minutes=cfg_dict["weights"]["standing_time"])
                    schedule.at[index, "planed"] = (
                        schedule.at[index - 1, "planed"] + time_delta + standing_time
                    )
                    schedule.at[index, "delay"] = int(
                        (
                            schedule.at[index, "planed"]
                            - schedule.at[index, "promissed_time"]
                        ).seconds
                        // 60
                    )

                    # check: letting people get out, bevor letting new in
                    if index + 1 in schedule.index:
                        if (
                            schedule.at[index, "station"]
                            == schedule.at[index + 1, "station"]
                            and schedule.at[index, "boarding"] > 0
                            and schedule.at[index + 1, "boarding"] < 0
                        ):
                            if entry not in delete_array:
                                delete_array.append(entry)
            schedule_dictionary[entry]["pooling_rate"] = schedule[
                "occupation"
            ].sum() / len(schedule)
            if (
                schedule["delay"].max() > cfg_dict["weights"]["delay_max"]
                or schedule["occupation"].max()
                > schedule_dictionary[entry]["vehicle"].seats
            ):
                if entry not in delete_array:
                    delete_array.append(entry)
            else:
                schedule_dictionary[entry]["schedule"] = schedule
        for entry in delete_array:
            del schedule_dictionary[entry]
        return schedule_dictionary

    def calculate_score(self, schedule_dictionary, cfg_dict):
        """
        Calculate scores for generated schedules.

        This function calculates scores for generated schedules based on delay, balance,
        pooling rate, and distance factors.

        Parameters
        ----------
        schedule_dictionary : dict
            A dictionary storing schedule entries.
        cfg_dict : dict
            A dictionary containing configuration data for the simulation.

        Returns
        -------
        dict
            Information about the best schedule.

        """
        # calculating delay_score
        delay_list = []
        for entry in schedule_dictionary:
            delay = (
                schedule_dictionary[entry]["schedule"]["delay"].sum()
                - schedule_dictionary[entry]["delay_old"]
            )
            schedule_dictionary[entry]["delay"] = delay
            delay_list.append(delay)
        for entry in schedule_dictionary:
            if max(delay_list) == 0:
                schedule_dictionary[entry]["delay_score"] = 1
            else:
                schedule_dictionary[entry]["delay_score"] = 1 - schedule_dictionary[
                    entry
                ]["delay"] / max(delay_list)

        # calculating balance
        balance_list = []
        for entry in schedule_dictionary:
            balance_list.append(len(schedule_dictionary[entry]["vehicle"].schedule))
        for entry in schedule_dictionary:
            if max(balance_list) == 0:
                schedule_dictionary[entry]["balance_score"] = 1
            else:
                schedule_dictionary[entry]["balance_score"] = 1 - len(
                    schedule_dictionary[entry]["vehicle"].schedule
                ) / max(balance_list)

        # Calculating pooling score
        pooling_list = []
        for entry in schedule_dictionary:
            pooling_list.append(schedule_dictionary[entry]["pooling_rate"])
        for entry in schedule_dictionary:
            if max(pooling_list) == 0:
                schedule_dictionary[entry]["pooling_score"] = 0
            else:
                schedule_dictionary[entry]["pooling_score"] = schedule_dictionary[
                    entry
                ]["pooling_rate"] / max(pooling_list)

        # calculating distance_score
        distance_list = []
        for entry in schedule_dictionary:
            distance_new = self.calculating_distance(
                schedule_dictionary[entry]["schedule"]
            )
            schedule_dictionary[entry]["distance"] = (
                distance_new - schedule_dictionary[entry]["distance_old"]
            )
            distance_list.append(
                distance_new - schedule_dictionary[entry]["distance_old"]
            )
        for entry in schedule_dictionary:
            if max(distance_list) == 0:
                schedule_dictionary[entry]["distance_score"] = 1
            else:
                schedule_dictionary[entry]["distance_score"] = 1 - (
                    schedule_dictionary[entry]["distance"] / max(distance_list)
                )

        # pick best schedule
        score_list = []
        entry_list = []
        for entry in schedule_dictionary:
            score = (
                schedule_dictionary[entry]["delay_score"]
                * cfg_dict["weights"]["delay_factor"]
                + schedule_dictionary[entry]["balance_score"]
                * cfg_dict["weights"]["balance_factor"]
                + schedule_dictionary[entry]["pooling_score"]
                * cfg_dict["weights"]["pooling_factor"]
                + schedule_dictionary[entry]["distance_score"]
                * cfg_dict["weights"]["distance_factor"]
            )
            entry_list.append(entry)
            schedule_dictionary[entry]["score"] = score
            score_list.append(score)
        index_best_schedule = score_list.index(max(score_list))
        best_entry = schedule_dictionary[entry_list[index_best_schedule]]
        return best_entry

    def calculating_distance(self, schedule):
        """
        Calculate the total distance traveled in a schedule.

        This function calculates the total distance traveled in a given schedule.

        Parameters
        ----------
        schedule : pd.DataFrame
           A DataFrame representing a vehicle's schedule.

        Returns
        -------
        float
           The total distance traveled in the schedule.

        """
        distance_list = []
        for i in schedule.index:
            if i == max(schedule.index):
                continue
            else:
                start_id = schedule.at[i, "station"]
                destination_id = schedule.at[i + 1, "station"]
                distance_list.append(float(self.distance.loc[start_id, destination_id]))
        distance = sum(distance_list)
        return distance
