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
from kubernetes import client, config
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

logger = logging.getLogger(__name__)

'''
Design Layout [DRAFT 4]
- Run all experiments in on large cluster
	- (1) Mimic separate nodes by paritioning existing nodes with boundaries
	- (2) Subpartition nodes within a given cluster to run specific nodes


Design Layout [DRAFT 3]
- Before each run within a sweep, create the cluster then delete the cluster
	- Cluster creation and deletion takes ~5-10 minutes to create -- another 5-10 minutes to delete 
		- There may be a quota on number of clusters I can launch
	- Steps to Complete
		- Create N cluster at once in parallel, where N > 100
		- Setup github code within each cluster then run a sweep 
		- SCP logs from scheduler VM back to local commputer
			- No need to scp any files or logs directly from k8s clusters
		- Then terminate the clusters all in parallel
Design Layout [DRAFT 2]

- Sweep Requirements -> Cluster -> Add Logs -> Parse Logs -> Analyze Sweep Requirements -> Plot
- Input Requirements -> Grid Search Values 

Design Layout [DRAFT 1]

1. Generate Job Hyperparameters
	a. Hyperparameters
		i. Arrival Time
		ii. Sleep Time
			a. 5 min lower bound
			b. 24 hr upper bound
		iii. Workload Size
			a. CPUs
			b. GPUs
2. Insert Hyperparameters into Jinja Job Yaml
3. Submit Batch of Jobs
	a. Same arrival time 
		i. Different sleep time 
		ii. Diferent workload size
	b. Randomly sampled arrival time
		i. Different sleep time
		ii. Different workload size

Example -- Fixed workload and sleep time
- Same workload, same sleep time
	- Varying arrival time
		- Simulate as a poisson process: https://timeseriesreasoning.com/contents/poisson-process/
		- Specify difference between arrival time of two events from exponential distribution
			- Keep a cumalitive sum of the times stored in an array
	- Submit Jobs to Array of Job times
		- Simple loop 
		- Multithreading 
			- https://www.studytonight.com/python/python-threading-timer-object

Option 1: 
	- if proability of event is less than generated thresshold then submit job 
	- space betwen two events follows exponential 
'''

'''
result_dict = {
	'idx': np.array([j.idx for j in finished_jobs]),
	'arrival': np.array([j.arrival for j in finished_jobs]),
	'start': np.array([j.start for j in finished_jobs]),
	'runtime': np.array([j.runtime for j in finished_jobs]),
	'deadline': np.array([j.deadline for j in finished_jobs]),
	'num_gpus': np.array([j.num_gpus for j in finished_jobs]),
	'state': np.array([j.state for j in finished_jobs]),
	'allocated_gpus': np.array([j.allocated_gpus for j in finished_jobs]),
	'simulator_spec': simulator_spec,
	'stats': {}
}
'''

'''
run_config = {
	# Cluster config
	'cluster_size': args.cluster_size,
	'gpus_per_node': args.gpus_per_node,
	'cpus_per_node': args.cpus_per_node,
	# Policy config
	'sched_alg': args.sched_alg,
	'binpack_alg': args.binpack_alg,
	'waiting_policy': args.waiting_policy,
	'backfill': args.backfill,
	'loop': args.loop,
	'predict_wait': args.predict_wait,
	# Simulator config
	'verbose': args.verbose,
	'debug': args.debug,
	'warmup_jobs': args.warmup_jobs,
	'jobgen_spec': {
		'dataset': args.dataset,
		'arrival_rate': args.arrival_rate,
		'cv_factor': args.cv_factor,
		'total_jobs': args.total_jobs,
		'job_runtime': args.job_runtime,
		'seed': args.seed
	}
}
'''

DEFAULT_HYPERPARAMETERS = {
	"uniform_arrival": 1, 
	"uniform_submission": False,
	"waiting_policy": "fifo_onprem_only",
	"time_constrained": True,
	#"onprem_cluster_nodes": 4,
	"cluster_size": 4,
	#"onprem_cpu_per_node": 8,
	"cpus_per_node": 8, 
	"cloud_cluster_nodes": 4, 
	"cloud_cpu_per_node": 8,  
	"random_seed": 0,
	'total_jobs': 100,
	"batch_time": 300,
	"wait_time": 0,
	"time_out": 5,
	"mean_duration": 30,
	"arrival_rate": 1,
	"cpu_sizes": [1,2,4,8,16,32],
	"cpu_dist": [0, 0.2, 0.2, 0.2, 0.2, 0.2], 
	"gpu_sizes": [1,2,4,8,16,32],
	"gpu_dist": [0, 0.2, 0.2, 0.2, 0.2, 0.2],
	"memory_sizes": [100, 500, 1000, 50000],
	"memory_dict": [0.25, 0.25, 0.25, 0.25],
}

