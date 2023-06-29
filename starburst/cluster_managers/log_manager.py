import time as time
from starburst.types.job import Job


class LogManager(object):
    """
    A cluster manager acting over a log file.

    Assumes the log file is a cluster of infinite resources and can run jobs at infinite speed.
    """

    def __init__(self, cluster_name: str, log_file: str):
        self.cluster_name = cluster_name
        self.log_file = log_file

    def submit_job(self, job: Job):
        gpu_resources = job.resources['gpu']
        submission_time = job.job_event_queue_add_time
        with open(self.log_file, "a") as f:
            f.write(f'Cloud Job || job name {job.job_name} | '
                    f'estimated cloud start time {time.time()} | '
                    f'estimated job duration {job.runtime} | '
                    f'submission time {submission_time} | '
                    f'gpus {gpu_resources} \n')
