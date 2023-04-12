# Defines the waiting policies for the queue. A policy can introspect the queue and cluster and decide what action to take.
import logging
import time
from typing import Iterable, List

from starburst.cluster_managers.kubernetes_manager import KubernetesManager
from starburst.types.job import Job

logger = logging.getLogger(__name__)


def get_policy(policy: str):
    """ Get the policy object based on the policy name. """
    if policy == "fifo_onprem_only":
        return FIFOOnpremOnlyPolicy
    if policy == "fifo_wait":
        return FIFOWaitPolicy
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
                 wait_threshold: int = 60):
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