"""
Core Dictionaries
- Job Dictionary
- TODO: Sweep Dictionary 

Core Functions
- Sweep 
	- Generate_Sweep()
"""

import concurrent.futures
from google.cloud import container_v1

def parallel_experiments(num_clusters=1, project_id = 'sky-burst', zone = 'us-central1-c', cluster_prefix='parallel-exp'):
	# Create a GKE client
	client = container_v1.ClusterManagerClient()

	def create_cluster(cluster_name):
		nonlocal project_id
		nonlocal zone

		# Define the cluster config
		cluster = {
			'name': cluster_name,
			'network': 'skypilot-vpc',
			'initial_node_count': 1,
			#'master_auth': {
			#	'username': 'admin',
			#	'password': 'passwordpassword'
			#},
			'node_config': {
				'machine_type': 'n1-standard-1',
				'disk_size_gb': 100,
				'oauth_scopes': [
					'https://www.googleapis.com/auth/compute',
					'https://www.googleapis.com/auth/devstorage.read_write',
					'https://www.googleapis.com/auth/logging.write',
					'https://www.googleapis.com/auth/monitoring'
				]
			}
		}

		# Create the cluster
		operation = client.create_cluster(project_id=project_id, zone=zone, cluster=cluster)
		#result = operation.result()
		status = operation.status
		print(f'Cluster {cluster_name} status {status}')
		return status

	def delete_cluster(cluster_name):
		nonlocal project_id
		nonlocal zone

		# Delete the cluster
		operation = client.delete_cluster(project_id=project_id, zone=zone, cluster_id=cluster_name)
		#result = operation.result()
		status = operation.status
		print(f'Cluster {cluster_name} status {status}')
		return status 

	# Use a ThreadPoolExecutor to create the clusters in parallel
	with concurrent.futures.ThreadPoolExecutor() as executor:
		# Submit the create_cluster function for each cluster to the executor
		futures = [executor.submit(create_cluster, f'{cluster_prefix}-{i}') for i in range(num_clusters)]
		# Wait for all the futures to complete
		'''
		for future in concurrent.futures.as_completed(futures):
			try:
				# Get the result of the future, if available
				result = future.result()
			except Exception as e:
				# Handle any exceptions raised by the create_cluster function
				print(f'Error creating cluster: {e}')
		'''

	# Use a ThreadPoolExecutor to delete the clusters in parallel
	with concurrent.futures.ThreadPoolExecutor() as executor:
		# Submit the delete_cluster function for each cluster to the executor
		futures = [executor.submit(delete_cluster, f'{cluster_prefix}-{i}') for i in range(num_clusters)]
		# Wait for all the futures to complete
		'''
		for future in concurrent.futures.as_completed(futures):
			try:
				# Get the result of the future, if available
				result = future.result()
			except Exception as e:
				# Handle any exceptions raised by the delete_cluster function
				print(f'Error deleting cluster: {e}')
		'''

class Config:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

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

		#TODO: Handle the inverse -- this is inaccurarte
		if hp.uniform_submission: 
			submit_time += hp.uniform_arrival
		else: 
			submit_time += max(0.05, np.random.exponential(scale=1/hp.arrival_rate))
		job_duration = np.random.exponential(scale=hp.mean_duration)
		cpus = int(np.random.choice(hp.cpu_sizes, p=hp.cpu_dist))
		gpus = min(0, int(np.random.exponential(scale=2)))
		memory = min(0, int(np.random.exponential(scale=50)))
		job['submit_time'] = submit_time
		job['scheduler_submit_time'] = None
		job['job_duration'] = job_duration
		workload = {"gpu": gpus, "cpu":cpus, "memory":memory}
		job['workload'] = workload
		jobs[job_index] = job
		arrivals.append((job_index, submit_time))
		job_index += 1
	
	#last_job = job_index - 1

	return jobs, arrivals#, last_job 

