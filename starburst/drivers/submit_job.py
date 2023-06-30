import argparse
import grpc
import logging
import time 
from starburst.event_sources.grpc.protogen import job_submit_pb2_grpc, job_submit_pb2

DEFAULT_IP = 'localhost'
DEFAULT_PORT = 30000 #9999 #50051 #10000 #50051 
JOB_YAML_PATH = 'examples/default/example_job.yaml'

logger = logging.getLogger(__name__)

def parseargs():
    parser = argparse.ArgumentParser(description='Starburst Job Submission client that sends jobs to the scheduler.')
    parser.add_argument('--job-yaml', '-j', type=str, default=JOB_YAML_PATH, help='Path to k8s job YAML to submit')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT, help='GRPC Port')
    parser.add_argument('--ip', '-i', type=str, default=DEFAULT_IP, help='GRPC IP addresss')
    parser.add_argument('--kubeflow', '-k', type=bool, default=False, help='kubeflow job submission')
    parser.add_argument('--submit-time', '-t', type=float, default=0, help='submission_time')
    args = parser.parse_args()

    return args

def run_client(ip, port, job_yaml_path):
    with grpc.insecure_channel(f'{ip}:{port}') as channel:
        stub = job_submit_pb2_grpc.JobSubmissionStub(channel)
        print("-------------- SubmitJob --------------")
        # Read the job yaml
        #with open(JOB_YAML_PATH, 'r') as f:
        
        #if args.kubeflow: 
        #    stub.SubmitJob
        #else: 
        logger.debug(f'CLIENT READ AT {ip}:{port} with {channel}')
        with open(args.job_yaml, 'r') as f:
            job_yaml = f.read()
        print(job_yaml)
        #logger.debug(f'****** Job Sent to GRPC SERVER -- Job {args.submit_time} at Time {time.time()}')
        #logger.debug(f'****** Job Reached GRPC SERVER -- Job {job_yaml} at Time {time.time()}')
        curr_time = time.time()
        print(f'****** Job Sent to GRPC SERVER -- Job {args.submit_time} at Time {curr_time} with Delta {curr_time - args.submit_time}')
        #print(f'****** Job Reached GRPC SERVER -- Job {job_yaml} at Time {time.time()}')
        ret = stub.SubmitJob(job_submit_pb2.JobMessage(JobYAML=job_yaml))
        print(f"Got retcode {ret.retcode}")


if __name__ == '__main__':
    logging.basicConfig()
    args = parseargs()
    logging.info(args)
    run_client(args.ip, args.port, args.job_yaml)