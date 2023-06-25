import argparse
import numpy as np 
import os 
import time
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from kubernetes import client, config
import json
import starburst.utils.log_jobs as log_jobs
import multiprocessing as mp
import starburst.drivers.main_driver as driver 
import subprocess
import copy
import itertools
import logging
import sweeps 
import job_generator
import sys 
import yaml 
import psutil
from typing import List
import re

import tempfile
import math 

DEFAULT_CONFIG = sweeps.DEFAULT_CONFIG
JOB_GENERATORS =  {
    'cpu_sleep': job_generator.CPUSleepJobGenerator,
    'gpu_sleep': job_generator.GPUSleepJobGenerator,
    'gpu_train': job_generator.GPUTrainJobGenerator,
}
LOG_DIRECTORY = '../sweep_logs/{name}/'

logger = logging.getLogger(__name__)

class RunConfig:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

def submit(jobs={}, arrivals=[], timestamp=None, index=None, clusters=None):
	def update_scheduler_submit_times(submit_times=None, timestamp=timestamp, index=index, arrivals=arrivals): 
		trial_data_path = f'{LOG_DIRECTORY.format(name=str(timestamp))}jobs/{str(index)}.yaml'
		job_data = {}
		# TODO: Figure out the bug for why schedule submit time fails 
		with open(trial_data_path, "r") as f:
			job_data = yaml.safe_load(f)
		for i in range(len(arrivals)):
			# TODO: add scheduler_submit_time value in addition to submit_time 
			if i in submit_times: 
				job_data[i]['scheduler_submit_time'] = submit_times[i] 

		with open(trial_data_path, "w") as f:
			yaml.safe_dump(job_data, f)

	start_time = time.time()
	curr_time = time.time()
	job_index = 0
	total_jobs = len(arrivals) #len(jobs)
	submit_times = {}
	p2_log = "../sweep_logs/" + timestamp + '/' + 'p2.log'

	while True:
		curr_time = time.time()
		if job_index < total_jobs and curr_time > arrivals[job_index][1] + start_time:
			job = jobs[job_index]
			with tempfile.NamedTemporaryFile(mode='w') as f:
				temp_file_path = f.name
				yaml.safe_dump(job['kube_yaml'], f)
				subprocess.run(['python3', '-m', 'starburst.drivers.submit_job', '--job-yaml', temp_file_path, '--submit-time', str(time.time())])
			#logger.debug(f'****** Job {job_index} submission time {time.time()}')
			submit_time = time.time()
			submit_times[job_index] = submit_time
			job_index += 1
			with open(p2_log, "a") as f:
				f.write("Submitting job " + str(job) + '\n')
			update_scheduler_submit_times(submit_times=submit_times)
		#TODO: Improve stop condition -- wait until last job completes
		time.sleep(0.01)
		if job_index >= total_jobs: 
			break
	update_scheduler_submit_times(submit_times=submit_times)
	

	def all_submitted(submitted_jobs):
		for submission_state in submitted_jobs.values():
			if submission_state == False: 
				return False 
		return True
	
	def check_submitted(submitted_jobs):
		def find_job_with_substring(jobs, substring):
			for job in jobs:
				if substring in job.metadata.name:
					return job
			return None

		def parse_jobs():
			with open(f'../sweep_logs/{timestamp}/events/{index}.log', "r") as f:
				cloud_log_list = f.read().split('\n')
			log_jobs = []
			for log in cloud_log_list[1:-1]:
				match = re.search(r"Cloud Job \|\| job id (\S+) \| (\S+)", log)
				match = match.groups()
				if match:
					job = int(match[0])
					log_jobs.append(job)
			return log_jobs
		
		config.load_kube_config(context=clusters['onprem'])
		onprem_api_batch = client.BatchV1Api()

		config.load_kube_config(context=clusters['cloud'])
		cloud_api_batch = client.BatchV1Api()

		apis = [onprem_api_batch, cloud_api_batch]
		for api in apis: 
			#job_list = api.list_namespaced_job(namespace="default")
			limit = None #50
			continue_token = ""
			job_list, _, _ = api.list_namespaced_job_with_http_info(namespace="default", limit=limit, _continue=continue_token)
			 
			for job in submitted_jobs: 
				try: 
					curr_job = find_job_with_substring(job_list.items, "job-" + str(job))#"sleep-" + str(job))
					if curr_job.status.succeeded == 1:
						submitted_jobs[job] = True 
				except Exception as e:
					pass
		
		if jobs['hyperparameters']['spill_to_cloud'] == False:
			cloud_jobs = parse_jobs()
			for job in cloud_jobs: 
				submitted_jobs[job] = True 
			
		return submitted_jobs
	
	# TODO: Verify if jobs is accesible
	submitted_jobs = {}
	for job in jobs:
		if job == 'hyperparameters':
			continue
		submitted_jobs[job] = False

	

	while not all_submitted(submitted_jobs=submitted_jobs):
		logger.debug("Running ...")
		with open(p2_log, "a") as f:
			f.write("Submitted Jobs State: " + str(submitted_jobs) + '\n')

		check_start = time.perf_counter()
		logger.debug("Checking State...")
		submitted_jobs = check_submitted(submitted_jobs=submitted_jobs)
		check_end = time.perf_counter()

		with open(p2_log, "a") as f:
			f.write("Check Time (seconds): " + str(check_end - check_start) + '\n')

		time.sleep(1)

	with open(p2_log, "a") as f:
		f.write("reached end of p2 " + str(index) + '\n')

	return 

