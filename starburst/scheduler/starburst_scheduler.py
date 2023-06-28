"""
Starburst scheduler.
"""
import asyncio
import logging
import time
import traceback
from typing import Dict

from starburst.policies import queue_policies
from starburst.cluster_managers.kubernetes_manager import KubernetesManager
from starburst.types.events import BaseEvent, EventTypes, SchedTick, \
    JobAddEvent

logger = logging.getLogger(__name__)

SCHED_TICK = 1


class StarburstScheduler:
    """ Starburst scheduler.
    
    Description: Starburst scheduler is responsible for scheduling jobs on both
    the on-prem and cloud clusters. It is also responsible for handling events,
    such as job add events (JobAdd) and scheduling ticks (SchedulerTick).
    """

    def __init__(
        self,
        event_queue: asyncio.Queue,
        event_logger: object,
        onprem_cluster_name: str,
        cloud_cluster_name: str,
        spill_to_cloud: str,
        policy_config: Dict[str, str],
        log_file: str = None,
    ):
        """
        Main Starburst scheduler class.
        
        Responsible for processing events in the provided event queue.

        Args:
            event_queue (asyncio.Queue): Event queue for asynchronous
                                         event processing.
            event_logger (object): Event logger used for debug and
                                   storing events in the system.
            onprem_cluster_name (str): Name of the on-prem cluster (the name
                                       of the context in kubeconfig).
            cloud_cluster_name (str): Name of the cloud cluster (the name
                                      of the context in kubeconfig).
        """
        # Scheduler objects
        self.event_queue = event_queue
        self.event_logger = event_logger

        # Job queue
        # TODO(mluo): Move to within Kubernetes instead.
        self.job_queue = []
        self.ticks = []
        self.log_file = log_file

        # if not self.debug:
        #     logging.basicConfig(level=logging.INFO)

        # Create the cluster maangers for on-prem and cloud.
        self.onprem_cluster_name = onprem_cluster_name
        self.cloud_cluster_name = cloud_cluster_name
        self.onprem_cluster_manager = KubernetesManager(
            self.onprem_cluster_name)
        self.cloud_cluster_manager = KubernetesManager(self.cloud_cluster_name)
        self.spill_to_cloud = spill_to_cloud
        self.policy_config = policy_config
        # Set up policy
        queue_policy_class = queue_policies.get_policy(self.policy_config)
        if 'FifoOnpremOnlyPolicy' not in str(queue_policy_class):
            self.queue_policy = queue_policy_class(
                self.onprem_cluster_manager,
                self.cloud_cluster_manager,
                spill_to_cloud=self.spill_to_cloud,
                policy_config=self.policy_config,
                log_file=self.log_file)
        else:
            self.queue_policy = queue_policy_class(self.onprem_cluster_manager,
                                                   self.cloud_cluster_manager)

    def process_event(self, event: BaseEvent):
        '''
        Sends an event to the appropriate processor.

        Args:
            event (BaseEvent): Event to process. Can be SchedulerTick
                               or JobAddEvent.
        '''
        # TODO: Timeout event for job
        if event.event_type == EventTypes.SCHED_TICK:
            assert isinstance(event, SchedTick), "Event is not a SchedTick"
            self.processor_sched_tick_event(event)
        elif event.event_type == EventTypes.JOB_ADD:
            assert isinstance(event, JobAddEvent), "Event is not a JobAddEvent"
            self.processor_job_add_event(event)
        else:
            raise NotImplementedError(
                f"Event type {event.event_type} is not supported.")

    def processor_sched_tick_event(self, event: SchedTick):
        """
        Scheduler tick event. This is the periodic event for the scheduler.

        This is where the scheduler will process the queue and make
        intelligent decisions.
        """
        self.event_logger.log_event(event)
        # Process the queue
        self.queue_policy.process_queue(self.job_queue)

    def processor_job_add_event(self, event: JobAddEvent):
        """
        Process an add job event. This is where the job is added to the
        scheduler queue.

        Args:
            event (JobAddEvent): Job add event.
        """
        self.event_logger.log_event(event)
        event.job.set_event_queue_add_time(time.time())
        self.job_queue.append(event.job)

    async def scheduler_loop(self, queue, conn):
        """
        Main scheduler loop.
        
        This is the main loop for the scheduler. It will process events
        """
        while True:
            loop_start_time = time.perf_counter()
            event = None
            try:
                if not self.event_queue.empty():
                    event = self.event_queue.get_nowait()
            except Exception as e:
                logger.debug(f"Exception: {e}: {traceback.print_exc()}")
                pass

            # Call scheduler every SCHED_TICK seconds
            self.queue_policy.process_queue(self.job_queue)

            if event:
                self.process_event(event)
            loop_end_time = time.perf_counter()

            # This mimics a scheduler tick.
            # TODO(mluo): Make the scheduler truly async.
            # Add two async events; Scheduler tick and job timeouts
            delta = loop_end_time - loop_start_time
            if delta < SCHED_TICK:
                await asyncio.sleep(SCHED_TICK - delta)
