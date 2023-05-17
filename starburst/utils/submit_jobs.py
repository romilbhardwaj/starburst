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

DEFAULT_HYPERPARAMETERS = sweeps.DEFAULT_HYPERPARAMETERS

logger = logging.getLogger(__name__)

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
		if hp.uniform_submission: 
			submit_time += hp.uniform_arrival
		else: 
			submit_time += max(3, np.random.exponential(scale=1/hp.arrival_rate))
		job_duration = np.random.exponential(scale=hp.mean_duration)
		gpus = int(np.random.choice(hp.gpu_sizes, p=hp.gpu_dist)) #min(0, int(np.random.exponential(scale=2)))
		cpus = 11 * gpus
		#cpus = int(np.random.choice(hp.cpu_sizes, p=hp.cpu_dist))
		memory = min(0, int(np.random.exponential(scale=50)))
		job['submit_time'] = submit_time
		job['scheduler_submit_time'] = None
		job['job_duration'] = job_duration
		workload = {"gpu": gpus, "cpu":cpus, "memory":memory}
		job['workload'] = workload
		job['image'] = hp.image
		job['setup_script'] = hp.setup_script
		job['sleep'] = hp.sleep


		jobs[job_index] = job
		arrivals.append((job_index, submit_time))
		job_index += 1

	return jobs, arrivals

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
		if job_index < total_jobs and curr_time > arrivals[job_index][1] + start_time:
			job = jobs[job_index]
			generate_sampled_job_yaml(job_id=job_index, job=job)
			subprocess.run(['python3', '-m', 'starburst.drivers.submit_job', '--job-yaml', '../../examples/sampled/sampled_job.yaml'])
			submit_time = time.time()
			submit_times[job_index] = submit_time
			job_index += 1
		#TODO: Improve stop condition -- wait until last job completes
		if job_index >= total_jobs: 
			break
	
	trial_data_path = "../logs/archive/" + str(timestamp) + "/jobs/" + str(index) + ".json"
	job_data = {}
	with open(trial_data_path, "r") as f:
		job_data = json.load(f)

	for i in range(len(arrivals)):
		# TODO: add scheduler_submit_time value in addition to submit_time 
		job_data[str(i)]['scheduler_submit_time'] = submit_times[i] 

	with open(trial_data_path, "w") as f:
		json.dump(job_data, f)

	return 

