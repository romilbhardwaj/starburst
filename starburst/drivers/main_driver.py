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
CLOUD_CLUSTER_NAME = 'kind-cloud'


def get_config_argparse():
    parser = argparse.ArgumentParser(
        description='Starburst argparse for config file.')
    parser.add_argument('--config',
                        type=str,
                        help='Optional policy config file')
    return parser


def get_scheduler_argparse(config):
    parser = argparse.ArgumentParser(
        description='Launches Starburst scheduler.')
    parser.add_argument('--grpc_port',
                        type=int,
                        default=GRPC_PORT,
                        help='GRPC port to listen on')
    parser.add_argument('--sched_tick_time',
                        type=int,
                        default=config.get('schedule_tick', SCHED_TICK_TIME),
                        help='Time between scheduler ticks')
    parser.add_argument('--onprem_k8s_cluster_name',
                        type=str,
                        default=config.get('clusters', {})
                        .get('onprem', {})
                        .get('cluster_args', {})
                        .get('cluster_name', ONPREM_K8S_CLUSTER_NAME),
                        help='Name of on-prem cluster')
    parser.add_argument('--onprem_k8s_cluster_namespace',
                        type=str,
                        default=config.get('clusters', {})
                        .get('onprem', {})
                        .get('cluster_args', {})
                        .get('namespace', 'default'),
                        help='Namespace of on-prem cluster')
    parser.add_argument('--cloud_cluster_type',
                        type=str,
                        default=config.get('clusters', {})
                        .get('cloud', {})
                        .get('cluster_args', {})
                        .get('namespace', 'default'),
                        help='Type of cloud cluster. Possible options: [\'k8\', \'log\', \'skypilot\']')
    return parser


def get_policy_argparse(config):
    policy_parser = argparse.ArgumentParser(
        description='Launches Starburst scheduler with specified policy.')
    policy_parser.add_argument('--queue_policy',
                               type=str,
                               default=config.get('queue_policy', 'fifo'),
                               help='Queueing policy which sets the order of the jobs in the queue. Possible options: [\'fifo\', \'sjf\', \']')
    policy_parser.add_argument('--waiting_policy',
                               type=str,
                               default=config.get(
                                   'waiting_policy', 'constant'),
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
                               type=str,
                               default=str(config.get('loop', False)),
                               help='Removes head of line blocking, allows scheduler to loop through all jobs in the queue.')
    return policy_parser


def handle_cluster_type_specific_args(type, args, config):
    out = {}
    parser = argparse.ArgumentParser(
        description='Handles cluster type specific args.')
    parser.add_argument('--cloud_cluster_name',
                        type=str,
                        default=config.get('clusters', {})
                        .get('cloud', {})
                        .get('cluster_args', {})
                        .get('cluster_name', CLOUD_CLUSTER_NAME),
                        help='Name of cloud K8s cluster')

    if type is not None:
        if type.lower() == 'k8':
            parser.add_argument('--cloud_cluster_namespace',
                                type=str,
                                default=config.get('clusters', {})
                                .get('cloud', {})
                                .get('cluster_args', {})
                                .get('namespace', 'default'),
                                help='Namespace of cloud K8s cluster')
        elif type.lower() == 'log':
            parser.add_argument('--cloud_cluster_log_file',
                                type=str,
                                default=config.get('clusters', {})
                                .get('cloud', {})
                                .get('cluster_args', {})
                                .get('log', '/starburst.log'),
                                help='Name of log cluster')

    known, _ = parser.parse_known_args(args)

    out['cluster_name'] = known.cloud_cluster_name
    if type is not None:
        if type.lower() == 'k8':
            out['namespace'] = known.cloud_cluster_namespace
        elif type.lower() == 'log':
            out['log_file'] = known.cloud_cluster_log_file

    return out


def parse_args():
    # If config file passed, use values in config file as defaults
    # Otherwise, use hardcoded values
    config_parser = get_config_argparse()
    config_args, unknown = config_parser.parse_known_args()
    config = load_config(
        config_args.config) if config_args.config is not None else {}

    # Create separate argparser for scheduler and policy args
    scheduler_parser = get_scheduler_argparse(config)
    policy_parser = get_policy_argparse(config)

    scheduler_args, unknown = scheduler_parser.parse_known_args(unknown)
    policy_args, unknown = policy_parser.parse_known_args(unknown)

    # Cloud cluster can be one of k8, log, skypilot
    # Create and handle each type with a different parser
    cluster_args = handle_cluster_type_specific_args(
        scheduler_args.cloud_cluster_type, unknown, config)

    if policy_args.loop is not None:
        policy_args.loop = policy_args.loop.lower() in ['true', '1']

    return scheduler_args, policy_args, cluster_args


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
    scheduler_args, policy_args, cloud_cluster_args = parse_args()

    onprem_config = {
        'cluster_type': 'k8',
        'cluster_args': {
            'cluster_name': scheduler_args.onprem_k8s_cluster_name,
            'cluster_namespace': scheduler_args.onprem_k8s_cluster_namespace
        }
    }
    cloud_config = {
        'cluster_type': scheduler_args.cloud_cluster_type,
        'cluster_args': cloud_cluster_args
    }

    launch_starburst_scheduler(
        grpc_port=scheduler_args.grpc_port,
        sched_tick_time=scheduler_args.sched_tick_time,
        clusters={
            'onprem': onprem_config,
            'cloud': cloud_config
        },
        policy_config=vars(policy_args),)
