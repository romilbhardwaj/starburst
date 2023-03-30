import logging
import time
from asyncio import Queue

import grpc

from concurrent import futures

from starburst.event_sources.base_event_source import BaseEventSource
from starburst.event_sources.grpc.protogen import job_submit_pb2_grpc
from starburst.event_sources.grpc.protogen import job_submit_pb2
from starburst.types.events import JobAddEvent
from starburst.types.job import Job

logger = logging.getLogger(__name__)


class JobSubmissionServicer(job_submit_pb2_grpc.JobSubmissionServicer):
    # Implements the GRPC Servicer for job submission from clients
    def __init__(self,
                 event_queue: Queue,
                 debug_mode: bool = False):
        self.event_queues = event_queue
        self.debug_mode = debug_mode
        super(JobSubmissionServicer, self).__init__()

    def SubmitJob(self,
                       request: job_submit_pb2.JobMessage,
                       context):
        # Update this to fill in resources using JobMessage.
        job = Job(job_name="MyJob",
                  job_submit_time=time.time(),
                  job_start_time=0,
                  job_end_time=0,
                  job_yaml=request.JobYAML,
                  resources={'cpu': 1})
        event = JobAddEvent(job, timestamp=time.time())
        self.event_queues.put_nowait(event)
        if self.debug_mode:
            logger.debug(f"Got event: {str(event)}")
        return job_submit_pb2.JobAck(retcode=0)

class JobSubmissionEventSource(BaseEventSource):
    '''Runs a job submission grpc server to get data'''
    def __init__(self,
                 output_queue: Queue,
                 server_port: int):
        super(JobSubmissionEventSource, self).__init__(output_queue)
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        job_submit_pb2_grpc.add_JobSubmissionServicer_to_server(
            JobSubmissionServicer(self.output_queue), self.server)
        self.server.add_insecure_port(f'[::]:{server_port}')

    async def event_generator(self):
        '''
        Long running loop that generates events indefinitely
        :return:
        '''
        await self.server.start()
        await self.server.wait_for_termination()

    def __del__(self):
        self.server.stop(grace=0)