def clear_logs(clusters={}):
	"""Automates clearing of cluster state by removing event, logs, and pods on both onprem and cloud cluster"""
	print("Started Clearing Logs...")

	config.load_kube_config(context=clusters['onprem'])
	onprem_api = client.CoreV1Api()
	onprem_api_batch = client.BatchV1Api()

	config.load_kube_config(context=clusters['cloud'])
	cloud_api = client.CoreV1Api()
	cloud_api_batch = client.BatchV1Api()

	cluster_apis = [(onprem_api, onprem_api_batch)]#, (cloud_api, cloud_api_batch)]

	while True:
		try:
			for apis in cluster_apis:
				api, api_batch = apis

				api.delete_collection_namespaced_event(
					namespace='default',
					body=client.V1DeleteOptions(),
				)

				jobs_list = api_batch.list_namespaced_job(namespace='default')
				#logger.debug(f'Jobs Running {jobs_list}')
				for job in jobs_list.items:
					logger.debug(f'Attempting to Delete {job.metadata.name}')
					api_batch.delete_namespaced_job(
						name=job.metadata.name, 
						namespace='default', 
						body=client.V1DeleteOptions(
							propagation_policy='Foreground', 
							grace_period_seconds=0
							)
					)

				jobs_list = api_batch.list_namespaced_job(namespace='default')
				for job in jobs_list.items:
					logger.debug(f'Remaining Jobs {job.metadata.name}')

				# TODO: Debug code that deletes all pods from previous runs 
				pods = api.list_namespaced_pod(namespace='default')
				for pod in pods.items:
					if "chakra" not in pod.metadata.name and "prepull" not in pod.metadata.name:  
						print(f"Deleting pod {pod.metadata.name} in namespace {pod.metadata.namespace}")
						api.delete_namespaced_pod(name=pod.metadata.name, namespace=pod.metadata.namespace, body=client.V1DeleteOptions())
					else:
						print(f"Skipping deletion of pod {pod.metadata.name} in namespace {pod.metadata.namespace}")

		except Exception as e:
			print(f"Caught an exception: {e}")
			print("Re-executing code...")
			continue
		else:
			jobs_list = api_batch.list_namespaced_job(namespace='default')
			if len(jobs_list.items) == 0: 
				print("No remaining jobs to delete...")
				break	
			else: 
				continue 
	print("Completed Clearing Logs...")

def log(tag=None, batch_repo=None, loop=True, onprem_cluster="", cloud_cluster="", index=None):
	cluster_event_data = log_jobs.event_data_dict()
	log_jobs.write_cluster_event_data(batch_repo=batch_repo, cluster_event_data=cluster_event_data, tag=tag, loop=loop, onprem_cluster=onprem_cluster, cloud_cluster=cloud_cluster, index=index)

