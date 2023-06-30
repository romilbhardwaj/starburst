import random


class Job(object):
    """ Job object. """

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
        self.resources = resources  # Ideally read from job yaml
        self.job_id = str(random.randint(0, 1000000))

    def __repr__(self):
        return f"Job, name: {self.job_name}, submit: {self.job_submit_time}, start: {self.job_start_time}, " + \
               f"end: {self.job_end_time}, resources: {self.resources}"
