class Job(object):
    """
    Represents a Kubernetes job in the Starburst cluster scheduler.
    """

    def __init__(self,
                 job_name: str,
                 job_submit_time: float,
                 job_start_time: float,
                 job_end_time: float,
                 job_yaml: str,
                 resources: dict = None):
        self.job_name = job_name
        self.job_submit_time = job_submit_time
        self.job_event_queue_add_time = None
        self.job_start_time = job_start_time
        self.job_end_time = job_end_time
        self.job_yaml = job_yaml

        self._runtime = None
        self._resources = resources
        self._timeout = None

    @property
    def name(self):
        return self.job_name

    @property
    def resources(self):
        return self._resources

    @property
    def runtime(self):
        return self._runtime

    @property
    def timeout(self):
        return self._timeout

    def set_event_queue_add_time(self, time: float):
        self.job_event_queue_add_time = time

    def set_timeout(self, timeout: float):
        self._timeout = timeout

    def set_runtime(self, runtime: float):
        self._runtime = runtime

    def set_resources(self, resources: dict):
        self._resources = resources

    def __repr__(self):
        return (f"Job, name: {self.job_name}, submit: {self.job_submit_time}, "
                f"start: {self.job_start_time}, "
                f"end: {self.job_end_time}, resources: {self.resources}")
