from typing import Dict


class Job(object):
    """
    Represents a generic job for the Starburst job scheduler.
    """

    def __init__(self,
                 name: str,
                 arrival: float = -1,
                 runtime: float = -1,
                 yaml: Dict[str, object] = {},
                 resources: dict = {}):
        """
        Args:
            name (str): The name of the job.
            arrival (float): The timestamp when the job arrived in the system.
            runtime (float): The runtime (estimated in seconds) of the job.
            yaml (dict): The yaml configuration of the job.
            resources (dict): The resources required by the job.
        """
        self._name = name
        # Arrival here means when the user submits the jobs.
        self._arrival = arrival
        # Arrival here means when the Starburst scheduler receives the job.
        self._scheduler_arrival = -1
        self._start = -1
        self._end = -1

        # History of cluster assignments that the job has been assigned to.
        self._cluster_history = []

        self._runtime = None
        self._resources = resources
        self._timeout = None
        self._yaml = yaml

    def set_scheduler_arrival(self, time: float):
        self._scheduler_arrival = time

    def set_name(self, name: str):
        self._name = name

    def set_timeout(self, timeout: float):
        self._timeout = timeout

    def set_runtime(self, runtime: float):
        self._runtime = runtime

    def set_resources(self, resources: dict):
        self._resources = resources

    def get_submission_delay(self):
        """
        Returns the delay between the time of user job submission and
        the time the job is added to the Starburst job queue.
        """
        return self._scheduler_arrival - self.arrival

    @property
    def arrival(self):
        return self._arrival

    @property
    def end(self):
        return self._end

    @property
    def name(self):
        return self._name

    @property
    def resources(self):
        return self._resources

    @property
    def runtime(self):
        return self._runtime

    @property
    def scheduler_arrival(self):
        return self._scheduler_arrival

    @property
    def start(self):
        return self._start

    @property
    def timeout(self):
        return self._timeout

    @property
    def yaml(self):
        return self._yaml

    def __repr__(self):
        return (f"Job, name: {self.name}, submit: {self.arrival}, "
                f"start: {self.start}, "
                f"end: {self.end}, resources: {self.resources}")
