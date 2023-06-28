# Defines the waiting policies for the queue. A policy can introspect the
# queue and cluster and decide what action to take.
# TODO(mluo): Make Kubernetes Manager a sublcass of a general manager class.
# TODO(mluo): Make cloud_manager into LogManager, KubernetesManager, and
# SkypilotManager.
import logging
import time
from typing import Dict, List

from starburst.cluster_managers.kubernetes_manager import KubernetesManager
from starburst.policies import waiting_policies
from starburst.types.job import Job

logger = logging.getLogger(__name__)

POLICY_CONFIG_TEMPLATE = {
    'waiting_policy': 'infinite',
    'waiting_coeff': -1,
    'queue_policy': 'fifo',
    'min_waiting_time': 10,
    'loop': False,
}


def get_policy(policy_config: Dict[str, str]):
    """ Get the policy object based on the policy name. """
    if policy_config['waiting_policy'] is None:
        return FIFOOnpremOnlyPolicy
    else:
        return FIFOWaitPolicy


class BasePolicy(object):

    def __init__(self, onprem_manager: KubernetesManager,
                 cloud_manager: KubernetesManager):
        self.onprem_manager = onprem_manager
        self.cloud_manager = cloud_manager

    def process_queue(self, queue):
        raise NotImplementedError("Policy must implement process method.")


# Similar to YARN CapacityScheduler. Jobs wait in queue until the onprem cluster can fit the job.
class FIFOOnpremOnlyPolicy(BasePolicy):
    """
    Implements FIFO submission to only onprem. Jobs wait indefinitely
    in the queue until the onprem cluster can fit the job.
    """

    def process_queue(self, job_queue: List[Job]):
        """
        Process in FIFO order. Block the queue if the onprem cluster
        cannot fit the job and return.
        """
        if job_queue:
            # Check if the onprem cluster can fit the job
            if self.onprem_manager.can_fit(job_queue[0]):
                # Remove from queue
                job = job_queue.pop(0)
                # Submit the job
                self.onprem_manager.submit_job(job)


class FIFOWaitPolicy(BasePolicy):
    """ Implements FIFO submission to only onprem. If job has been waiting longer than a threshold, submit to cloud. """

    def __init__(
        self,
        onprem_manager: KubernetesManager,
        cloud_manager: KubernetesManager,
        spill_to_cloud: str = 'cluster',
        policy_config: Dict[str, str] = POLICY_CONFIG_TEMPLATE,
        log_file: str = None,
    ):
        super().__init__(onprem_manager, cloud_manager)
        self.spill_to_cloud = spill_to_cloud
        copy_dict = dict(POLICY_CONFIG_TEMPLATE)
        copy_dict.update(policy_config)
        self.policy_config = copy_dict

        self.waiting_policy = policy_config['waiting_policy']
        self.waiting_coeff = policy_config['waiting_coeff']
        self.queue_policy = policy_config['queue_policy']
        self.loop = policy_config['loop']
        self.min_waiting_time = policy_config['min_waiting_time']
        self.log_file = log_file

        self.waiting_policy_cls = waiting_policies.get_waiting_policy_cls(
            self.waiting_policy)(self.waiting_coeff)

        self.spilled_jobs_path = self.log_file
        with open(self.spilled_jobs_path, "a") as f:
            f.write("Scheduler spun up! \n")

        self.prevJobName = None,
        self.prevJobStatus = None,

    def process_queue(self, job_queue: List[Job]):

        # Loop through queue to release jobs which timeout
        if job_queue:
            for job in job_queue:
                wait_time = time.time() - job.job_submit_time
                if job.timeout is None:
                    job.set_timeout(
                        self.waiting_policy_cls.compute_timeout(job))
                timeout = max(job.timeout, self.min_waiting_time)
                job_timed_out = wait_time >= timeout
                if job_timed_out:
                    if self.spill_to_cloud == 'cluster':
                        self.cloud_manager.submit_job(job)
                    elif self.spill_to_cloud == 'log':
                        gpu_resources = job.resources['gpu']
                        submission_time = job.job_event_queue_add_time
                        with open(self.spilled_jobs_path, "a") as f:
                            f.write(
                                f'Cloud Job || job name {job.job_name} | '
                                f'estimated cloud start time {time.time()} | '
                                f'estimated job duration {job.runtime} | '
                                f'submission time {submission_time} | '
                                f'gpus {gpu_resources} \n')
                    else:
                        raise ValueError('Invalid spill_to_cloud value: '
                                         f'{self.spill_to_cloud}')
                    job_queue.remove(job)

            # Loop through the queue for submitting jobs to on-prem.
            for job in job_queue:
                if isinstance(self.prevJobName, tuple):
                    self.prevJobName = self.prevJobName[0]
                if isinstance(self.prevJobStatus, tuple):
                    self.prevJobStatus = self.prevJobStatus[0]
                logger.debug(
                    f'prev job name {str(self.prevJobName)} | prev job status {str(self.prevJobStatus)} | type {type(self.prevJobName)}'
                )

                if self.prevJobName:
                    self.prevJobStatus = self.onprem_manager.job_running(
                        job_name=self.prevJobName, namespace='default')
                    logger.debug(
                        f'Updated Previous Job Status || prev job name {str(self.prevJobName)} | prev job status {str(self.prevJobStatus)} | type {type(self.prevJobName)}'
                    )

                can_fit = self.onprem_manager.can_fit(job)
                logger.debug(
                    f'Onprem Submission Check || Can fit: {can_fit} | Prev Job Name: {self.prevJobName} | Prev Job Status: {self.prevJobStatus}'
                )
                # TODO: Set previous job completed instead of previous job
                # scheduled -- ERROR
                if can_fit and (self.prevJobName == None or self.prevJobStatus
                                == None or self.prevJobStatus == 1):
                    job_queue.remove(job)
                    self.onprem_manager.submit_job(job)
                    self.prevJobName = job.job_name
                else:
                    if self.loop:
                        continue
                    break
