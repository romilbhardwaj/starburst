import argparse
import numpy as np 
import matplotlib.pyplot as plt
import os 
import time
import datetime
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from kubernetes import client, config
from datetime import datetime
from starburst.drivers import main_driver
import json
import starburst.utils.log_jobs as log_jobs
import multiprocessing as mp
import starburst.drivers.main_driver as driver 
import subprocess
import copy
import itertools
from collections import defaultdict
from collections import OrderedDict
import atexit 
import logging
import sweeps 
import concurrent.futures
from google.cloud import container_v1
import sys 
import yaml 
import requests
import psutil
from typing import List
import re

import math 
import training_dataset

DEFAULT_HYPERPARAMETERS = sweeps.DEFAULT_HYPERPARAMETERS
ESTIMATED_TIMES = training_dataset.ESTIMATED_TIMES
LOG_DIRECTORY = '../sweep_logs/'

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

def get_training_jobs(gpu):
	"""returns list of runtimes and jobs with specified number of gpus"""
	valid_jobs = []
	for job in ESTIMATED_TIMES: 
		if job[2] == gpu: 
			valid_jobs.append((job[1], job[3]))
	return valid_jobs

def sample_training_job(gpu, runtime):
	"return script the closest fils gpu runtime pair"
	jobs = get_training_jobs(gpu)
	#id = 0
	min_delta = math.inf
	min_id = 0  
	for i in range(len(jobs)):
		job = jobs[i]
		delta = abs(jobs[i][0] - runtime)
		if delta <= min_delta: 
			min_delta = delta
			min_id = i
	logger.debug(f'exponentially distributed time {runtime} -- mapped time {jobs[min_id][0]} -- gpu {gpu}')
	return jobs[min_id]

def generate_jobs(hyperparameters): 
	jobs = {}
	hp = Config(hyperparameters)
	jobs = {}
	jobs['hyperparameters'] = hyperparameters
	arrivals = []
	np.random.seed(hp.random_seed)

	job_index = 0 #1
	submit_time = 0

	while True:
		if hp.time_constrained == True and submit_time > hp.batch_time:
			break
		elif hp.time_constrained == False and job_index >= hp.total_jobs:
			break
		job = {}
		gpus = int(np.random.choice(hp.gpu_sizes, p=hp.gpu_dist)) #min(0, int(np.random.exponential(scale=2)))
		cpus = 11 * gpus

		logger.debug(f'workload type: {hp.workload_type}')
		if hp.workload_type == 'cpu':
			gpus = 0
			cpus = int(np.random.choice(hp.cpu_sizes, p=hp.cpu_dist))

		memory = 0 #min(0, int(np.random.exponential(scale=50)))
		workload = {"gpu": gpus, "cpu":cpus, "memory":memory}
		job['workload'] = workload
		job['workload_type'] = hp.workload_type

		if hp.uniform_submission:
			submit_time += hp.uniform_arrival
		else: 
			submit_time += max(3, np.random.exponential(scale=1/hp.arrival_rate)) # TODO: Normalize this value 

		job_duration = max(30, np.random.exponential(scale=hp.mean_duration))
		job_duration = min(job_duration, 10000) # Set upperbound

		# TODO: Implement training -- include estimate runtime
		if hp.sample_real_workloads:
			logger.debug(f'sampling real world workloads')
			estimated_runtime, training_job_script = sample_training_job(gpus, job_duration)
			job['setup_script'] = training_job_script
			job['job_duration'] = estimated_runtime
		else:
			job['setup_script'] = hp.setup_script
			job['job_duration'] = job_duration

		# TODO: First find set of all jobs with same # of gpus
		# TODO: Find job with closest time given gpu distribution 

		#cpus = int(np.random.choice(hp.cpu_sizes, p=hp.cpu_dist))
		
		job['submit_time'] = submit_time
		job['scheduler_submit_time'] = None
		job['image'] = hp.image
		#job['sleep'] = hp.sleep
		job['job_type'] = hp.job_type
		jobs[job_index] = job
		arrivals.append((job_index, submit_time))
		job_index += 1

	return jobs, arrivals

def save_jobs(jobs, repo, tag):
	log_path = "../sweep_logs/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path = "../sweep_logs/archive/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path += repo + "/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path += "jobs/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	current_log_path = log_path + tag + ".json"
	with open(current_log_path, "w") as f:
		json.dump(jobs, f)