'''
def execute(hyperparameters, repo, tag): 
	jobs, arrivals = generate_jobs(hyperparameters)
	save_jobs(jobs, repo, tag)
	submit(jobs, arrivals)
'''

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
	sleep=job['sleep']

	if sleep: 
		template = env.get_template("sampled_job.yaml.jinja")
		output += template.render({"job":str(job_id), "time":str(sleep_time)})
	else:
		template = env.get_template("train_job.yaml.jinja")
		output += template.render({"job":str(job_id), "image":str(image), "setup_script":str(setup_script)})

	set_limits = False

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

	cluster_apis = [(onprem_api, onprem_api_batch), (cloud_api, cloud_api_batch)]

	while True:
		try:
			for apis in cluster_apis:
				api, api_batch = apis

				api.delete_collection_namespaced_event(
					namespace='default',
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
				pods = api.list_namespaced_pod(namespace='default')
				for pod in pods.items:
					print(f"Deleting pod {pod.metadata.name} in namespace {pod.metadata.namespace}")
					api.delete_namespaced_pod(name=pod.metadata.name, namespace=pod.metadata.namespace, body=client.V1DeleteOptions())
		except Exception as e:
			print(f"Caught an exception: {e}")
			print("Re-executing code...")
			continue
		else:
			print("Logs cleared successfully.")
			break	
	print("Completed Clearing Logs...")

def log(tag=None, batch_repo=None, loop=True, onprem_cluster="", cloud_cluster=""):
	cluster_event_data = log_jobs.event_data_dict()
	log_jobs.write_cluster_event_data(batch_repo=batch_repo, cluster_event_data=cluster_event_data, tag=tag, loop=loop, onprem_cluster=onprem_cluster, cloud_cluster=cloud_cluster)

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

	for apis in cluster_apis:
		api, api_batch = apis
		pods = api.list_namespaced_pod(namespace)
		running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
		if running_pods:
			return False
		
		jobs = api_batch.list_job_for_all_namespaces()
		unsucceedful_jobs = [job.status.succeeded for job in jobs.items if job.status.succeeded != 1]
		if unsucceedful_jobs:
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


def run(hyperparameters, batch_repo, index, tick):
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
	
	'''
	config.load_kube_config(context=clusters['onprem'])
	onprem_api = client.AppsV1Api()

	config.load_kube_config(context=clusters['cloud'])
	cloud_api = client.AppsV1Api()
	'''
	#client.V1DaemonSet()
	'''
	if hp.gpu_workload:
		url = "https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml"
		r = requests.get(url)
		open('gpu_plugin.yaml', 'wb').write(r.content)
		gpu_support = yaml.safe_load('gpu_plugin.yaml')
		resp = onprem_api.create_namespaced_daemon_set(body=gpu_support, namespace="default") 
		resp = cloud_api.create_namespaced_daemon_set(body=gpu_support, namespace="default") 
	'''
	sched_tick = tick #0.1
	p0 = mp.Process(target=driver.custom_start, args=(None, c2, grpc_port, sched_tick, clusters['onprem'], clusters['cloud'], hp.waiting_policy, hp.wait_time, jobs, batch_repo, index))
	p0.start()
	
	clear_logs(clusters=clusters)
	while not empty_cluster(clusters=clusters):
		print("Cleaning Logs and Cluster....")
		time.sleep(1)
	clear_logs(clusters=clusters)
	
	tag = str(index)
	p1 = mp.Process(target=log, args=(tag, batch_repo, True, clusters['onprem'], clusters['cloud']))
	p2 = mp.Process(target=submit, args=(jobs, arrivals, batch_repo, index))
	p1.start()
	p2.start()

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
					curr_job = find_job_with_substring(job_list.items, "sleep-" + str(job))
					if curr_job.status.succeeded == 1:
						submitted_jobs[job] = True 
				except Exception as e:
					pass
		return submitted_jobs
	
	submitted_jobs = {}
	for job in jobs:
		if job == 'hyperparameters':
			continue
		submitted_jobs[job] = False

	# TODO: Keep a dictionary that continously gets updated with information about each generated job
	# TODO: Array
	while True: 
		logger.debug("Running ...")
		logger.debug("Submitted Jobs State: " + str(submitted_jobs))
		if all_submitted(submitted_jobs=submitted_jobs):
			logger.debug("Last job completed $$$")
			p1.terminate()
			p2.terminate()
			break 
		check_start = time.perf_counter()
		logger.debug("Checking State...")
		submitted_jobs = check_submitted(submitted_jobs=submitted_jobs)
		check_end = time.perf_counter()
		logger.debug("Check Time (seconds): " + str(check_end - check_start))
	'''
	# Keep running until last job is completed
	last_job = len(jobs) - 2
	while True:
		logger.debug("Running ...")
		if reached_last_job(job_name="sleep-" + str(last_job), clusters=clusters):
			logger.debug("Last job completed $$$")
			p1.terminate()
			p2.terminate()
			break 
	'''
	p1 = mp.Process(target=log, args=(tag, batch_repo, False, clusters['onprem'], clusters['cloud']))
	p1.start()
	while (p1.is_alive()):
		print("Saving last logs....")
		print("p1 alive status: " + str(p1.is_alive()))
		time.sleep(1)
	'''
	submitted_jobs = {}
	for job in jobs:
		if job == 'hyperparameters':
			continue
		submitted_jobs[job] = False
	
	while True: 
		# TODO: Ensure one complete set of logs are executed to completion
		logger.debug("Running ...")
		logger.debug("Submitted Jobs State: " + str(submitted_jobs))
		submitted_jobs = check_submitted(submitted_jobs=submitted_jobs)
		if all_submitted(submitted_jobs=submitted_jobs):
			logger.debug("Last job completed $$$")
			p1.terminate()
			break
	'''
		
	p0.terminate()
	
	return 0 

def run_sweep(sweep={}, sweep_timestamp=None):
	if not sweep_timestamp: 
		sweep_timestamp = str(int(datetime.now().timestamp()))
	else: 
		sweep_timestamp = str(sweep_timestamp)

	sweep_dir = "../logs/archive/" + sweep_timestamp + "/"
	if not os.path.exists(sweep_dir):
		os.mkdir(sweep_dir)
	sweep_path = sweep_dir + "sweep.json"

	with open(sweep_path, "w") as f:
		json.dump(sweep, f)

	for i in range(len(sweep) - 2):
		hp = sweep[i]
		tick = sweep['fixed_values']['sched_tick']
		run(hp, sweep_timestamp, str(i), tick)

	return sweep_timestamp

def submit_sweep(sweep=None, timestamp=None):
	fixed_values = OrderedDict(sweep['fixed_values'])
	varying_values = OrderedDict(sweep['varying_values'])
	sweep = generate_sweep(fixed_values=fixed_values, varying_values=varying_values)
	time_stamp = run_sweep(sweep=sweep, sweep_timestamp=timestamp)
	return time_stamp 

def generate_sweep(fixed_values=OrderedDict(), varying_values=OrderedDict()): 
	"""
	Takes specified fixed values and generates grid of hyperparameters based on varying values
	
	# TODO: Integrate hpo tool (e.g. optuna)
	# TODO: Specify grid search values, then plot them
	"""
	sweep = {}
	sweep["fixed_values"] = fixed_values
	sweep["varying_values"] = varying_values

	# DEFAULT VALUES
	hyperparameters = copy.deepcopy(DEFAULT_HYPERPARAMETERS)
	
	# FIXED VALUES
	for key, value in fixed_values.items(): 
		hyperparameters[key] = value

	# VARYING VALUES
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
	return sweep

def generate_interval(min=0, max=10, intervals=10):
	return np.linspace(min, max, num=intervals+1).tolist()

def create_cluster(cluster=None):
	"""
	TODO: Wait till GKE cluster finishes creating
	TODO: https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/projects.locations.clusters 
	"""
	client = container_v1.ClusterManagerClient() 
	operation = client.create_cluster(project_id=cluster['project_id'], zone=cluster['zone'], cluster=cluster['cluster'])

def delete_cluster(cluster=None):
	"""
	Wait until cluster finishes creating
	"""
	client = container_v1.ClusterManagerClient() 
	operation = client.delete_cluster(project_id=cluster['project_id'], zone=cluster['zone'], cluster_id=cluster['name'])

def main(arg1, arg2, arg3):
	"""
	Runs sweep of runs on starburst
	TODO: Integrate cluster creation and deletion code before and after call to submit_sweep()
	TODO: Create both onprem and cloud clusters before sweep
	"""
	sweep = sweeps.SWEEPS[arg2]
	cluster = {
		'name': "starburst_gpu",
		'network': 'skypilot-vpc',
		'initial_node_count': 1,
		'master_auth': {
			'username': "",
			'password': ""
		},
		'node_config': {
			'machine_type': 'n1-standard-96',
			'disk_size_gb': 100,
			'oauth_scopes': [
				'https://www.googleapis.com/auth/compute',
				'https://www.googleapis.com/auth/devstorage.read_write',
				'https://www.googleapis.com/auth/logging.write',
				'https://www.googleapis.com/auth/monitoring'
			],
			"accelerators": [
                {
                    "accelerator_count": 1,
                    "accelerator_type": "nvidia-tesla-v100"
                }
            ]
		},
	}

	cluster_config = {
		"cluster_name": "starburst_gpu",
		"project_id": 'sky-burst', 
		"zone": 'us-central1-c', 
		"cluster_prefix": 'parallel-exp',
		"cluster": cluster
	}

	# TODO:: Automate adding the gpu device plugin: kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml 
	
	

	if arg1 == 'run': 
		#create_cluster(cluster_config)
		submit_sweep(sweep=sweep, timestamp=arg3)
		#delete_cluster(cluster_config)

	return

if __name__ == '__main__':
    main(arg1=sys.argv[1], arg2=sys.argv[2], arg3=sys.argv[3])
	#pass

"""
UTIL + MISC FUNCTIONS
"""

def start_scheduler(policy="fifo_onprem_only", onprem_cluster="gke_sky-burst_us-central1-c_starburst", cloud_cluster="gke_sky-burst_us-central1-c_starburst-cloud"):
	os.system('python3 -m starburst.drivers.main_driver --policy {} --onprem_k8s_cluster_name {} --cloud_k8s_cluster_name {}'.format(policy, onprem_cluster, cloud_cluster))
	#subprocess.run(['python3', '-m', 'starburst.drivers.main_driver' '--policy', policy, '--onprem_k8s_cluster_name', onprem_cluster,'--cloud_k8s_cluster_name', cloud_cluster])
	return

def update_local_kube_config():
	"""
	Update the local kubeconfig with the values of the newly created cluster
	Use gcloud to update local kubeconfig values
	"""

def parallel_experiments(cluster_configs=None): #num_clusters=1, project_id='sky-burst', zone = 'us-central1-c', cluster_prefix='parallel-exp'):
	'''
	Creates cluster, submits job, deletes cluster
	#TODO: Finalize design and implement this codebase 
	#TODO: Don't create a new cluster if cluster already running
	#TODO: Create a GPU GKE cluster then delete it
	#TODO: Add created cluster name to local /.kube/config file to allow for automated authentication 
	'''	
	client = container_v1.ClusterManagerClient() 
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