def empty_cluster(clusters={}):
	"""Function returns true if there are any running pods in the cluster"""
	"""
	'status': {'active': None,
	'completed_indexes': None,
	'completion_time': datetime.datetime(2023, 4, 30, 7, 3, 35, tzinfo=tzutc()),
	'conditions': [{'last_probe_time': datetime.datetime(2023, 4, 30, 7, 3, 35, tzinfo=tzutc()),
					'last_transition_time': datetime.datetime(2023, 4, 30, 7, 3, 35, tzinfo=tzutc()),
					'message': None,
					'reason': None,
					'status': 'True',
					'type': 'Complete'}],
	'failed': None,
	'ready': 0,
	'start_time': datetime.datetime(2023, 4, 30, 7, 3, 29, tzinfo=tzutc()),
	'succeeded': 1,
	'uncounted_terminated_pods': {'failed': None, 'succeeded': None}}}
	"""

	config.load_kube_config(context=clusters['onprem'])
	onprem_api = client.CoreV1Api()
	onprem_api_batch = client.BatchV1Api()

	config.load_kube_config(context=clusters['cloud'])
	cloud_api = client.CoreV1Api()
	cloud_api_batch = client.BatchV1Api()

	cluster_apis = [(onprem_api, onprem_api_batch), (cloud_api, cloud_api_batch)]
	namespace="default"

	cluster_apis =  [(onprem_api, onprem_api_batch)]#, (cloud_api, cloud_api_batch)]
	for apis in cluster_apis:
		api, api_batch = apis
		pods = api.list_namespaced_pod(namespace)
		logger.debug(f'Running pods {[pod.metadata.name for pod in pods.items]}')
		running_pods = []
		for pod in pods.items:
			count = 0
			if (pod.status.phase == "Running"):
				if "chakra" in pod.metadata.name:
					#logger.debug(f'{pod.metadata.name}')
					count += 1
				if "prepull"in pod.metadata.name:
					#logger.debug(f'{pod.metadata.name}')
					count += 1
				if count == 0: 
					running_pods.append(pod.metadata.name)
				#elif "prepull" not in pod.metadata.name:
				#	running_pods.append(pod.metadata.name)
		#running_pods = [pod.metadata.name for pod in pods.items if (pod.status.phase == "Running") and ("chakra" not in pod.metadata.name) and ("prepull" not in pod.metadata.name))]
		logger.debug(f'Pending deletion pods {running_pods}')
		if running_pods:
			return False
		
		jobs = api_batch.list_job_for_all_namespaces()
		#unsuccessful_jobs = [job.status.succeeded for job in jobs.items if (("prepull" not in job.metadata.name) and job.status.succeeded != 1)]
		unsuccessful_jobs = []
		for job in jobs.items:
			#count = 0 
			logger.debug(f'Job name {job.metadata.name}')
			if "prepull" in job.metadata.name:
				#count += 1
				continue 
			if job.status.succeeded != 1:
				unsuccessful_jobs.append(job.status.succeeded)
		
		logger.debug(f'Pending job deletions {unsuccessful_jobs}')
		if unsuccessful_jobs:
			return False 

	return True 

def reached_last_job(job_name=None, clusters={}): 
	def find_job_with_substring(jobs, substring):
		for job in jobs:
			if substring in job.metadata.name:
				return job
		return None

	config.load_kube_config(context=clusters['onprem'])
	onprem_api = client.CoreV1Api()
	onprem_api_batch = client.BatchV1Api()

	try: 
		job_list = onprem_api_batch.list_namespaced_job(namespace="default")
		job = find_job_with_substring(job_list.items, job_name)
		status = job.status

		if job: 
			logger.debug("Job Succeeded")
			logger.debug(str(job.status.succeeded))
		if job.status.succeeded == 1:
			return True 
	except Exception as e:
		pass

	config.load_kube_config(context=clusters['cloud'])
	cloud_api = client.CoreV1Api()
	cloud_api_batch = client.BatchV1Api()

	try: 
		job_list = cloud_api_batch.list_namespaced_job(namespace="default")
		job = find_job_with_substring(job_list.items, job_name)
		status = job.status
		if job: 
			logger.debug("Succeed")
			logger.debug(str(job.status.succeeded))
		if job.status.succeeded == 1:
			return True 
	except Exception as e: 
		pass 

	return False 

def launch_submit(jobs={}, arrivals=[], timestamp=None, index=None, clusters=None):
	try: 
		submit(jobs=jobs, arrivals=arrivals, timestamp=timestamp, index=index, clusters=clusters)
	except Exception as e:
		import traceback
		t = traceback.format_exc()
		p2_log = "../sweep_logs/" + timestamp + '/' + 'p2.log'
		with open(p2_log, "a") as f:
			f.write("p2 failed \n " + t + '\n')
		pass