def submit(jobs={}, arrivals=[], timestamp=None, index=None, clusters=None):
	def update_scheduler_submit_times(submit_times=None, timestamp=timestamp, index=index, arrivals=arrivals): 
		trial_data_path = "../sweep_logs/archive/" + str(timestamp) + "/jobs/" + str(index) + ".json"
		job_data = {}
		# TODO: Figure out the bug for why schedule submit time fails 
		with open(trial_data_path, "r") as f:
			job_data = json.load(f)

		for i in range(len(arrivals)):
			# TODO: add scheduler_submit_time value in addition to submit_time 
			if i in submit_times: 
				job_data[str(i)]['scheduler_submit_time'] = submit_times[i] 

		with open(trial_data_path, "w") as f:
			json.dump(job_data, f)

	start_time = time.time()
	curr_time = time.time()
	job_index = 0 #1
	total_jobs = len(arrivals) #len(jobs)
	submit_times = {}
	p2_log = "../sweep_logs/archive/" + timestamp + '/' + 'p2.log'

	while True:
		curr_time = time.time()
		if job_index < total_jobs and curr_time > arrivals[job_index][1] + start_time:
			job = jobs[job_index]
			generate_sampled_job_yaml(job_id=job_index, job=job)
			submit_time = time.time()
			subprocess.run(['python3', '-m', 'starburst.drivers.submit_job', '--job-yaml', '../../examples/sampled/sampled_job.yaml', '--submit-time', str(submit_time)])
			#logger.debug(f'****** Job {job_index} submission time {time.time()}')
			submit_time = time.time()
			submit_times[job_index] = submit_time
			job_index += 1
			with open(p2_log, "a") as f:
				f.write("Submitting job " + str(job) + '\n')
			update_scheduler_submit_times(submit_times=submit_times)
		#TODO: Improve stop condition -- wait until last job completes
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
			with open(f'../sweep_logs/archive/{timestamp}/events/{index}.log', "r") as f:
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

def generate_sampled_job_yaml(job_id=0, job=None):
	""" 
	Generalizes job submission to perform hyperparameter sweep 
	# TODO: Finalize design
	# TODO: Input the following value back into the yaml -- imagePullPolicy: Always
	# TODO: Integrate skyburst yamls: https://github.com/michaelzhiluo/skyburst/tree/main/task_yamls
	# TODO: Modify job object to support the following values: 
	image=job['image']
	setup_script=job['setup_script']
	"""
	output = ""
	env = Environment(
		loader=FileSystemLoader("../../examples/sampled/templates"),
		autoescape=select_autoescape()
	)

	sleep_time=job["job_duration"]
	workload=job['workload']
	image=job['image']
	setup_script=job['setup_script']
	#sleep=job['sleep']
	job_type=job['job_type']
	workload_type=job['workload_type']

	#nvidia-smi --query-gpu=uuid --format=csv,noheader && echo "||" && sleep {{time}}

	if job_type == 'sleep': 
		template = env.get_template("sampled_job.yaml.jinja")
		if workload_type == 'cpu':
			gpu_setup = 'echo "||"'
		else:
			gpu_setup == 'nvidia-smi --query-gpu=uuid --format=csv,noheader && echo "||"'
		output += template.render({"job":str(job_id), "time":str(sleep_time), "gpu_script": gpu_setup})
	elif job_type == 'train':
		template = env.get_template("train_job.yaml.jinja")
		output += template.render({"job":str(job_id), "image":str(image), "setup_script":str(setup_script)})

	set_limits = False
	# TODO: Merge all these for loops into one

	#if workload_type == 'cpu':
	#	if 'gpu' in workload:
	#		workload.pop('gpu')
			
	for w in workload.values():
		if w > 0:
			set_limits = True
			template = env.get_template("resource_limit.yaml.jinja")
			output += "\n" + template.render()
			break
	
	for w in workload:
		if workload[w] > 0:
			template = env.get_template("{}_resource.yaml.jinja".format(w))
			output += "\n" + template.render({w: workload[w]})

	for w in workload.values():
		if w > 0:
			set_limits = True
			template = env.get_template("resource_request.yaml.jinja")
			output += "\n" + template.render()
			break 

	for w in workload: 
		if workload[w] > 0: 
			template = env.get_template("{}_resource.yaml.jinja".format(w))
			output += "\n" + template.render({w: workload[w]})

	template = env.get_template("restart_limit.yaml.jinja")
	output += "\n" + template.render()

	job_yaml = open("../../examples/sampled/sampled_job.yaml", "w")
	job_yaml.write(output)
	job_yaml.close()
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


