import argparse
import grpc
import logging

from starburst.event_sources.grpc.protogen import job_submit_pb2_grpc, job_submit_pb2

DEFAULT_IP = 'localhost'
DEFAULT_PORT = 10000
JOB_YAML_PATH = 'examples/default/example_job.yaml'

def parseargs():
    parser = argparse.ArgumentParser(description='Starburst Job Submission client that sends jobs to the scheduler.')
    parser.add_argument('--job-yaml', '-j', type=str, default=JOB_YAML_PATH, help='Path to k8s job YAML to submit')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT, help='GRPC Port')
    parser.add_argument('--ip', '-i', type=str, default=DEFAULT_IP, help='GRPC IP addresss')
    parser.add_argument('--kubeflow', '-k', type=bool, default=False, help='kubeflow job submission')
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
        with open(args.job_yaml, 'r') as f:
            job_yaml = f.read()
        print(job_yaml)
        ret = stub.SubmitJob(job_submit_pb2.JobMessage(JobYAML=job_yaml))
        print(f"Got retcode {ret.retcode}")


if __name__ == '__main__':
    logging.basicConfig()
    args = parseargs()
    logging.info(args)
    run_client(args.ip, args.port, args.job_yaml)