"""
Starburst scheduler.
"""
import asyncio
import logging
import os
import queue
import time
import json 

from starburst.policies import queue_policies
from starburst.cluster_managers.kubernetes_manager import KubernetesManager
from starburst.types.events import BaseEvent, EventTypes, SchedTick, JobAddEvent

logger = logging.getLogger(__name__)


class StarburstScheduler:
    """ Starburst scheduler. """

    def __init__(self,
                 event_queue: asyncio.Queue,
                 event_logger: object,
                 onprem_cluster_name: str,
                 cloud_cluster_name: str,
                 queue_policy_str: str = "fifo_onprem_only",
                 wait_time: int = 0,
                 job_data: dict = {},
                 timestamp: int = 0,
                 run: int = 0,
                 policy: str = 'fixed'):
        """
        Main Starburst scheduler class. Responsible for processing events in the provided event queue.
        :param event_queue: Main event queue
        :param event_logger: Event logger used for debug and storing events in the system.
        :param onprem_cluster_name: Name of the on-prem cluster (the name of the context in kubeconfig)
        :param cloud_cluster_name: Name of the cloud cluster (the name of the context in kubeconfig)
        """
        # Scheduler objects
        self.event_queue = event_queue
        self.event_logger = event_logger
        self.onprem_cluster_name = onprem_cluster_name
        self.cloud_cluster_name = cloud_cluster_name
        self.job_queue = []
        self.prev_sched_tick_call = None
        self.prev_tick = 0
        self.prev_event = None 
        self.timestamp = timestamp
        self.ticks = []
        self.run = run
        self.prev_loop_time = None

        # Create the cluster managers
        self.onprem_cluster_manager = KubernetesManager(self.onprem_cluster_name)
        self.cloud_cluster_manager = KubernetesManager(self.cloud_cluster_name)

        # Set up policy
        logger.debug(f'all job data inputted {job_data}')
        queue_policy_class = queue_policies.get_policy(queue_policy_str)
        if queue_policy_str == "fifo_wait":
            self.queue_policy = queue_policy_class(self.onprem_cluster_manager, self.cloud_cluster_manager, wait_threshold=wait_time, job_data=job_data, policy=policy, batch_repo=timestamp, index=run)
        elif queue_policy_str == "time_estimator":
            self.queue_policy = queue_policy_class(self.onprem_cluster_manager, self.cloud_cluster_manager, wait_threshold=wait_time, job_data=job_data)
        else: 
            self.queue_policy = queue_policy_class(self.onprem_cluster_manager, self.cloud_cluster_manager)

        # Get asyncio loop
        self.aioloop = asyncio.get_event_loop()

    def process_event(self, event: BaseEvent):
        '''
        Sends an event to the appropriate processor.
        :param event:
        :return:
        '''
        # TODO: Timeout event for job 
        if event.event_type == EventTypes.SCHED_TICK:
            assert isinstance(event, SchedTick)
            self.processor_sched_tick_event(event)
        elif event.event_type == EventTypes.JOB_ADD:
            assert isinstance(event, JobAddEvent)
            self.processor_job_add_event(event)
        else:
            raise NotImplementedError(f"Event type {event.event_type} is not supported.")

    def processor_sched_tick_event(self, event: SchedTick):
        """ Scheduler tick event. Think of this as a periodic event.

        You can do a bunch of things here, such as updating local state and trying to submit jobs from the queue.
        """
        # Log the event
        self.event_logger.log_event(event)
        # Process the queue
        self.queue_policy.process_queue(self.job_queue)

    def processor_job_add_event(self, event: JobAddEvent):
        """ Process an add job event. This is where you probably want to add job to your queue"""
        _start_process_event_time = time.perf_counter()
        event.job.job_event_queue_add_time = time.time()
        self.job_queue.append(event.job)
        _end_process_event_time = time.perf_counter()
        logger.debug("QUEUEADD TIME (()) " + str(_end_process_event_time - _start_process_event_time))
        logger.debug(f'***** Job Retrieved in Event Queue -- Job {event.job} at time {_end_process_event_time}')
        logger.debug(f'DIFF TIMES {time.time()} or {time.perf_counter()}')

    async def scheduler_loop(self, queue, conn):
        """Main loop"""
        start_time = time.perf_counter()
        counter = 0 

        #TODO: Ensure any two consequtive calls to SchedEventTick are limited by 
        while True: 
            _start_time = time.perf_counter()
            _start_await_time = time.perf_counter()
            event = None
            try: 
                # TODO: Added all events from event queue onto process queue within a tick
                event = self.event_queue.get_nowait()
                #event = await self.event_queue.get()
            except Exception as e: 
                pass
            _end_await_time = time.perf_counter()

            _start_process_queue_time = time.perf_counter()
            job_queue_len = len(self.job_queue)
            self.queue_policy.process_queue(self.job_queue)
            _end_process_queue_time = time.perf_counter()

            _start_process_event_time = time.perf_counter()
            event_queue_len = self.event_queue.qsize
            if event: 
                self.process_event(event)
            _end_process_event_time = time.perf_counter()
            _end_time = time.perf_counter()
            
            #logger.debug("LOOP TIME (()) " + str(_end_time))
            #logger.debug("LOOP TIME (()) " + str(_end_time))
            #logger.debug("LOOP TIME (()) " + str(_end_time - _start_time))
            
            '''scheduler_tick_interval = 0.5
            if _end_time - _start_time > 0.5:
                logger.debug("LOOP TIME (()) " + str(_end_time - _start_time))
                continue
            else:
                time.sleep(0.5 - (_end_time - _start_time))
            '''
            logger.debug("AWAIT TIME (()) " + str(_end_await_time - _start_await_time))
            logger.debug("PROCESSQUEUE TIME (()) " + str(_end_process_queue_time - _start_process_queue_time))
            logger.debug("JOB QUEUE SIZE " + str(job_queue_len))
            logger.debug("PROCESSEVENT TIME (()) " + str(_end_process_event_time - _start_process_event_time))
            logger.debug("EVENT QUEUE SIZE (()) " + str(event_queue_len))
            delta = _end_time  - _start_time
            if delta < 1:
                await asyncio.sleep(1.0 -(_end_time - _start_time)) # -(_end_time - _start_time))
            _interloop_end_time = time.perf_counter()
            logger.debug("INTERLOOP TIME (()) " + str(_interloop_end_time - _start_time))
            if self.prev_loop_time:
                logger.debug("LOOP TIME (()) " + str(_interloop_end_time - self.prev_loop_time))#str(_end_time - _start_time))
            self.prev_loop_time = _interloop_end_time