def starburst_run(hyperparameters, batch_repo, index, tick):

	hp = Config(hyperparameters)
	jobs, arrivals = generate_jobs(hyperparameters=hyperparameters)
	logger.debug("JOBS SUBMITTED " + str(jobs))
	save_jobs(jobs=jobs, repo=batch_repo, tag=index)
	c1, c2 = mp.Pipe()
	grpc_port = 30000 #9999 #50051

	clusters = {
		"onprem": hp.onprem_cluster,
		"cloud": hp.cloud_cluster
	}
	logger.debug(f'Running policy: {hp.policy}')
	sched_tick = tick
	p0 = mp.Process(target=driver.custom_start, args=(grpc_port, sched_tick, clusters['onprem'], clusters['cloud'], hp.waiting_policy, hp.wait_time, jobs, batch_repo, index, hp.policy))
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
	signal_file = "../sweep_logs/archive/"+ batch_repo + '/signal.lock' 
	try:
		os.unlink(signal_file)
	except Exception as e: 
		pass 


	tag = str(index)
	p1 = mp.Process(target=log, args=(tag, batch_repo, True, clusters['onprem'], clusters['cloud'], index))
	p2 = mp.Process(target=launch_submit, args=(jobs, arrivals, batch_repo, index, clusters))
	p1.start()
	p2.start()
	p2.join()
	# TODO: Write file 
	with open(signal_file, "w") as f:
		pass
	p1.join()
	p0.terminate()
	logger.debug("Terminated Scheduler...")
	
	return 0 

def launch_submit(jobs={}, arrivals=[], timestamp=None, index=None, clusters=None):
	try: 
		submit(jobs=jobs, arrivals=arrivals, timestamp=timestamp, index=index, clusters=clusters)
	except Exception as e:
		import traceback
		t = traceback.format_exc()
		p2_log = "../sweep_logs/archive/" + timestamp + '/' + 'p2.log'
		with open(p2_log, "a") as f:
			f.write("p2 failed \n " + t + '\n')
		pass 


def run_sweep(sweep={}, sweep_timestamp=None):
	sweep_dir = "../sweep_logs/archive/" + sweep_timestamp + "/"
	if not os.path.exists(sweep_dir):
		os.mkdir(sweep_dir)
	sweep_path = sweep_dir + "sweep.json"

	with open(sweep_path, "w") as f:
		json.dump(sweep, f)

	for i in range(len(sweep)):
		hp = sweep[i]
		tick = hp['sched_tick']
		starburst_run(hp, sweep_timestamp, str(i), tick)


def sweep_pipeline(sweep_config: str):
	"""
	Runs a hyperparameter sweep on the cluster.

	Args:
		sweep_config (str): Path to YAML file containing sweep configuration.
	"""
	# 1) Clean Sweeps from prior runs.
	clear_prior_sweeps(retry_limit=3)

	# 2) Load sweep config and generate runs.
	sweep = load_yaml_file(sweep_config)
	sweep_dict = generate_runs(sweep)

	# Create Log directories
	current_timestamp = int(time.time())
	directory_path = f"../sweep_logs/archive/{current_timestamp}"
	absolute_path = os.path.abspath(directory_path)
	os.makedirs(absolute_path, exist_ok=True)

	run_sweep(sweep=sweep_dict, sweep_timestamp=current_timestamp)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Submit a sweep of synthetically generated jobs.')
	parser.add_argument(
		'--config',
		type=str,
		default='../../scripts/cpu_sweep.yaml',
		help='Input YAML config.')
	args = parser.parse_args()
	sweep_pipeline(sweep_config=args.config)


def generate_runs(sweep_config: dict) -> List[dict]: 
	"""
	Takes specified fixed values and generates grid of hyperparameters based on varying values

	"""
	list_type_args = ['cpu_sizes', 'cpu_dist', 'gpu_sizes', 'gpu_dist']

	# Split sweep_config into fixed and varied hyperparameters.
	base_config = copy.deepcopy(sweeps.DEFAULT_HYPERPARAMETERS)
	varied_config = {}
	for key, value in sweep_config.items():
		if not isinstance(value, list):
			base_config[key] = value
		elif isinstance(value, list) and key in list_type_args and not isinstance(value[0], list):
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