def save_jobs(jobs, repo, tag):
	log_path = "../logs/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path = "../logs/archive/"
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

def submit(jobs={}, arrivals=[], timestamp=None, index=None):
	start_time = time.time()
	curr_time = time.time()
	job_index = 0 #1
	total_jobs = len(arrivals) #len(jobs)
	submit_times = {}
	
	while True:
		curr_time = time.time()
		#print(str(job_index) + " " + str(total_jobs) +  " " + str(curr_time) + " " + str(arrivals[job_index]) + " " + str(start_time))
		#print(arrivals)
		#print(job_index)
		if job_index < total_jobs and curr_time > arrivals[job_index][1] + start_time:
			job = jobs[job_index]
			generate_sampled_job_yaml(job_id=job_index, sleep_time=job["job_duration"], workload=job['workload'])
			#os.system('python3 -m starburst.drivers.submit_job --job-yaml ../../examples/sampled/sampled_job.yaml')
			subprocess.run(['python3', '-m', 'starburst.drivers.submit_job', '--job-yaml', '../../examples/sampled/sampled_job.yaml'])
			submit_time = time.time()

			#if job_index not in submit_times: 
			#	submit_times[job_index] = []
			submit_times[job_index] = submit_time

			job_index += 1
		#TODO: Improve stop condition -- wait until last job completes
		
		if job_index >= total_jobs: 
			break

		'''
		elif (arrivals != []) and (curr_time >= start_time + arrivals[-1][1] + jobs["hyperparameters"]["time_out"]): 
			print("Job Connection Time Out...")
			break
		'''
	
	trial_data_path = "../logs/archive/" + str(timestamp) + "/jobs/" + str(index) + ".json"
	job_data = {}
	with open(trial_data_path, "r") as f: #"../logs/event_data.json", "r") as f:
		job_data = json.load(f)

	for i in range(len(arrivals)):
		#job_data[str(i)]['submit_time'] = submit_times[i]
		# TODO: add scheduler_submit_time value in addition to submit_time 
		job_data[str(i)]['scheduler_submit_time'] = submit_times[i] 

	with open(trial_data_path, "w") as f: #"../logs/event_data.json", "r") as f:
		#job_data = json.dump(f)
		json.dump(job_data, f)

	return 

def execute(hyperparameters, repo, tag): 
	jobs, arrivals = generate_jobs(hyperparameters)
	save_jobs(jobs, repo, tag)
	submit(jobs, arrivals)

def generate_sampled_job_yaml(job_id=0, arrival_time=0, sleep_time=5, workload={"cpu": 0, "memory": 0, "gpu": 0}):
	""" Generalizes job submission to perform hyperparameter sweep """
	# TODO: Finalize design
	output = ""
	env = Environment(
		loader=FileSystemLoader("../../examples/sampled/templates"),
		autoescape=select_autoescape()
	)

	template = env.get_template("sampled_job.yaml.jinja")
	output += template.render({"job":str(job_id), "time":str(sleep_time)})

	set_limits = False

	for w in workload.values():
		print(w)
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
		print(w)
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

def clear_logs():
	# TODO: Automate log cleaning
	# TODO: Remove logs and both onprem and cloud cluster
	print("Started Clearing Logs...")

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()
	onprem_api_batch = client.BatchV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()
	cloud_api_batch = client.BatchV1Api()

	cluster_apis = [(onprem_api, onprem_api_batch), (cloud_api, cloud_api_batch)]

	'''
	for apis in cluster_apis:
		# TODO: Add a try catch exception in case deletion fails 

		api, api_batch = apis
		# Delete all event logs in the cluster
		api.delete_collection_namespaced_event(
			namespace='default',  # Replace with the namespace where you want to delete the events
			body=client.V1DeleteOptions(),
		)

		jobs_list = api_batch.list_namespaced_job(namespace='default')
		for job in jobs_list.items:
			api_batch.delete_namespaced_job(
				name=job.metadata.name, 
				namespace='default', 
				body=client.V1DeleteOptions(
					propagation_policy='Foreground', 
					grace_period_seconds=0
					)
			)
	'''

	while True:
		try:
			# code to try executing
			for apis in cluster_apis:
				# TODO: Add a try catch exception in case deletion fails 

				api, api_batch = apis
				# Delete all event logs in the cluster
				api.delete_collection_namespaced_event(
					namespace='default',  # Replace with the namespace where you want to delete the events
					body=client.V1DeleteOptions(),
				)

				jobs_list = api_batch.list_namespaced_job(namespace='default')
				for job in jobs_list.items:
					api_batch.delete_namespaced_job(
						name=job.metadata.name, 
						namespace='default', 
						body=client.V1DeleteOptions(
							propagation_policy='Foreground', 
							grace_period_seconds=0
							)
					)

				# TODO: Debug code that deletes all pods from previous runs 
				# List all the pods in the target namespace
				pods = api.list_namespaced_pod(namespace='default')

				# Iterate through the pods and delete them
				for pod in pods.items:
					print(f"Deleting pod {pod.metadata.name} in namespace {pod.metadata.namespace}")
					api.delete_namespaced_pod(name=pod.metadata.name, namespace=pod.metadata.namespace, body=client.V1DeleteOptions())
					

			# raise an exception to test
		except Exception as e:
			# print the exception message
			print(f"Caught an exception: {e}")
			# re-execute the code inside the try block
			print("Re-executing code...")
			continue
		else:
			# if no exceptions were raised, break out of the loop
			print("Logs cleared successfully.")
			break	
	print("Completed Clearing Logs...")