def generate_jobs(run_config: RunConfig):
	"""
	Generate jobs based on the job generation configuration. 
	"""
	rc = run_config
	np.random.seed(rc.random_seed)

	# Get the job generator class.
	job_gen_class = None
	if rc.workload_type  in JOB_GENERATORS:
		job_gen_class = JOB_GENERATORS[rc.workload_type]
	else:
		raise ValueError(f'Invalid workload type {rc.workload_type}.')
	
	# Initialize the job generator.
	all_params =  vars(run_config)
	job_gen = job_gen_class({key: all_params[key] for key in job_generator.JOB_GEN_ARRAY if key in all_params})

	jobs = {}
	arrivals = []
	job_index = 0
	total_submit_time = 0	
	while True:
		if total_submit_time >= rc.submit_time:
			break
		job = {}
		job['job_id'] = job_index
		job['workload_type'] = rc.workload_type
		job['resources'] = job_gen.get_resources()
		total_submit_time += job_gen.get_interarrival()
		job['submit_time'] = total_submit_time
		job['image'] = job_gen.image
		job['job_duration'] = job_gen.get_duration()
		
		arrivals.append((job_index, total_submit_time))

		env = Environment(
			loader=FileSystemLoader("../../job_templates"),
			autoescape=select_autoescape()
		)
		template = env.get_template(job_gen.get_jinja_template())
		jinja_dict = job_gen.get_jinja_dict(job)
		jinja_str = template.render(jinja_dict)
		job['kube_yaml'] = yaml.safe_load(jinja_str)
		jobs[job_index] = job
		job_index += 1
	jobs['hyperparameters'] = vars(run_config)
	return jobs, arrivals


def launch_run(run_config: dict, sweep_name: str, run_index: int = 0):
	run_config = RunConfig(run_config)
	jobs, arrivals = generate_jobs(run_config=run_config)
	save_jobs(jobs=jobs, sweep_name=sweep_name, run_index=run_index)
	import pdb; pdb.set_trace()
	grpc_port = 30000

	clusters = {
		"onprem": run_config.onprem_cluster,
		"cloud": run_config.cloud_cluster
	}
	logger.debug(f'Running policy: {run_config.policy}')
	sched_tick = run_config.sched_tick
	p0 = mp.Process(target=driver.custom_start, args=(grpc_port, sched_tick, clusters['onprem'], clusters['cloud'], run_config.waiting_policy, run_config.wait_time, jobs, sweep_name, run_index, run_config.policy))
	p0.start()
	
	logger.debug(f'Started cleaning cluster pods, jobs, and event logs...')
	clear_logs(clusters=clusters)
	while not empty_cluster(clusters=clusters):
		logger.debug(f'Cleaning...')
		print("Cleaning Logs and Cluster....")
		time.sleep(1)
	clear_logs(clusters=clusters)
	logger.debug(f'Completed cleaning cluster pods, jobs, and event logs...')
	
	# TODO: Delete file
	signal_file = LOG_DIRECTORY.format(name=sweep_name) + '/signal.lock' 
	try:
		os.unlink(signal_file)
	except Exception as e: 
		pass 


	tag = str(run_index)
	p1 = mp.Process(target=log, args=(tag, sweep_name, True, clusters['onprem'], clusters['cloud'], tag))
	p1.start()

	launch_submit(jobs, arrivals, sweep_name, tag, clusters)
	#p2 = mp.Process(target=launch_submit, args=(jobs, arrivals, sweep_name, tag, clusters))
	#p2.start()
	#p2.join()
	# TODO: Write file 
	with open(signal_file, "w") as f:
		pass
	p1.join()
	p0.terminate()
	logger.debug("Terminated Scheduler...")
	
	return 0 

#==================================================#

def save_jobs(jobs: dict, sweep_name: str, run_index: int = 0):
	"""
	Saves jobs to yaml file.
	
	Args:
		jobs (dict): Dictionary of jobs to save.
		sweep_name (str): Name of sweep.
		run_idx (int): Index of run.
	"""
	log_path = LOG_DIRECTORY.format(name=sweep_name)
	if not os.path.exists(log_path):
		raise Exception(f'Sweep logs {log_path} does not exist.')
	log_path += "jobs/"
	os.makedirs(log_path, exist_ok=True)
	
	jobs_path = f'{log_path}{run_index}.yaml'
	yaml_jobs = yaml.dump(jobs)
	with open(jobs_path, "w") as f:
		f.write(yaml_jobs)

