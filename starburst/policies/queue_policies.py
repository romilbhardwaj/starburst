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
                 wait_threshold: int = 0,
                 loop: bool = False,
                 preempt_cpu: bool = False,
                 linear_wait_constant: int = 1,
                 wait_until_scheduled: bool = False):
        
        self.wait_threshold = wait_threshold
        self.loop = loop
        self.preemmpt_cpu = preempt_cpu
        self.linear_wait_constant = linear_wait_constant
        self.estimated_state = {
                        "cpu": 0,
                        "memory": 0,
                        "gpu": 0,
                        #"nvidia.com/gpu": 0
                    }
        self.prevState = None
        self.currState = None
        self.curr_pods = None
        self.prev_pods = None
        self.wait_until_scheduled = wait_until_scheduled
        self.previous_function_call_time = 0
        self.prevJobName = None,
        self.prevJobStatus = None,
        self.onprem_only = False, 
        self.cloud_only = False, 
        super().__init__(onprem_manager, cloud_manager)
    '''
    Cluster state updates:
    (1) Once submitted yaml (cached/hardcoded state with no queries of cluster) -- SPECULATIVE w/ no cluster state 
    (2) Once submitted yaml, creates job on k8s (queries cluster's pod states) -- SPECULATIVE w/ pod state
    (3) Once submitted yaml, creates job on k8s, kills jobs if running for too long (queries cluster's pod states) -- SPECULATIVE w/ pod state and ROLLBACK
    (4) Once submitted yaml, creates job on k8s, creates a pod, and gets scheduled (queries cluster's node states) -- NON SPECULATIVE

    Waiting Policies
    # COMPUTE WAIT
    # runtime * resources * ---- Michael 

    Misc Todos
    #TODO: Mark jobs pending on the queue as pending, so they are not used to submit locally 
    #TODO: Don't run and wait for process queue until empty
    #TODO: Check job.submit_time and see if it has been waiting longer than the threshold
    #TODO: Check if the onprem cluster can fit the job
    #TODO: Compute job timeout values in parallel 
    # TODO: Figure out why cloud timeout fails  
    # TODO: Don't submit cluster to onprem if cluster state remains the same from a previous job
    # TODO: Retrieve the jobs on the onprem cluster and list them 
    # TODO: Compute job timeout values in parallel 
    '''
    def process_queue(self, job_queue: List[Job]):
        """ Process in FIFO order. Iterates over all jobs (no HoL blocking).
        If job has been waiting longer than a threshold, submit to cloud. """
        
        start_time = time.perf_counter()
        curr_time = time.perf_counter()
        retry = 0
        
        logger.debug(f'New process_queue function call || time since previous call {str(time.perf_counter() - self.previous_function_call_time)} | previous call time {str(self.previous_function_call_time)}')
        self.previous_function_call_time = time.perf_counter()
        if job_queue:
            curr_time = time.perf_counter()
            logger.debug("Retry(" + str(retry) + ") " + "Started queue loop : ~~~ --- " + str(curr_time-start_time))
            retry += 1
            job_id = 0
            cloud_start_time = time.time()
            for job in job_queue:
                loop_time = time.time()
                # if self.cloud_only # TODO: Include option for submission to onprem only
                event_wait_time = loop_time - job.job_event_queue_add_time
                wait_time = loop_time - job.job_submit_time
                time_out = wait_time > self.wait_threshold
                logger.debug(f'Cloud Timeout Submission Check || time out {time_out} | wait threshold {self.wait_threshold} | wait time {wait_time} | event queue wait time {event_wait_time} | curr time {loop_time} | submission time {job.job_submit_time} | event added time {job.job_event_queue_add_time}')
                if time_out:
                    logger.debug(f'Cloud Timeout Submission Entered || job {job.job_name} | queue {job_queue}')
                    curr_time = time.time()
                    self.cloud_manager.submit_job(job)
                    job_queue.remove(job)

            cloud_end_time = time.time()
            logger.debug(f"Looped through queue for cloud timeout || processing time {cloud_end_time - cloud_start_time}")
             
            onprem_start_time = time.time() 
            
            for job in job_queue:
                curr_time = time.perf_counter()
                logger.debug("Job(" + str(job_id) + ") " + "Next job on queue : ~~~ --- " + str(curr_time-start_time))
                job_id += 1 
                debug_time = time.time()
                
                if isinstance(self.prevJobName, tuple):
                    self.prevJobName = self.prevJobName[0]
                if isinstance(self.prevJobStatus, tuple):
                    self.prevJobStatus = self.prevJobStatus[0]
                logger.debug("prevJobName " +  str(self.prevJobName))
                logger.debug("prevJobStatus " +  str(self.prevJobStatus))
                if self.prevJobName: 
                    logger.debug("Looking for job ^^^ " +  str(self.prevJobName))
                    self.prevJobStatus = self.onprem_manager.job_running(job_name=self.prevJobName, namespace='default')
                    logger.debug("Prev job status ^^^ " +  str(self.prevJobStatus))
                    logger.debug("Looking for job ^^^ " +  str(self.prevJobName))
                logger.debug("prevJobName " +  str(self.prevJobName))
                logger.debug("prevJobStatus " +  str(self.prevJobStatus))
                
                # Added: time.time() - job.job_submit_time <= self.wait_threshold 
                # if self.cloud_only # TODO: Include option for submission to cloud only
                can_fit = self.onprem_manager.can_fit(job)
                logger.debug(f'Onprem Submission Check || Can fit: {can_fit} | Prev Job Name: {self.prevJobName} | Prev Job Status: {self.prevJobStatus}')
                if can_fit and (self.prevJobName == None or self.prevJobStatus == None or self.prevJobStatus == 1): 
                    logger.debug(f'Onprem Submission Entered || job {job.job_name} | queue {job_queue} | submission time {job.job_submit_time} | debug time {debug_time}' )                    
                    # TODO: Can_fit incorrectly executes here -- print out log of cluster state before and after submit_job
                    # TODO: Figure out how to properly parse the job data from the cluster event logs
                    job_queue.remove(job)
                    self.onprem_manager.submit_job(job)
                    self.prevJobName = job.job_name # NOTE: Previous job status computed outside if statement
                    # TODO: Verify if job.resources matches estimated state's key values
                    for r in job.resources:
                        self.estimated_state[r] += job.resources[r]
                    
                    #logger.debug(f"Onprem cluster can fit {job}. Submitting to onprem.")
                else:
                    logger.debug(f'Onprem submission adverted | job {job.job_name} | queue {job_queue} | submission time {job.job_submit_time} | debug time {debug_time}')
                    waited_time = time.time() - job.job_submit_time
                    #logger.debug(f"Waiting - Onprem cluster cannot fit {job}. Been waiting for {waited_time} seconds.")
                    if self.loop: 
                        pass
                    else: 
                        break
            onprem_end_time = time.time()
            logger.debug(f"Looped through queue for onprem submission || processing time {onprem_end_time - onprem_start_time}")
            curr_time = time.perf_counter()
            logger.debug(f'End of process_queue function call || total time {str(curr_time-start_time)}')
        else:
            logger.info("Job queue is empty.")
            curr_time = time.perf_counter()
            logger.debug(f'End of process_queue function call || total time {str(curr_time-start_time)}')
            return