def log(tag=None, batch_repo=None, loop=True):
	event_data = log_jobs.event_data_dict()
	log_jobs.write_cluster_event_data(batch_repo=batch_repo, event_data=event_data, tag=tag, loop=loop)

def empty_cluster():
	"""Function returns true if there are any running pods in the cluster"""
	'''
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()

	cluster_apis = [onprem_api, cloud_api]
	namespace = "default"
	'''
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()
	onprem_api_batch = client.BatchV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()
	cloud_api_batch = client.BatchV1Api()

	cluster_apis = [(onprem_api, onprem_api_batch), (cloud_api, cloud_api_batch)]
	namespace="default"

	for apis in cluster_apis:
		api, api_batch = apis
		pods = api.list_namespaced_pod(namespace)
		running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
		if running_pods:
			return False

		jobs = api_batch.list_job_for_all_namespaces()
		running_jobs = [job.status.succeeded for job in jobs.items if job.status.succeeded != 1] # if pod.status.phase == "Running"]
		#print(running_jobs)
		#time.sleep(1000)
		if running_jobs:
			return False 

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
	'''
	for api in cluster_apis:
		pods = api.list_namespaced_pod(namespace)
		running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
		if running_pods:
			return False
	'''
	'''
	for api in cluster_apis:
		jobs = api.list_job_for_all_namespaces()
		running_jobs = [job.status for job in jobs.items]# if pod.status.phase == "Running"]
		print(running_jobs)
		time.sleep(1000)
		if running_jobs:
			return False
	'''
	return True 

def reached_last_job(job_name): 
	def find_job_with_substring(jobs, substring):
		for job in jobs:
			if substring in job.metadata.name:
				return job
		return None


	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()
	onprem_api_batch = client.BatchV1Api()

	try: 
		job_list = onprem_api_batch.list_namespaced_job(namespace="default")
		job = find_job_with_substring(job_list.items, job_name)

		status = job.status

		if job: 
			logger.debug("Succ")
			logger.debug(str(job.status.succeeded))
			#logger.debug("Found job")# + str(job))
			#logger.debug("Succeeded status " + str(job.status.succeeded) + " " + str(status.succeeded) + " " + str(status['succeeded']))
			#logger.debug("Found job with status " + str(status))
			
		#job = onprem_api_batch.read_namespaced_job(name=job_name, namespace="default")
		

		#if status.succeeded is not None and status.succeeded > 0:
		#if status.succeeded == 1:
		#if job.status.succeeded == 1 or status.succeeded == 1 or status['succeeded'] == 1:
		if job.status.succeeded == 1:
			return True 
	except Exception as e:
		pass

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()
	cloud_api_batch = client.BatchV1Api()

	try: 
		job_list = cloud_api_batch.list_namespaced_job(namespace="default")
		job = find_job_with_substring(job_list.items, job_name)
		status = job.status

		if job: 
			logger.debug("Succ")
			logger.debug(str(job.status.succeeded))
			#logger.debug("Found job")# + str(job))
			#logger.debug("Succeeded status " + str(job.status.succeeded) + " " + str(status.succeeded) + " " + str(status['succeeded']))
			#logger.debug("Found job with status " + str(status))
			

		#if job: 
		#	logger.debug("Found job " + str(job))

		#job = cloud_api_batch.read_namespaced_job(name=job_name, namespace="default")
		#status = job.status

		#if status.succeeded is not None and status.succeeded > 0:
		#if status.succeeded == 1:
		#if job.status.succeeded == 1 or status.succeeded == 1 or status['succeeded'] == 1:
		if job.status.succeeded == 1:
			return True 
	except Exception as e: 
		pass 

	return False 