def generate_runs(sweep_config: dict) -> List[dict]: 
	"""
	Takes specified fixed values and generates grid of hyperparameters based on varying values

	Args:
		sweep_config (dict): Dictionary of hyperparameters to sweep over.
	"""
	list_type_args = ['cpu_sizes', 'cpu_dist', 'gpu_sizes', 'gpu_dist']

	# Split sweep_config into fixed and varied hyperparameters.
	base_config = copy.deepcopy(sweeps.DEFAULT_CONFIG)
	varied_config = {}
	for key, value in sweep_config.items():
		if not isinstance(value, list):
			base_config[key] = value
		elif isinstance(value, list) and key in list_type_args \
			and not isinstance(value[0], list):
			base_config[key] = value
		else:
			varied_config[key] = value
	
	# Generate carteisan production across varied hyperparameters.
	keys = []
	values = []
	for key, value in varied_config.items():
		keys.append(key)
		values.append(value)
	grid_search = itertools.product(*values)

	# Generate runs from cartesian product.
	runs = {}
	for run_index, trial in enumerate(grid_search):
		for key_index, key in enumerate(keys):
			base_config[key] = trial[key_index]
		runs[run_index] = copy.deepcopy(base_config)
	return runs

def load_yaml_file(file_path: str) -> dict:
	"""
	Loads a YAML file from a specified file path.

	Args:
		file_path (str): Path to YAML file.
	"""
	file_path = os.path.abspath(file_path)
	if not os.path.isfile(file_path):
		raise FileNotFoundError(f"Sweep config YAML not found: {file_path}")
	with open(file_path, 'r') as file:
		data = yaml.safe_load(file)
	return data

def clear_prior_sweeps(retry_limit: int = 1) -> None:
	"""
	Deletes all prior sweeps from the cluster.

	Args:
		retry_limit (int): Number of times to retry deleting a sweep before giving up.
	"""
	# @TODO(Surya): Delete pods from prior sweeps.
	current_pid = os.getpid()
	for _ in range(retry_limit):
		# Get a list of all processes.
		processes = psutil.process_iter()
		found_submit_process = False
		for process in processes:
			try:
				# Obtain process name and CMD line arguments.
				name = process.name()
				cmdline = process.cmdline()
				# Check for prior sweeps and if the prior sweep is not this current sweep.
				if name == 'python3' and 'submit_jobs.py' in cmdline and process.pid != current_pid:
					# terminate the process
					process.terminate()
					found_submit_process = True
			except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
				pass
		if not found_submit_process:
			break

def create_log_directory(sweep_name: str=None) -> int:
	"""
	Creates a log directory for the entire sweep.

	Args:
		name (str): Name of the log directory for the current sweep.
	"""
	if not sweep_name:
		sweep_name  = str(int(time.time()))
	log_directory_path = LOG_DIRECTORY.format(name=sweep_name)
	absolute_path = os.path.abspath(log_directory_path)
	os.makedirs(absolute_path, exist_ok=True)
	return sweep_name

def save_sweep_runs(runs: dict, sweep_name: str) -> None:
	"""
	Saves the sweep runs to a JSON file.

	Args:
		runs (dict): Dictionary of runs to save.
		sweep_name (str): Name of the sweep.
	"""
	sweep_path = LOG_DIRECTORY.format(name=sweep_name)+ "sweep.yaml"
	yaml_runs = yaml.dump(runs)
	with open(sweep_path, "w") as f:
		f.write(yaml_runs)
	
def sweep_pipeline(sweep_config: str):
	"""
	Runs a hyperparameter sweep on the cluster.

	Args:
		sweep_config (str): Path to YAML file containing sweep configuration.
	"""
	# 1) Clean Sweeps from prior runs.
	clear_prior_sweeps(retry_limit=3)

	# 2) Create Log directory for sweep
	current_timestamp = create_log_directory()

	# 3) Load sweep config and generate runs.
	sweep_dict = load_yaml_file(sweep_config)
	runs_dict = generate_runs(sweep_dict)
	save_sweep_runs(runs_dict, current_timestamp)

	# 4) Launch runs in sequence.
	for run_idx in runs_dict.keys():
		launch_run(run_config=runs_dict[run_idx],
	     		   sweep_name=current_timestamp,
				   run_index=str(run_idx))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Submit a sweep of synthetically generated jobs.')
	parser.add_argument(
		'--config',
		type=str,
		default='../../scripts/cpu_sweep.yaml',
		help='Input YAML config.')
	parser.add_argument('--debug',
		     action='store_true',
			 help='Enable debug mode')
	args = parser.parse_args()
	sweep_pipeline(sweep_config=args.config)