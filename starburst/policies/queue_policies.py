# Defines the waiting policies for the queue. A policy can introspect the queue and cluster and decide what action to take.
import logging
from typing import Iterable, List

from starburst.cluster_managers.kubernetes_manager import KubernetesManager
from starburst.types.job import Job


logger = logging.getLogger(__name__)

def get_policy(policy: str):
    """ Get the policy object based on the policy name. """
    if policy == "fifo_onprem_only":
        return FIFOOnpremOnlyPolicy
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
                logger.info(f"Onprem cluster can fit the {job}. Submitting the job.")
            else:
                logger.info("Onprem cluster cannot fit the job. Waiting for it to become available.")
                return
        else:
            logger.info("Job queue is empty.")
            return