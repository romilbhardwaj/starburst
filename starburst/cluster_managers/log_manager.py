import math
import time as time
from starburst.types.job import Job
from starburst.utils import LogManager


class LogClusterManager(object):
    """
    A cluster manager acting over a log file.

    Assumes the log file is a cluster of infinite resources and can run jobs
    at infinite speed.
    """

    def __init__(self, cluster_name: str, log_file: str):
        self.cluster_name = cluster_name
        self.log_file = log_file
        self.logger = LogManager(cluster_name, self.log_file)

    def get_cluster_resources(self):
        """ Gets total cluster resources for each node."""
        cluster_resources = {}
        cluster_resources[self.cluster_name] = {
            'cpu': math.inf,
            'memory': math.inf,
            'gpu': math.inf
        }
        return cluster_resources

    def get_allocatable_resources(self):
        return self.get_cluster_resources()

    def can_fit(self, job: Job):
        return True

    def submit_job(self, job: Job):
        submission_time = job.job_event_queue_add_time
        log_string = (f'Job: {job.job_name} | '
                      f'Arrival: {submission_time} | '
                      f'Start:  {time.time()} | '
                      f'Runtime: {job.runtime} | ')
        for r_type, r_count in job.resources.items():
            log_string += f'{r_type}: {r_count} | '
        self.logger.append(log_string)
