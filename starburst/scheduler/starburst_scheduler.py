"""
Starburst scheduler.
"""

import asyncio
import logging
import os
import queue
import time

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
                 job_data: dict = {}):
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

        # Create the cluster managers
        self.onprem_cluster_manager = KubernetesManager(self.onprem_cluster_name)
        self.cloud_cluster_manager = KubernetesManager(self.cloud_cluster_name)

        # Set up policy
        
        queue_policy_class = queue_policies.get_policy(queue_policy_str)
        if queue_policy_str == "fifo_wait":
            self.queue_policy = queue_policy_class(self.onprem_cluster_manager, self.cloud_cluster_manager, wait_threshold=wait_time)
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
        self.job_queue.append(event.job)

    async def scheduler_loop(self, queue, conn):
        """Main loop"""
        '''
        while True:
            #while not queue.empty():
            #    print("Clearing Process Queue...")
            #    queue.get()
            if conn: 
                conn.send(self.job_queue)
            #conn.close()
            #if not queue.empty():
            #    print("Clearing Process Queue...")
            #    queue.get()
            #print("Current Job Queue" + str(self.job_queue))
            #queue.put(self.job_queue)
            logger.debug("Waiting for event.")

            # Fetch event
            event = await self.event_queue.get()
            logger.debug(str(event))
            self.event_logger.log_event(event)

            # Parse and handle event
            self.process_event(event)
        '''

        start_time = time.perf_counter()
        counter = 0 
        while True:
            curr_time = time.perf_counter()
            logger.debug("Count(" + str(counter) + ") Loop start: ~~~ " + str(curr_time-start_time))
            counter += 1
            #while not queue.empty():
            #    print("Clearing Process Queue...")
            #    queue.get()
            # TODO: Remove connection
            '''
            if conn: 
                conn.send(self.job_queue)
            '''
            
            #conn.close()

            curr_time = time.perf_counter()
            logger.debug("Connection end: ~~~ " + str(curr_time-start_time))
            '''
            if not queue.empty():
                print("Clearing Process Queue...")
                queue.get()
            print("Current Job Queue" + str(self.job_queue))
            queue.put(self.job_queue)
            '''
            logger.debug("Waiting for event.")

            curr_time = time.perf_counter()
            logger.debug("Start event processing: ~~~ " + str(curr_time-start_time))

            # Fetch event
            event = await self.event_queue.get()

            curr_time = time.perf_counter()
            logger.debug("Fetched event: ~~~ " + str(curr_time-start_time))


            logger.debug(str(event))
            self.event_logger.log_event(event)

            curr_time = time.perf_counter()
            logger.debug("Logged event: ~~~ " + str(curr_time-start_time))


            # Parse and handle event
            self.process_event(event)

            curr_time = time.perf_counter()
            logger.debug("End event processing and loop: ~~~ " + str(curr_time-start_time))