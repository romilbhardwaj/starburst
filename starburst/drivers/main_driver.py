"""
Driver for Starburst. Use this to run Starburst.
"""
import argparse
import asyncio
import logging

from starburst.event_sources.grpc.job_submit_event_source import JobSubmissionEventSource
from starburst.event_sources.sched_tick_event_source import SchedTickEventSource
from starburst.scheduler.starburst_scheduler import StarburstScheduler
from starburst.utils.event_logger import SimpleEventLogger

logging.basicConfig(level=logging.DEBUG, #CRITICAL or INFO
                    format='%(asctime)s | %(levelname)-6s | %(name)-40s || %(message)s',
                    datefmt='%m-%d %H:%M:%S'
                    )

logger = logging.getLogger(__name__)

# TODO: Resolve local logs from being overriden by logs of imported packages (e.g. kubeflow)

# Job submission parameters
GRPC_PORT = 10000 #50051

# Other parameters
ASYNC_SLEEP_TIME = 0.5
SCHED_TICK_TIME = 1 # Run a tick every 1s

# K8s configuration. These names must exist as contexts in your kubeconfig file. Check using `kubectl config get-contexts`.
ONPREM_K8S_CLUSTER_NAME = 'kind-onprem'
CLOUD_K8S_CLUSTER_NAME = 'kind-cloud'

# Policy configuration
POLICY_STR = 'fifo_onprem_only' 

def main():
    """ Main function. """
    # Parse command line arguments =================================================================
    parser = argparse.ArgumentParser(description='Starburst scheduler')
    parser.add_argument('--grpc_port', type=int, default=GRPC_PORT,
                        help='GRPC port to listen on')
    parser.add_argument('--sched_tick_time', type=int, default=SCHED_TICK_TIME,
                        help='Time between scheduler ticks')
    parser.add_argument('--onprem_k8s_cluster_name', type=str, default=ONPREM_K8S_CLUSTER_NAME,
                        help='Name of on-prem K8s cluster')
    parser.add_argument('--cloud_k8s_cluster_name', type=str, default=CLOUD_K8S_CLUSTER_NAME,
                        help='Name of cloud K8s cluster')
    parser.add_argument('--policy', type=str, default=POLICY_STR,
                        help='Policy to use. Currently supported - fifo_onprem_only')
    args = parser.parse_args()


    # Create event queue, logger and sources ==================================================
    event_queue = asyncio.Queue()
    event_logger = SimpleEventLogger()
    event_loop = asyncio.get_event_loop()
    # Create event sources
    sched_tick_event_source = SchedTickEventSource(event_queue, args.sched_tick_time)
    grpc_job_submit_event_source = JobSubmissionEventSource(event_queue, args.grpc_port)
    event_sources = [sched_tick_event_source, grpc_job_submit_event_source]   # Add more, such as GRPC event source here

    # Pass learner bank and time series model to the scheduler =====================================
    starburst = StarburstScheduler(event_queue,
                                   event_logger,
                                   onprem_cluster_name=args.onprem_k8s_cluster_name,
                                   cloud_cluster_name=args.cloud_k8s_cluster_name,
                                   queue_policy_str=args.policy)

    # Create event sources =========================================================================
    for s in event_sources:
        event_loop.create_task(s.event_generator())
    try:
        event_loop.run_until_complete(starburst.scheduler_loop(None, None))
    finally:
        event_loop.close()

starburst_scheduler = None
if __name__ == '__main__':
    main()


def custom_start(grpc_port=None, sched_tick_time=SCHED_TICK_TIME, onprem_k8s_cluster_name=ONPREM_K8S_CLUSTER_NAME, cloud_k8s_cluster_name=CLOUD_K8S_CLUSTER_NAME, waiting_policy=POLICY_STR, wait_time=0, job_data={}, timestamp=None, index=None, policy='fixed'):
    #global startburst_scheduler
    '''
    # Parse command line arguments =================================================================
    parser.add_argument('--grpc_port', type=int, default=GRPC_PORT,
                        help='GRPC port to listen on')
    parser.add_argument('--sched_tick_time', type=int, default=SCHED_TICK_TIME,
                        help='Time between scheduler ticks')
    parser.add_argument('--onprem_k8s_cluster_name', type=str, default=ONPREM_K8S_CLUSTER_NAME,
                        help='Name of on-prem K8s cluster')
    parser.add_argument('--cloud_k8s_cluster_name', type=str, default=CLOUD_K8S_CLUSTER_NAME,
                        help='Name of cloud K8s cluster')
    parser.add_argument('--policy', type=str, default=POLICY_STR,
                        help=`'Policy` to use. Currently supported - fifo_onprem_only')
    args = parser.parse_args()
    '''

    # Create event queue, logger and sources ==================================================
    event_queue = asyncio.Queue()
    event_logger = SimpleEventLogger()
    event_loop = asyncio.get_event_loop()
    # Create event sources
    sched_tick_event_source = SchedTickEventSource(event_queue, sched_tick_time)
    grpc_job_submit_event_source = JobSubmissionEventSource(event_queue, grpc_port)
    event_sources = [grpc_job_submit_event_source] #[sched_tick_event_source, grpc_job_submit_event_source]   # Add more, such as GRPC event source here

    # Pass learner bank and time series model to the scheduler =====================================
    starburst = StarburstScheduler(event_queue,
                                    event_logger,
                                    onprem_cluster_name=onprem_k8s_cluster_name,
                                    cloud_cluster_name=cloud_k8s_cluster_name,
                                    queue_policy_str=waiting_policy,
                                    wait_time=wait_time,
                                    job_data=job_data,
                                    timestamp=timestamp,
                                    run=index,
                                    policy = policy
                                    )
    
    if 'hyperparameters' in job_data: 
        logger.debug(f"Hyperparameters: {str(job_data['hyperparameters'])}")

    for s in event_sources:
        event_loop.create_task(s.event_generator())
    try:
        event_loop.run_until_complete(starburst.scheduler_loop(None, None)) 
    finally:
        event_loop.close()
