class Request:
    """
    Represents a ride request with attributes and methods for status management.

    This class manages ride request attributes and the status of ride requests.

    Attributes
    ----------
    start : int
        The starting station for the ride request.
    destination : int
        The destination station for the ride request.
    request_id : int
        A unique identifier for the ride request.
    start_time : datetime
        The time the ride request is made.
    passangers : int
        The number of passengers in the ride request.
    status : bool
        The status of the ride request (accepted or denied).
    time : datetime
        The scheduled time for the ride request.
    delay_max : float
        The maximum allowable delay for the ride request.
    waytime : float
        The estimated travel time between the start and destination.

    Methods
    -------
    accept_status(decision)
        Set the status of the ride request (accepted or denied).

    """

    def __init__(
        self, start_id, dest_id, id, start_time, passangers, time, delay_max, waytime
    ):
        """
        Initialize a Request object with the provided information.

        Parameters
        ----------
        start_id : int
            The ID of the starting station.
        dest_id : int
            The ID of the destination station.
        id : int
            The unique identifier for the request.
        start_time : datetime
            The start time of the request.
        passangers : int
            The number of passengers associated with the request.
        time : datetime
            The time of the request got sended
        delay_max : float
            The maximum allowable delay for the request.
        waytime : pd.DataFrame
            A DataFrame representing waytime information between stations.

        Returns
        -------
        None

        """
        self.start = start_id
        self.destination = dest_id
        self.request_id = id
        self.start_time = start_time
        self.passangers = passangers
        self.status = (
            True  # if request gets accepted True, if request gets denied False
        )
        self.time = time
        self.delay_max = delay_max
        self.waytime = waytime

    def accept_status(self, decision):
        """
        Update the status of the request based on the decision made in the pooling process.

        Parameters
        ----------
        decision : bool
            The decision on whether to accept or deny the request. True for acceptance, False for denial.

        Returns
        -------
        None

        """
        if decision == True:
            self.status = True
        if decision == False:
            self.status = False
