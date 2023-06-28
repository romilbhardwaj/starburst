"""
Submit a job to the scheduler via GRPC. The scheduler is assumed to already be
launched.

Usage:
    python starburst/drivers/submit_job.py --job-yaml JOB_YAML_PATH
"""
import argparse
import grpc
import logging
import time

import starburst.drivers.main_driver as driver
from starburst.event_sources.grpc.protogen import job_submit_pb2_grpc, \
    job_submit_pb2

DEFAULT_IP = 'localhost'
JOB_YAML_PATH = 'examples/default/example_job.yaml'

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Starburst Job Submission client that sends jobs '
        'to the scheduler.')
    parser.add_argument('--job-yaml',
                        '-j',
                        type=str,
                        default=JOB_YAML_PATH,
                        help='Path to k8s job YAML to submit')
    parser.add_argument('--port',
                        '-p',
                        type=int,
                        default=driver.GRPC_PORT,
                        help='GRPC Port')
    parser.add_argument('--ip',
                        '-i',
                        type=str,
                        default=DEFAULT_IP,
                        help='GRPC IP addresss (Scheduler Server IP)')
    args = parser.parse_args()
    return args


def run_client(ip: str, port: int, job_yaml_path: str):
    """
    Submit a job to the scheduler via GRPC.

    Args:
        ip (str): IP address of scheduler server.
        port (int): Port of scheduler server.
        job_yaml_path (str): Path to k8s job YAML to submit.
    """
    with grpc.insecure_channel(f'{ip}:{port}') as channel:
        stub = job_submit_pb2_grpc.JobSubmissionStub(channel)
        logger.debug(f'CLIENT READ AT {ip}:{port} with {channel}')
        with open(job_yaml_path, 'r') as f:
            job_yaml = f.read()
        print("-------------- SubmitJob --------------")
        print(job_yaml)
        print("---------------------------------------")
        curr_time = time.time()
        logger.debug(
            f'****** Job Sent to GRPC SERVER at Time {curr_time} ******')
        ret = stub.SubmitJob(job_submit_pb2.JobMessage(JobYAML=job_yaml))
        logger.debug(f"Got retcode {ret.retcode}")


if __name__ == '__main__':
    args = parse_args()
    run_client(args.ip, args.port, args.job_yaml)
