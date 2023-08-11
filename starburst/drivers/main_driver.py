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
from starburst.event_sources.sched_tick_event_source import \
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
CLOUD_CLUSTER_NAME = 'kind-cloud'


def get_config_argparse():
    parser = argparse.ArgumentParser(
        description='Starburst argparse for config file.')
    parser.add_argument('--config',
                        type=str,
                        help='Optional policy config file')
    return parser


def get_scheduler_argparse():
    parser = argparse.ArgumentParser(
        description='Launches Starburst scheduler.')
    parser.add_argument('--grpc_port',
                        type=int,
                        default=GRPC_PORT,
                        choices=range(1, 2**16),
                        help='GRPC port to listen on')
    return parser


def get_policy_argparse(config):
    policy_parser = argparse.ArgumentParser(
        description='Launches Starburst scheduler with specified policy.')
    policy_parser.add_argument('--schedule_tick',
                               type=int,
                               default=config.get(
                                   'schedule_tick', SCHED_TICK_TIME),
                               help='Time between scheduler ticks')
    policy_parser.add_argument('--queue_policy',
                               type=str,
                               default=config.get('queue_policy', 'fifo'),
                               choices=['fifo', 'sjf'],
                               help='Queueing policy which sets the order of the jobs in the queue. Possible options: [\'fifo\', \'sjf\', \']')
    policy_parser.add_argument('--waiting_policy',
                               type=str,
                               default=config.get(
                                   'waiting_policy', 'constant'),
                               choices=['constant', 'infinite',
                                        'runtime', 'resource', 'compute'],
                               help='Waiting policy which sets how long jobs wait in queue before timing out to the cloud.')
    policy_parser.add_argument('--waiting_coeff',
                               type=float,
                               default=config.get('waiting_coeff', 10),
                               help='Sets the hyperparameter for each waiting policy')
    policy_parser.add_argument('--waiting_budget',
                               type=float,
                               default=config.get('waiting_budget', -1),
                               help='Estimates the waiting coeff based on the waiting budget. Overrides waiting_coeff if it is set to a non-negative value.')
    policy_parser.add_argument('--min_waiting_time',
                               type=float,
                               default=config.get('min_waiting_time', 10),
                               help='Minimum waiting waiting for jobs. Equivalent to Kubernetes cluster autoscaler 10 (s) waiting time.')
    policy_parser.add_argument('--loop',
                               action="store_true",
                               default=config.get('loop', False),
                               help='Removes head of line blocking, allows scheduler to loop through all jobs in the queue.')
    return policy_parser


def parse_args():
    # If config file passed, use values in config file as defaults
    # Otherwise, use hardcoded values
    config_parser = get_config_argparse()
    config_args, unknown = config_parser.parse_known_args()
    config = load_config(
        config_args.config) if config_args.config is not None else {}

    # Create separate argparser for scheduler and policy args
    scheduler_parser = get_scheduler_argparse()
    policy_parser = get_policy_argparse(config)

    scheduler_args, unknown = scheduler_parser.parse_known_args(unknown)
    policy_args, unknown = policy_parser.parse_known_args(unknown)

    # Cloud cluster can be one of k8, log, skypilot
    # Create and handle each type with a different parser
    clusters = config.get("clusters") or {"onprem": {}, "cloud": {}}
    current_cluster = None

    for item in unknown:
        if item in ['onprem', 'cloud']:
            current_cluster = item
            clusters[current_cluster] = {}
        elif current_cluster is not None:
            cluster_attribute, value = item.split('=')
            if cluster_attribute == 'cluster_type':
                clusters[current_cluster]['cluster_type'] = value
            else:
                if 'cluster_args' not in clusters[current_cluster]:
                    clusters[current_cluster]['cluster_args'] = {}
                clusters[current_cluster]['cluster_args'][cluster_attribute] = value

    return scheduler_args, policy_args, clusters


def load_config(config_path):
    file_path = os.path.abspath(config_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Sweep config YAML not found: {file_path}")
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data


def launch_starburst_scheduler(
    grpc_port=None,
    clusters={},
    policy_config=None,
):
    # Create event queue, logger and sources.
    event_queue = asyncio.Queue()
    event_logger = SimpleEventLogger()
    event_loop = asyncio.get_event_loop()
    # Create event sources
    sched_tick_event_source = SchedTickEventSource(event_queue,
                                                   policy_config['schedule_tick'])
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
    scheduler_args, policy_args, clusters = parse_args()

    print(clusters["onprem"])
    print(clusters["cloud"])

    launch_starburst_scheduler(
        grpc_port=scheduler_args.grpc_port,
        clusters={
            'onprem': clusters["onprem"],
            'cloud': clusters["cloud"]
        },
        policy_config=vars(policy_args),)
