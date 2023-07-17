"""
Driver for Starburst. Use this to run Starburst.
"""
import argparse
import asyncio
import logging
import os
import yaml

from starburst.event_sources.grpc.job_submit_event_source import \
    JobSubmissionEventSource
from starburst.event_sources.sched_tick_event_source import\
    SchedTickEventSource
from starburst.scheduler.starburst_scheduler import StarburstScheduler
from starburst.utils.log_manager import SimpleEventLogger

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-6s | %(name)-40s || %(message)s',
    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Job submission parameters
GRPC_PORT = 30000

# Other parameters
SCHED_TICK_TIME = 1

# K8s configuration. These names must exist as contexts in your kubeconfig
# file. Check using `kubectl config get-contexts`.
ONPREM_K8S_CLUSTER_NAME = 'kind-onprem'
CLOUD_K8S_CLUSTER_NAME = 'kind-cloud'


def parse_args():
    parser = argparse.ArgumentParser(
        description='Launches Starburst scheduler.')
    parser.add_argument('--grpc_port',
                        type=int,
                        default=GRPC_PORT,
                        help='GRPC port to listen on')
    parser.add_argument('--sched_tick_time',
                        type=int,
                        default=SCHED_TICK_TIME,
                        help='Time between scheduler ticks')
    parser.add_argument('--onprem_k8s_cluster_name',
                        type=str,
                        default=ONPREM_K8S_CLUSTER_NAME,
                        help='Name of on-prem K8s cluster')
    parser.add_argument('--cloud_k8s_cluster_name',
                        type=str,
                        default=CLOUD_K8S_CLUSTER_NAME,
                        help='Name of cloud K8s cluster')
    parser.add_argument('--config',
                        type=str,
                        help='Optional policy config file')

    policy_parser = argparse.ArgumentParser(
        description='Launches Starburst scheduler with specified policy.')
    policy_parser.add_argument('--queue_policy',
                               type=str,
                               default='fifo',
                               help='Queueing policy which sets the order of the jobs in the queue. Possible options: [\'fifo\', \'sjf\', \']')
    policy_parser.add_argument('--waiting_policy',
                               type=str,
                               default='constant',
                               help='Waiting policy which sets how long jobs wait in queue before timing out to the cloud.')
    policy_parser.add_argument('--waiting_coeff',
                               type=float,
                               default=10,
                               help='Sets the hyperparameter for each waiting policy')
    policy_parser.add_argument('--waiting_budget',
                               type=float,
                               default=-1,
                               help='Estimates the waiting coeff based on the waiting budget. Overrides waiting_coeff if it is set to a non-negative value.')
    policy_parser.add_argument('--min_waiting_time',
                               type=float,
                               default=10,
                               help='Minimum waiting waiting for jobs. Equivalent to Kubernetes cluster autoscaler 10 (s) waiting time.')
    policy_parser.add_argument('--loop',
                               type=str,
                               default='False',
                               help='Removes head of line blocking, allows scheduler to loop through all jobs in the queue.')

    args, unknown = parser.parse_known_args()
    policy_args, _ = policy_parser.parse_known_args(unknown)

    if policy_args.loop is not None:
        policy_args.loop = policy_args.loop.lower() in ['true', '1']

    return args, policy_args


def load_config(config_path):
    file_path = os.path.abspath(config_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Sweep config YAML not found: {file_path}")
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data


def launch_starburst_scheduler(
    grpc_port=None,
    sched_tick_time=SCHED_TICK_TIME,
    clusters={},
    policy_config=None,
):
    # Create event queue, logger and sources.
    event_queue = asyncio.Queue()
    event_logger = SimpleEventLogger()
    event_loop = asyncio.get_event_loop()
    # Create event sources
    sched_tick_event_source = SchedTickEventSource(event_queue,
                                                   sched_tick_time)
    grpc_job_submit_event_source = JobSubmissionEventSource(
        event_queue, grpc_port)

    # TODO: add sched_tick_event_source back
    if sched_tick_event_source:
        sched_tick_event_source = 0

    event_sources = [grpc_job_submit_event_source]
    starburst = StarburstScheduler(event_queue,
                                   event_logger,
                                   clusters=clusters,
                                   policy_config=policy_config)

    # Create event sources
    for s in event_sources:
        event_loop.create_task(s.event_generator())
    try:
        event_loop.run_until_complete(starburst.scheduler_loop())
    finally:
        event_loop.close()
    return


if __name__ == '__main__':
    args, policy_args = parse_args()

    policy_config = load_config(
        args.config) if args.config else vars(policy_args)

    onprem_config = {
        'cluster_type': 'k8',
        'cluster_args': {
            'cluster_name': args.onprem_k8s_cluster_name
        }
    }
    cloud_config = {
        'cluster_type': 'k8',
        'cluster_args': {
            'cluster_name': args.cloud_k8s_cluster_name
        }
    }
    launch_starburst_scheduler(
        grpc_port=args.grpc_port,
        sched_tick_time=args.sched_tick_time,
        clusters={
            'onprem': onprem_config,
            'cloud': cloud_config
        },
        policy_config=policy_config,)