def run(hyperparameters, batch_repo, index):
	hp = Config(hyperparameters)
	jobs, arrivals = generate_jobs(hyperparameters=hyperparameters)
	logger.debug("JOBS SUBMITTED " + str(jobs))
	save_jobs(jobs=jobs, repo=batch_repo, tag=index)
	c1, c2 = mp.Pipe()
	grpc_port = 10000

	p0 = mp.Process(target=driver.custom_start, args=(None, c2, grpc_port, 1, "gke_sky-burst_us-central1-c_starburst","gke_sky-burst_us-central1-c_starburst-cloud", hp.waiting_policy, hp.wait_time, jobs))
	p0.start()
	
	clear_logs()
	while not empty_cluster():
		print("Cleaning Logs and Cluster....")
		time.sleep(1)
	clear_logs()
	
	tag = str(index)
	p1 = mp.Process(target=log, args=(tag, batch_repo, True))
	p2 = mp.Process(target=submit, args=(jobs, arrivals, batch_repo, index))
	p1.start()
	p2.start()

	# Keep running until last job is completed
	last_job = len(jobs) - 2
	while True:
		logger.debug("Waiting for last job to complete $$$")
		if reached_last_job("sleep-" + str(last_job)):
			p1.terminate()
			p2.terminate()
			break 

	p1 = mp.Process(target=log, args=(tag, batch_repo, False))
	p1.start()
	while (p1.is_alive()):
		print("Saving last logs....")
		print("p1 alive status: " + str(p1.is_alive()))
		time.sleep(1)

	p0.terminate()
	
	return 0 

def run_sweep(sweep={}):#, fixed_values=OrderedDict(), varying_values=OrderedDict()):
	sweep_timestamp =  str(int(datetime.now().timestamp()))
	sweep_dir = "../logs/archive/" + sweep_timestamp + "/"
	if not os.path.exists(sweep_dir):
		os.mkdir(sweep_dir)
	sweep_path = sweep_dir + "sweep.json"

	with open(sweep_path, "w") as f:
		json.dump(sweep, f)

	for i in range(len(sweep) - 2):
		hp = sweep[i]
		run(hp, sweep_timestamp, str(i))

	return sweep_timestamp

#def submit_sweep(fixed_values=OrderedDict(), varying_values=OrderedDict()):
def submit_sweep(sweep=None):
	fixed_values = OrderedDict(sweep['fixed_values'])
	varying_values = OrderedDict(sweep['varying_values'])
	sweep = generate_sweep(fixed_values=fixed_values, varying_values=varying_values)
	#save_sweep(sweep=sweep, fixed_values=fixed_values, varying_values=varying_values)
	time_stamp = run_sweep(sweep)
	return time_stamp

def plot_sweep(sweep_timestamp=0, fixed_values=OrderedDict(), varying_values=OrderedDict()):
	print("Analyzing and plotting data...")
	metrics, all_jobs = log_jobs.analyze_sweep(event_number=sweep_timestamp, graph=True)#, fixed_values=fixed_values, varying_values=varying_values)
	print("Plotting complete...")
	return 

