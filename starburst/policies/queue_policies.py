# Defines the waiting policies for the queue. A policy can introspect the queue and cluster and decide what action to take.
import logging
import time
from typing import Iterable, List
import heapq 

from starburst.cluster_managers.kubernetes_manager import KubernetesManager
from starburst.types.job import Job

logger = logging.getLogger(__name__)


def get_policy(policy: str):
    """ Get the policy object based on the policy name. """
    if policy == "fifo_onprem_only":
        return FIFOOnpremOnlyPolicy
    elif policy == "fifo_wait":
        return FIFOWaitPolicy
    elif policy == "time_estimator": 
        return TimeEstimatorPolicy
    else:
        raise NotImplementedError(f"Policy {policy} is not implemented.")


class BasePolicy(object):

    def __init__(self,
                 onprem_manager: KubernetesManager,
                 cloud_manager: KubernetesManager):
        self.onprem_manager = onprem_manager
        self.cloud_manager = cloud_manager

    def process_queue(self, queue):
        raise NotImplementedError("Policy must implement process method.")


class FIFOOnpremOnlyPolicy(BasePolicy):
    """ Implements FIFO submission to only onprem. Jobs wait indefinitely. """

    def __init__(self,
                 onprem_manager: KubernetesManager,
                 cloud_manager: KubernetesManager):
        super().__init__(onprem_manager, cloud_manager)

    def process_queue(self, job_queue: List[Job]):
        """ Process in FIFO order. Block the queue if the onprem cluster cannot fit the job and return. """
        # Check if the onprem cluster can fit the job
        if job_queue:
            if self.onprem_manager.can_fit(job_queue[0]):
                # Remove from queue
                job = job_queue.pop(0)
                # Submit the job
                self.onprem_manager.submit_job(job)
                logger.info(
                    f"Onprem cluster can fit the {job}. Submitting the job.")
            else:
                logger.info(
                    "Onprem cluster cannot fit the job. Waiting for it to become available.")
                return
        else:
            logger.info("Job queue is empty.")
            return


class FIFOWaitPolicy(BasePolicy):
    """ Implements FIFO submission to only onprem. If job has been waiting longer than a threshold, submit to cloud. """

    def __init__(self,
                 onprem_manager: KubernetesManager,
                 cloud_manager: KubernetesManager,
                 wait_threshold: int = 0):
        self.wait_threshold = wait_threshold
        super().__init__(onprem_manager, cloud_manager)

    def process_queue(self, job_queue: List[Job]):
        """ Process in FIFO order. Iterates over all jobs (no HoL blocking).
        If job has been waiting longer than a threshold, submit to cloud. """
        # Check if the onprem cluster can fit the job
        if job_queue:
            for job in job_queue:
                if self.onprem_manager.can_fit(job):
                    # Remove from queue
                    job_queue.remove(job)
                    # Submit the job
                    self.onprem_manager.submit_job(job)
                    logger.debug(
                        f"Onprem cluster can fit {job}. Submitting to onprem.")
                else:
                    # Check job.submit_time and see if it has been waiting longer than the threshold
                    if time.time() - job.job_submit_time > self.wait_threshold:
                        # Submit to cloud
                        self.cloud_manager.submit_job(job)
                        logger.debug(
                            f"Deadline passed, spilling over {job}. Submitting to cloud.")
                        # Remove from queue
                        job_queue.remove(job)
                    else:
                        waited_time = time.time() - job.job_submit_time
                        logger.debug(
                            f"Waiting - Onprem cluster cannot fit {job}. Been waiting for {waited_time} seconds.")

        else:
            logger.info("Job queue is empty.")
            return

class TimeEstimatorPolicy(BasePolicy):
    def __init__(self,
                 onprem_manager: KubernetesManager,
                 cloud_manager: KubernetesManager,
                 wait_threshold: int = 0,
                 job_data: dict = {}):
        self.job_data = job_data
        self.running_jobs = []
        super().__init__(onprem_manager, cloud_manager)

    def process_queue(self, job_queue: List[Job]):
        # TODO: Retrieve job times of jobs currently being executed and blocking the new job 
        # TODO: Determine running jobs based on submit_time + job_runtime
        # TODO: Keep running job end times stored on min heap -- pop values if current time is ever greater than existing job 
        #running_jobs = []

        if job_queue:
            while (len(self.running_jobs) > 0) and self.running_jobs[0][0] < time.time(): 
                heapq.heappop(self.running_jobs)
            
            job = job_queue[0]
            job_index = int(job.job_name)
            job_runtime = self.job_data[job_index]['job_duration']
            # TODO: Determine how to job_start_time to replace job_submit_time
            job_end_time = job.job_submit_time + job_runtime
            if self.onprem_manager.can_fit(job):
                # Remove from queue
                job_queue.pop(0)
                # Submit the job
                self.onprem_manager.submit_job(job)
                logger.debug(
                    f"Onprem cluster can fit {job}. Submitting to onprem.")
                heapq.heappush(self.running_jobs, (job_end_time, job_index))
            else:
                # Check job.submit_time and see if it has been waiting longer than the threshold
                if len(self.running_jobs) > 1: #job_runtime > running_jobs[0][1] - time.time(): 
                    # TODO: Determine minimum time for enough jobs within a single node to complete with sufficient resources for upcoming job
                    first_job_to_finish_time, first_job_to_finish = self.running_jobs[0]
                    # Runs locally if time job has to wait is less than job runtime, else gets submitted to cloud 
                    if job_runtime > first_job_to_finish_time - time.time(): 
                        # Submit to cloud
                        self.cloud_manager.submit_job(job)
                        logger.debug(
                            f"Deadline passed, spilling over {job}. Submitting to cloud.")
                        # Remove from queue
                        job_queue.remove(job)
                    else:
                        waited_time = time.time() - job.job_submit_time
                        logger.debug(
                            f"Waiting - Onprem cluster cannot fit {job}. Been waiting for {waited_time} seconds.")
                else:
                    waited_time = time.time() - job.job_submit_time
                    logger.debug(
                        f"Waiting - Onprem cluster cannot fit {job}. Been waiting for {waited_time} seconds.")


class HOLBlockingPolicy(BasePolicy):
    def __init__(self,
                 onprem_manager: KubernetesManager,
                 cloud_manager: KubernetesManager):
        self.onprem_manager = onprem_manager
        self.cloud_manager = cloud_manager


    def process_queue(self, queue):
        # TODO: Siyuan -- If front of queue is waiting loop throughout queue and submit jobs
        raise NotImplementedError("Policy must implement process method.")