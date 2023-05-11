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

        super().__init__(onprem_manager, cloud_manager)

    '''
    Cluster state updates:
    (1) Once submitted yaml (cached/hardcoded state with no queries of cluster) -- SPECULATIVE w/ no cluster state 
    (2) Once submitted yaml, creates job on k8s (queries cluster's pod states) -- SPECULATIVE w/ pod state
    (3) Once submitted yaml, creates job on k8s, kills jobs if running for too long (queries cluster's pod states) -- SPECULATIVE w/ pod state and ROLLBACK
    (4) Once submitted yaml, creates job on k8s, creates a pod, and gets scheduled (queries cluster's node states) -- NON SPECULATIVE
    '''

    def process_queue(self, job_queue: List[Job]):
        """ Process in FIFO order. Iterates over all jobs (no HoL blocking).
        If job has been waiting longer than a threshold, submit to cloud. """
        # Check if the onprem cluster can fit the job
        import time
        start_time = time.perf_counter()
        curr_time = time.perf_counter()

        logger.debug("Started process_queue(): ~~~ --- " + str(curr_time-start_time))

        retry = 0 

        #TODO: Mark jobs pending on the queue as pending, so they are not used to submit locally 
        #TODO: Don't run and wait for process queue until empty

        if job_queue:
            curr_time = time.perf_counter()
            logger.debug("Retry(" + str(retry) + ") " + "Started queue loop : ~~~ --- " + str(curr_time-start_time))
            retry += 1
            
            # NOTE: Pops off pending jobs before submitting new jobs
            job_id = 0
            
            for job in job_queue:
                # Check job.submit_time and see if it has been waiting longer than the threshold
                '''
                # TODO: Integrate job_data from timeestimator here
                if self.preempt_cpu and job.resources['gpus'] == 0:
                    self.cloud_manager.submit_job(job)
                    logger.debug(
                    f"Deadline passed, spilling over {job}. Submitting to cloud.")
                    # Remove from queue
                    job_queue.remove(job)
                '''
                '''
                # TODO: Move this to timeestimator + linear wait policy 
                if job.resources['gpus'] * sum(job.resources['runtime']) <= self.linear_wait_constant:
                    self.cloud_manager.submit_job(job)
                    logger.debug(
                    f"Deadline passed, spilling over {job}. Submitting to cloud.")
                    # Remove from queue
                    job_queue.remove(job)
                '''
                debug_time = time.time()
                if time.time() - job.job_submit_time > self.wait_threshold:
                    logger.debug(f"SUBMIT - CLOUD ### Delta {debug_time - job.job_submit_time} Timeout {self.wait_threshold}")
                    logger.debug(f"SUBMIT - CLOUD ### Currtime {debug_time} Submitime {job.job_submit_time}")
                    # Submit to cloud

                    
                    self.cloud_manager.submit_job(job)
                    logger.debug(
                        f"Deadline passed, spilling over {job}. Submitting to cloud.")
                    # Remove from queue
                    job_queue.remove(job)
            # TODO: Figure out why the above doesn't work as intended         
            for job in job_queue:
                curr_time = time.perf_counter()
                logger.debug("Job(" + str(job_id) + ") " + "Next job on queue : ~~~ --- " + str(curr_time-start_time))
                job_id += 1 

                debug_time = time.time()
                # TODO: Don't submit cluster to onprem if cluster state remains the same from a previous job

                # TODO: Retrieve the jobs on the cluster and list them 

                if self.wait_until_scheduled: 
                    self.currState, self.curr_pods = self.onprem_manager.get_allocatable_resources_per_node()

                    if self.prevState and self.prev_pods: 
                        while self.prevState == self.currState and self.prev_pods == self.curr_pods:
                            logger.debug(f"SCHEDULER OVERCLOCKED ***")
                            self.currState, self.curr_pods = self.onprem_manager.get_allocatable_resources_per_node()
                            
                    #self.prevState = None #self.currState
                    self.currState = None
                    self.curr_pods = None

                if time.time() - job.job_submit_time <= self.wait_threshold and self.onprem_manager.can_fit(job):
                    if self.wait_until_scheduled: 
                        self.currState, self.curr_pods = self.onprem_manager.get_allocatable_resources_per_node()

                        if self.prevState == self.currState and self.curr_pods == self.prev_pods:
                            logger.debug(f"SCHEDULER OVERCLOCKED ***")
                                
                        #self.prevState = self.currState
                        logger.debug("PREV STATE IS " + str(self.prevState))
                        logger.debug("CURR STATE IS " + str(self.currState))

                        logger.debug("PREV PODS IS " + str(self.prev_pods))
                        logger.debug("CURR PODS IS " + str(self.curr_pods))
                        
                        self.prevState = self.currState
                        self.currState = None

                        self.prev_pods = self.curr_pods
                        self.curr_pods = None 

                #if self.onprem_manager.can_fit(job):
                    logger.debug(f"SUBMIT - ONPREM ### Currtime {debug_time} Submitime {job.job_submit_time}")
                    # TODO: Can_fit incorrectly executes here -- print out log of cluster state before and after submit_job
                    # TODO: Figure out how to properly parse the job data from the cluster event logs
                    # Remove from queue
                    job_queue.remove(job)
                    # Submit the job


                    self.onprem_manager.submit_job(job)
                    # TODO: Verify if job.resources matches estimated state's key values
                    for r in job.resources:
                        self.estimated_state[r] += job.resources[r]

                    logger.debug(f"Onprem cluster can fit {job}. Submitting to onprem.")
                else:
                    logger.debug(f"WAITING - CANNOT FIT ON PREM AND DID NOT TIMEOUT  ### Currtime {debug_time} Submitime {job.job_submit_time}")
                    waited_time = time.time() - job.job_submit_time
                    logger.debug(
                        f"Waiting - Onprem cluster cannot fit {job}. Been waiting for {waited_time} seconds.")
                    if self.loop: 
                        pass
                    else: 
                        break
        else:
            logger.info("Job queue is empty.")
            curr_time = time.perf_counter()

            logger.debug("Completed process_queue(): ~~~ --- " + str(curr_time-start_time))

            return

# TODO: Implement Linear Wait Policy
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

        while job_queue:
            while (len(self.running_jobs) > 0) and self.running_jobs[0][0] < time.time(): 
                heapq.heappop(self.running_jobs)
            
            job = job_queue[0]
            job_index = int(job.job_name[6:])
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