def generate_sweep(fixed_values=OrderedDict(), varying_values=OrderedDict()): 
	"""
	Takes specified fixed values and generates grid of hyperparameters based on varying values 
	"""
	# TODO: Integrate hpo tool (e.g. optuna)
	# TODO: Specify grid search values, then plot them

	'''
	Example 1:
	Sweep: 
		1 - arrival rates
		2 - waiting times
		3 - policy
		4 - cpu_dist

		- order
		- cpu dist [row] 
			- waiting time [column]
				- arrival rate [data]
	'''
	sweep={}
	sweep["fixed_values"] = fixed_values
	sweep["varying_values"] = varying_values
	# DEFAULT VALUES
	hyperparameters = copy.deepcopy(DEFAULT_HYPERPARAMETERS)
	
	# FIXED VALUES
	for key, value in fixed_values.items(): 
		hyperparameters[key] = value

	# VARYING VALUES
	# TODO: Create cartesian product of values then iterate through the values and map them to a job index

	keys = []
	values = []
	for key, value in varying_values.items():
		keys.append(key)
		values.append(value)

	#values = values[::-1]

	grid_search = itertools.product(*values)
	
	for trial_index, trial in enumerate(grid_search):
		for key_index, key in enumerate(keys):
			hyperparameters[key] = trial[key_index]
		sweep[trial_index] = copy.deepcopy(hyperparameters)

	'''
	# SWEEP 1
	hyperparameters["policy"] = "fifo_wait"

	for cpu_dist in cpu_dists: 
		for w in wait_times:
			for a in arrival_rates:
				hyperparameters["cpu_dist"] = cpu_dist
				hyperparameters["arrival_rate"] = a
				hyperparameters["wait_time"] = w
				sweep[index] = copy.deepcopy(hyperparameters)
				index += 1
	'''

	'''
	# SWEEP 2
	hyperparameters["policy"] = "fifo_onprem_only"

	for cpu_dist in cpu_dists: 
		for a in arrival_rates:
			hyperparameters["cpu_dist"] = cpu_dist
			hyperparameters["arrival_rate"] = a
			sweep[index] = copy.deepcopy(hyperparameters)
			index += 1			
	'''

	'''
	# SWEEP 3
	hyperparameters["policy"] = "time_estimator"

	for cpu_dist in cpu_dists: 
		for a in arrival_rates:
			hyperparameters["arrival_rate"] = a
			hyperparameters["wait_time"] = w
			sweep[index] = hyperparameters
			index += 1
	'''
	
	return sweep

def generate_interval(min=0, max=10, intervals=10):
	return np.linspace(min, max, num=intervals+1).tolist()

def main():
	"""
	Note: Only execute sweep through the main function, since mp package fails otherwise
	"""
	sweep = sweeps.SWEEPS['6']
	submit_sweep(sweep=sweep)
	return 

if __name__ == '__main__':
    main()
	#pass

"""
UTIL + MISC FUNCTIONS
"""

def start_scheduler(policy="fifo_onprem_only", onprem_cluster="gke_sky-burst_us-central1-c_starburst", cloud_cluster="gke_sky-burst_us-central1-c_starburst-cloud"):
	os.system('python3 -m starburst.drivers.main_driver --policy {} --onprem_k8s_cluster_name {} --cloud_k8s_cluster_name {}'.format(policy, onprem_cluster, cloud_cluster))
	#subprocess.run(['python3', '-m', 'starburst.drivers.main_driver' '--policy', policy, '--onprem_k8s_cluster_name', onprem_cluster,'--cloud_k8s_cluster_name', cloud_cluster])
	#python3 -m starburst.drivers.main_driver --policy fifo_onprem_only --onprem_k8s_cluster_name gke_sky-burst_us-central1-c_starburst --cloud_k8s_cluster_name gke_sky-burst_us-central1-c_starburst-cloud
	#starburst, driver.custom_start(onprem_k8s_cluster_name=onprem_cluster, cloud_k8s_cluster_name=cloud_cluster, policy=policy)
	return 

def view_submitted_arrival_times(num_jobs = 100, batch_time=100): 
	batches = 5
	fig, axs = plt.subplots(nrows=5, ncols=1)
	arrival_rates = np.linspace(0, 8, num=batches+1).tolist()[1:]
	
	arrival_times = []
	for i in range(len(arrival_rates)):
		ar = arrival_rates[i]
		#times = submit_jobs(time_constrained=True, batch_time=batch_time, arrival_rate=ar, sleep_mean=10, submit=False)
		hyp =  copy.deepcopy(DEFAULT_HYPERPARAMETERS)
		hyp['arrival_rate'] = 10
		hyp['batch_time'] = 600
		hyp['mean_duration'] = 60
		times = generate_jobs(hyp)
		arrival_times.append(times)
		axs[i].eventplot(times)
		axs[i].set_ylabel(str(ar))
		axs[i].set_xlim((0, hyp['batch_time']))#800))
		axs[i].set_yticks([])
	plt.show()