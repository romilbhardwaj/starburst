"""
Submit a job to the scheduler via GRPC.

Usage:
	python starburst/drivers/submit_job.py --job-yaml examples/default/example_job.yaml
"""
import argparse
import grpc
import logging
import time

import starburst.drivers.main_driver as driver 
from starburst.event_sources.grpc.protogen import job_submit_pb2_grpc, job_submit_pb2

DEFAULT_IP = 'localhost'
JOB_YAML_PATH = 'examples/default/example_job.yaml'

logger = logging.getLogger(__name__)

def parse_args():
	parser = argparse.ArgumentParser(description='Starburst Job Submission client that sends jobs to the scheduler.')
	parser.add_argument('--job-yaml', '-j', type=str, default=JOB_YAML_PATH, help='Path to k8s job YAML to submit')
	parser.add_argument('--port', '-p', type=int, default=driver.GRPC_PORT, help='GRPC Port')
	parser.add_argument('--ip', '-i', type=str, default=DEFAULT_IP, help='GRPC IP addresss')
	args = parser.parse_args()

	return args

def run_client(ip, port, job_yaml_path):
	with grpc.insecure_channel(f'{ip}:{port}') as channel:
		stub = job_submit_pb2_grpc.JobSubmissionStub(channel)
		logger.debug(f'CLIENT READ AT {ip}:{port} with {channel}')
		with open(args.job_yaml, 'r') as f:
			job_yaml = f.read()
		print("-------------- SubmitJob --------------")
		print(job_yaml)
		curr_time = time.time()
		logger.debug(f'****** Job Sent to GRPC SERVER at Time {curr_time} ******')
		ret = stub.SubmitJob(job_submit_pb2.JobMessage(JobYAML=job_yaml))
		logger.debug(f"Got retcode {ret.retcode}")


if __name__ == '__main__':
	logging.basicConfig()
	args = parse_args()
	logging.info(args)
	run_client(args.ip, args.port, args.job_yaml)