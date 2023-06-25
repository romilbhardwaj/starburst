# Defines the waiting policies for the queue. A policy can introspect the queue and cluster and decide what action to take.
import logging
import time
from typing import Iterable, List
import heapq 
import os 

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
                 policy: str = 'fixed',
                 job_data: dict = {},
                 batch_repo: int = 0,
                 index: int = 0, 
                 ):
        
        self.wait_threshold = wait_threshold
        self.policy = policy
        self.loop = loop
        self.preemmpt_cpu = preempt_cpu
        self.linear_wait_constant = linear_wait_constant
        self.estimated_state = {
                        "cpu": 0,
                        "memory": 0,
                        "gpu": 0,
                        #"nvidia.com/gpu": 0
                    }
        

        self.previous_function_call_time = 0
        self.prevJobName = None,
        self.prevJobStatus = None,
        self.onprem_only = False, 
        self.cloud_only = False, 
        if isinstance(job_data, tuple):
            self.job_data = self.job_data[0]
        else: 
            self.job_data = job_data

        self.total_workload_volume = 0
        self.total_workload_time = 0
        self.total_workload_surface_area = 0
        self.total_jobs = 0
        assert len(self.job_data) >= 1, "Job data is empty, job submission is bugged." 
        self.workload_type = self.job_data[0]['workload_type']
        logger.debug(f'all jobs data {self.job_data}')
        for job_id in self.job_data:
            job = self.job_data[job_id]
            logger.debug(f'job data {job}')
            self.total_jobs += 1
            self.total_workload_time += job['job_duration']
            resources = job['resources']
            if self.workload_type == 'cpu_sleep':
                self.total_workload_surface_area += resources['cpu']
                self.total_workload_volume += job['job_duration'] * resources['cpu']
            else: 
                self.total_workload_surface_area += resources['gpu']
                self.total_workload_volume += job['job_duration'] * resources['gpu']
            cpus = resources['cpu']
            logger.debug(f'total cpu {cpus}')

        self.max_tolerance = 0.25 #Increase in JCT they want over No-Wait
        
        # TODO: Recompute compute wait coefficient -> use gpu_sizes, gpu_dist from hyperparameters value
        # TODO: Improve terminology 
        self.constant_wait_coefficient = self.max_tolerance * (self.total_workload_time) / self.total_jobs

        self.runtime_wait_coefficient = (self.linear_wait_constant * self.total_jobs) / self.total_workload_time # TODO: Computing incorrect value
        self.resource_wait_coefficient = (self.linear_wait_constant * self.total_jobs) / self.total_workload_surface_area # TODO: Computing incorrect value
        self.compute_wait_coefficient = (self.linear_wait_constant * self.total_jobs) / self.total_workload_volume # TODO: Computing incorrect value
        
        self.avg_job_size = self.total_workload_surface_area/self.total_jobs
        
        self.compute_wait_coefficient = self.max_tolerance/self.avg_job_size

        self.spilled_jobs_path = f'../sweep_logs/{batch_repo}/events/{index}.log'
        event_path = f'../sweep_logs/{batch_repo}/events/'
        if not os.path.exists(event_path):
            os.mkdir(event_path)
        self.spill_to_cloud = self.job_data[0]['spill_to_cloud'] # TODO: Verify if this works as intended
        with open(self.spilled_jobs_path, "a") as f:
            f.write("Scheduler spun up! \n")
        


        # TODO: Compute average job_size directly from input distribution jobs['hyperparameters']['gpu_dist'] *  jobs['hyperparameters']['gpu_sizes']
        
        logger.debug(f'Optimal coefficients || constant wait coefficient {self.constant_wait_coefficient} | runtime wait coefficient {self.runtime_wait_coefficient} | resource wait coefficient {self.resource_wait_coefficient} | compute wait coefficient {self.compute_wait_coefficient}')
        
        super().__init__(onprem_manager, cloud_manager)
    '''
    Cluster state updates:
    (1) Once submitted yaml (cached/hardcoded state with no queries of cluster) -- SPECULATIVE w/ no cluster state 
    (2) Once submitted yaml, creates job on k8s (queries cluster's pod states) -- SPECULATIVE w/ pod state
    (3) Once submitted yaml, creates job on k8s, kills jobs if running for too long (queries cluster's pod states) -- SPECULATIVE w/ pod state and ROLLBACK
    (4) Once submitted yaml, creates job on k8s, creates a pod, and gets scheduled (queries cluster's node states) -- NON SPECULATIVE

    Waiting Policies
    (1) Constant Wait 
    (2) Compute Wait = runtime * resources
    (3) Starburst = compute wait + loop + cpu balking 

    Misc Todos
    # TODO: Mark jobs pending on the queue as pending, so they are not used to submit locally 
    # TODO: Don't run and wait for process queue until empty
    # TODO: Check job.submit_time and see if it has been waiting longer than the threshold
    # TODO: Check if the onprem cluster can fit the job
    # TODO: Compute job timeout values in parallel 
    # TODO: Figure out why cloud timeout fails  
    # TODO: Don't submit cluster to onprem if cluster state remains the same from a previous job
    # TODO: Retrieve the jobs on the onprem cluster and list them 
    # TODO: Compute job timeout values in parallel 
    # TODO: Can_fit incorrectly executes here -- print out log of cluster state before and after submit_job
    # TODO: Figure out how to properly parse the job data from the cluster event logs
    '''
    def process_queue(self, job_queue: List[Job]):
        """ Process in FIFO order. Iterates over all jobs (no HoL blocking).
        If job has been waiting longer than a threshold, submit to cloud. """
        start_time = time.perf_counter()
        # logger.debug(f'New process_queue function call || time since previous call {str(time.perf_counter() - self.previous_function_call_time)} | previous call time {str(self.previous_function_call_time)}')
        self.previous_function_call_time = time.perf_counter()
        if job_queue:
            cloud_start_time = time.time()
            
            for job in job_queue:
                if self.policy == 'onprem_only': 
                    break 
                # if self.cloud_only # TODO: Include option for submission to onprem only
                loop_time = time.time()
                event_wait_time = loop_time - job.job_event_queue_add_time
                wait_time = loop_time - job.job_submit_time
                job_id = int(job.job_name[4:])
                job_duration = self.job_data[job_id]['job_duration']
                job_resource = job.resources['gpu']
                timeout = 0
                job_timed_out = False
                if self.policy == 'constant': 
                    timeout = self.wait_threshold
                    job_timed_out = wait_time > max(timeout, 15) #timeout
                elif self.policy == 'constant_optimal': 
                    timeout = self.constant_wait_coefficient
                    job_timed_out = wait_time >  max(timeout, 15) # timeout
                elif self.policy == 'runtime_optimal':
                    timeout = job_duration * self.runtime_wait_coefficient
                    job_timed_out = wait_time >  max(timeout, 15) # timeout #self.wait_threshold * self.linear_wait_constant 
                elif self.policy == 'resource_optimal':
                    if self.workload_type == 'cpu':
                        timeout = job.resources['cpu'] * self.resource_wait_coefficient
                    else: 
                        timeout = job.resources['gpu'] * self.resource_wait_coefficient
                    job_timed_out = wait_time >  max(timeout, 15) #timeout #self.wait_threshold * self.linear_wait_constant
                elif self.policy == 'compute_optimal' or self.policy == 'starburst': 
                    if self.workload_type == 'cpu':
                        timeout = job_duration * job.resources['cpu'] * self.resource_wait_coefficient
                    else: 
                        timeout = job_duration * job.resources['gpu'] * self.compute_wait_coefficient
                    job_timed_out = wait_time >  max(timeout, 15) #timeout #self.wait_threshold * job.resources['gpus']
                # logger.debug(f'Cloud Timeout Submission Check || policy {self.policy} | job timed out {job_timed_out} | timeout value {timeout} | wait threshold {self.wait_threshold} | wait time {wait_time} | event queue wait time {event_wait_time} | curr time {loop_time} | submission time {job.job_submit_time} | event added time {job.job_event_queue_add_time} | input job duration {job_duration} | input job resources {str(job_resource)} | input job name {str(job_id)}')
                if job_timed_out:
                    # logger.debug(f'Cloud Timeout Submission Entered || job {job.job_name} | spilling to cloud  {self.spill_to_cloud} | queue {job_queue}')
                    if self.spill_to_cloud:
                        self.cloud_manager.submit_job(job)
                    job_queue.remove(job)
                    # TODO: Share and save job runtimes for cloud jobs when spill over begins 
                    # TODO: Log jobs name and time job reaches this condition
                    with open(self.spilled_jobs_path, "a") as f:
                        f.write(f'Cloud Job || job id {job_id} | job name {job.job_name} | estimated cloud start time {time.time()} | estimated job duration {job_duration} | submission time {job.job_event_queue_add_time} | gpus {job_resource} \n')

            cloud_end_time = time.time()
            logger.debug(f"Looped through queue for cloud timeout || processing time {cloud_end_time - cloud_start_time}")
             
            onprem_start_time = time.time() 
            for job in job_queue:
                debug_time = time.time()
                if isinstance(self.prevJobName, tuple):
                    self.prevJobName = self.prevJobName[0]
                if isinstance(self.prevJobStatus, tuple):
                    self.prevJobStatus = self.prevJobStatus[0]
                logger.debug(f'prev job name {str(self.prevJobName)} | prev job status {str(self.prevJobStatus)} | type {type(self.prevJobName)}')

                if self.prevJobName:     
                    self.prevJobStatus = self.onprem_manager.job_running(job_name=self.prevJobName, namespace='default')
                    logger.debug(f'Updated Previous Job Status || prev job name {str(self.prevJobName)} | prev job status {str(self.prevJobStatus)} | type {type(self.prevJobName)}')
                
                # TODO: Pre-emption conditional -- time.time() - job.job_submit_time <= self.wait_threshold 
                # if self.cloud_only # TODO: Include option for submission to cloud only
                can_fit = self.onprem_manager.can_fit(job)
                logger.debug(f'Onprem Submission Check || Can fit: {can_fit} | Prev Job Name: {self.prevJobName} | Prev Job Status: {self.prevJobStatus}')
                # TODO: Set previous job completed instead of previous job scheduled -- ERROR  
                if can_fit and (self.prevJobName == None or self.prevJobStatus == None or self.prevJobStatus == 1): 
                    logger.debug(f'Onprem Submission Entered || job {job.job_name} | queue {job_queue} | submission time {job.job_submit_time} | debug time {debug_time}' )                    
                    job_queue.remove(job)
                    self.onprem_manager.submit_job(job)
                    self.prevJobName = job.job_name # NOTE: Previous job status computed outside if statement
                    
                    for r in job.resources: # TODO: Verify if job.resources matches estimated state's key values
                        self.estimated_state[r] += job.resources[r]
                else:
                    logger.debug(f'Onprem submission adverted | job {job.job_name} | queue {job_queue} | submission time {job.job_submit_time} | debug time {debug_time}')
                    #if self.loop:
                    if self.policy == 'starburst': 
                        pass
                    else: 
                        break
            onprem_end_time = time.time()
            logger.debug(f"Looped through queue for onprem submission || processing time {onprem_end_time - onprem_start_time}")
            curr_time = time.perf_counter()
            logger.debug(f'End of process_queue function call || total time {str(curr_time-start_time)}')
        else:
            # logger.info("Job queue is empty.")
            curr_time = time.perf_counter()
            # logger.debug(f'End of process_queue function call || total time {str(curr_time-start_time)}')
            return

