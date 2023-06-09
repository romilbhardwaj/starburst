import matplotlib.pyplot as plt
import math
from kubernetes import client, config
import datetime
import time
import json
import re
import copy
import os 
from collections import defaultdict
from collections import OrderedDict
import itertools
import starburst.utils.submit_jobs as submit_jobs
import pandas as pd
import subprocess
import numpy as np 

"""
# TODO: Integrate kubecost or GCP calculator
# TODO: Include accurate cloud specific costs (e.g. network, disk, instance type)
# TODO: Submit cloud quotas requests
"""

GCP_PRICES = {
	"e2-medium": 0.038795,
	"e2-standard-8": 0.31036,
	"unknown": 0.038795,
}

AWS_PRICES = {
	"vCPU": 0.05,
	"V100": 2.66,
	"K80": 0.7,
	"T4": 0.378
}

SCALED_COSTS = {
	"V100:vCPU": 53, #x
	"K80:vCPU": 14, #x
	"T4:vCPU": 7.5, #x
}

container_creation_times = {}
container_start_times = {}
image_pull_start_times = {}
image_pull_end_times = {}
scheduled_nodes = {}
job_creation_times = {}
job_completion_times = {}
job_pods = {}
node_instances = {}

event_data = {
	'container_creation_times': container_creation_times,
	'container_start_times': container_start_times,
	'image_pull_start_times': image_pull_start_times,
	'image_pull_end_times': image_pull_end_times,
	'scheduled_nodes': scheduled_nodes,
	'job_creation_times': job_creation_times,
	'job_completion_times': job_completion_times,
	'job_pods': job_pods, 
	'node_instances': node_instances
	#'job_to_pod': 
}

# Global event data - updated when functions executed
cluster_event_data = {
	'onprem': copy.deepcopy(event_data),
	'cloud': copy.deepcopy(event_data)
}

def event_data_dict():
	container_creation_times = {}
	container_start_times = {}
	image_pull_start_times = {}
	image_pull_end_times = {}
	#scheduled_times = {}
	scheduled_nodes = {}
	job_creation_times = {}
	job_completion_times = {}
	job_pods = {}
	node_instances = {}

	event_data = {
		'container_creation_times': container_creation_times,
		'container_start_times': container_start_times,
		'image_pull_start_times': image_pull_start_times,
		'image_pull_end_times': image_pull_end_times,
		#'scheduled_times': scheduled_times,
		'scheduled_nodes': scheduled_nodes,
		'job_creation_times': job_creation_times,
		'job_completion_times': job_completion_times,
		'job_pods': job_pods, 
		'node_instances': node_instances
	}

	cluster_event_data = {
		'onprem': copy.deepcopy(event_data),
		'cloud': copy.deepcopy(event_data)
	}
	return cluster_event_data


def parse_event_logs(cluster_event_data=None, submission_data=None, event_time=None, avoid_congestion=True):#onprem_event_logs = None, cloud_event_logs = None):
	'''
	Return values from parsed and joined logs (e.g. events, generated job data, and sweep values)

	# TODO: Plot cloud and onprem cluster jobs together
	# TODO: Note that event_job_id = job_data + 1
	# NOTE: Parse `kube_pod_info` --> if node name is not found, then pod not scheduled onto a node

	# TRACKING DIFFERENT TIMES: 
	# Job Start time, Pod Start Time, Pod Scheduled Time
	# Note: Pod only starts after pod has been scheduled ~ pod start == pod scheduled 
	
	# Delta 1:
	# Waiting Time: Scheduled Time - Job Start Time
	# Run Time: Job End Time - Scheduled Time

	# Delta 2: Pod End Time - Job End Time
	# Waiting Time: Scheduled Time - Pod Start Time
	# Run Time: Job End Time - Scheduled Time

	# AVOIDS CONGESTION
	# Delta 3: 
	# Runtime: Job End Time - Pod Start Time
	# Waiting Time: Pod Start Time - Job Submit Time 

	# Delta 4 
	# Runtime: Job End Time - Pod Start Time
	# Waiting Time: Pod Start Time - Job Scheduled Time  

	# MISC
	# SCHEDULER SUBMIT TIME IS TRUE ARRIVAL
	#NOTE: Scheduler_submit_time == Job submit time
	#TODO: Set job start times to pod start times
	#TODO: Set pod end times to job end times associated with the pod that started

	# Waiting Time: Pod Start Time (Arrival) - Job Submit Time (WITH CONGESTION)   
	# Waiting Time: Pod Start Time (Arrival) - Job Scheduled Time (AVOID CONGESTION)

	# TODO: Pass in a bool to look at JCT when assuming scheduled time vs. sumbission time
	# TODO: Determine if logs should be initialized to submission_time or arrival_time
	'''

	hyperparameters = None
	if 'hyperparamters' in submission_data: 
		hyperparameters = submission_data['hyperparameters']

	job_names = {}

	jobs = {'idx':[], 'runtime':[], 'arrival':[], 'num_gpus':[], 'allocated_gpus':[], 'start':[], 'instance_type':[], 'node_index': [], 'node': [], 'cpus': [], 'submission_time': [], 'wait_times':[]}

	all_nodes = set()
	nodes = {}
	node_id = 0

	onprem_event_logs = cluster_event_data['onprem']
	cloud_event_logs = cluster_event_data['cloud']
	clusters = {"onprem": onprem_event_logs, "cloud": cloud_event_logs}
	for type in clusters:
		cluster = clusters[type]
		if cluster is not None:
			
			start_times = cluster['container_start_times']
			#pod_end_times = cluster['pod_end_times']
			creation_times = cluster['job_creation_times']
			completion_times = cluster['job_completion_times']
			pod_nodes = cluster['scheduled_nodes']
			job_pods = cluster['job_pods']
			pod_jobs = {value: key for key, value in job_pods.items()}
			node_instances = cluster['node_instances']

			job_start_times = {}
			job_end_times = {}
			pod_start_times = {}

			for pod in start_times:
				pod_name = pod
				pod_start_time = start_times[pod]
				pod_start_times[pod_name] = pod_start_time
			
			min_arrival = math.inf

			for job in creation_times:
				job_name = job
				job_start_time = creation_times[job]
				job_start_times[job_name] = job_start_time
			
			for job in completion_times:
				job_name = job
				job_end_time = completion_times[job]
				job_end_times[job_name] = job_end_time

			for pod in pod_nodes:
				pod_name = pod
				all_nodes.add(pod_nodes[pod])

			job_times = {}
			for job in job_start_times:
				if job in job_end_times:
					job_times[job] = [job_start_times[job], job_end_times[job]]

			pod_times = {}
			for pod in pod_start_times:
				job = pod_jobs[pod]
				if job in job_end_times:
					#job_completion_times[job] = [job_start_times[job], job_end_times[job]]
					pod_times[job] = [pod_start_times[pod], job_end_times[job]]
			
			for n in all_nodes:
				nodes[n] = node_id
				node_id += 1

			intervals = pod_times 
			#intervals = job_times
			for i, (key, value) in enumerate(intervals.items()):
				job_id = re.findall(r'\d+', key)[0] #e.g. "sleep-26-100444"
				job_names[i] = key
				jobs['idx'].append(int(job_id))# - 1)#i)
				jobs['runtime'].append(value[1] - value[0])
				jobs['arrival'].append(value[0])
				jobs['num_gpus'].append(1)
				jobs['cpus'].append(submission_data[job_id]['workload']['cpu'])

				if avoid_congestion:
					submit_time = cluster['job_creation_times'][key] #Job start time
				else:
					submit_time = submission_data[job_id]['scheduler_submit_time'] #Job submission time

				jobs['submission_time'].append(submit_time)

				if not submit_time:
					jobs['wait_times'].append(0)
				else:
					jobs['wait_times'].append(value[0] - submit_time)

				if job_pods[key] in pod_nodes:
					jobs['allocated_gpus'].append({nodes[pod_nodes[job_pods[key]]]: []})
					jobs['node_index'].append(nodes[pod_nodes[job_pods[key]]])
				else:
					jobs['allocated_gpus'].append({})
					jobs['node_index'].append(None)
				
				if type == "cloud":
					jobs['start'].append(None)
				else:
					jobs['start'].append(value[0])
				
				if job_pods[key] in pod_nodes:
					jobs['node'].append(pod_nodes[job_pods[key]])
				else:
					jobs['node'].append("unknown")
				
				if job_pods[key] in pod_nodes:
					jobs['instance_type'].append(node_instances[pod_nodes[job_pods[key]]])
				else:
					jobs['instance_type'].append("unknown")
		
	if not jobs['arrival']:
		print("No job arrival times logged!")

	min_arrival = min(jobs['submission_time'])
	jobs['arrival'] = [i - min_arrival for i in jobs['arrival']]
	jobs['submission_time'] = [i - min_arrival for i in jobs['submission_time']]
	jobs['start'] = [i - min_arrival if i is not None else None for i in jobs['start']]
	jobs['arrival'] = np.array(jobs['arrival'])
	jobs['num_gpus'] =  np.array(jobs['num_gpus'])

	return jobs, len(all_nodes), hyperparameters

def retrieve_pod_data():
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	api = client.CoreV1Api()
	while True: 
		pod_list = api.list_namespaced_pod(namespace="default")
		print(pod_list)
		break
	return

def retrieve_node_instance(api):
	node_list = api.list_node().items
	instance_types = {}
	for node_data in node_list:
		node_name = node_data.metadata.name
		for label, value in node_data.metadata.labels.items(): 
			if label == "node.kubernetes.io/instance-type":
				instance_types[node_name] = value
				break 
	return instance_types

def retrieve_raw_events():
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	api = client.CoreV1Api()
	events = api.list_event_for_all_namespaces()
	text_file = open("../../local/artifacts/raw_logs.txt", "w")
	n = text_file.write(str(events))
	text_file.close()

def analyze_df(jobs_df):
	"""
	# TODO: Compute baseline cost and cost savings
	#cost, cost_density, system_utilization = compute_metrics(jobs=jobs, num_nodes=num_nodes)
	#metrics[i] = {"cost": cost, "cost_density": cost_density, "system_utilization": system_utilization, "hyperparameters": hyperparameters}
	"""
	return jobs_df

def retrieve_df(event_number=None, avoid_congestion=False):
	"""Turns all logs from sweep into a pandas dataframe for analysis"""
	all_jobs = {}
	if event_number:
		cluster_data_path = "../logs/archive/" + str(event_number) + '/events/'
		submission_data_path = "../logs/archive/" + str(event_number) + '/jobs/'
		sweep_data_path = "../logs/archive/" + str(event_number) + "/sweep.json"
		with open(sweep_data_path, "r") as f: #"../logs/event_data.json", "r") as f:
			sweep = json.load(f)

		files = os.listdir(cluster_data_path)

		for i in range(len(files)):
			#import pdb; pdb.set_trace()
			file = str(i) + ".json"
			cluster_log_path = cluster_data_path + file
			submission_log_path = submission_data_path + file

			try: 
				cluster_event_data = read_cluster_event_data(cluster_log_path=cluster_log_path)
				submission_data = read_submission_data(submission_log_path=submission_log_path)
				jobs, num_nodes, hps = parse_event_logs(cluster_event_data=cluster_event_data, submission_data=submission_data, avoid_congestion=avoid_congestion)
			except Exception as e:
				print(e)
				continue 
			
			hyperparameters = submission_data['hyperparameters']

			for k, v in hyperparameters.items(): 
				jobs[k] = v

			sweep_metrics = sweep[str(i)]
			jobs["varying_values"] = sweep["varying_values"].keys()
			jobs["fixed_values"] = sweep["fixed_values"].keys()

			for k, v in sweep_metrics.items(): 
				jobs[k + "_sweep"] = v
 			
			all_jobs[i] = jobs

	jobs_df = pd.DataFrame.from_dict(all_jobs)
	jobs_df = jobs_df.transpose()
	return jobs_df

def read_cluster_event_data(cluster_log_path=None):
	if not cluster_log_path: 
		cluster_log_path = "../logs/"
		files = os.listdir(cluster_log_path)

		for file in files:
			if file.endswith(".json"):
				cluster_log_path += str(file)
				break 

	with open(cluster_log_path, "r") as f:
		loaded_data = json.load(f)

	return loaded_data

def read_submission_data(submission_log_path=None):
	if submission_log_path: 
		with open(submission_log_path, "r") as f:
			loaded_data = json.load(f)
		return loaded_data
	return {}

def write_cluster_event_data(batch_repo=None, event_data=event_data, tag=None, loop=False):
	'''
	Store relevant event data in a dictionary to disk with periodic calls

	Examples:
	Type    Reason     Age   From               Message
	----    ------     ----  ----               -------
	Normal  Scheduled  52m   default-scheduler  Successfully assigned default/sleep-6-481852-sswbd to gke-starburst-default-pool-8bec73e3-81j8
	Normal  Pulling    52m   kubelet            Pulling image "alpine:latest"
	Normal  Pulled     52m   kubelet            Successfully pulled image "alpine:latest" in 118.522763ms
	Normal  Created    52m   kubelet            Created container sleep
	Normal  Started    52m   kubelet            Started container sleep

	# TODO: Write experiment metadata to job events metadata
	# TODO: Move existing logs to archive
	'''

	global cluster_event_data
	import logging
	#client.rest.logger.setLevel(logging.WARNING)
	logger = logging.getLogger(__name__)
	log_frequency = 1
	
	archive_path = "../logs/archive/"

	log_path = "../logs/"
	files = os.listdir(log_path)
	for file in files:
		if file.endswith(".json"):
			existing_log_path = str(file)
			os.rename(log_path + existing_log_path, archive_path + existing_log_path)

	if batch_repo: 
		log_path = log_path + "archive/" + batch_repo + "/"
		if not os.path.exists(log_path):
			os.mkdir(log_path)
		log_path += 'events/'
		if not os.path.exists(log_path):
			os.mkdir(log_path)
		print("Made directory for hyperparameter search...")
		current_log_path = log_path + tag + ".json"
	else: 
		if tag: 
			current_log_path = log_path + "event_data_" + tag + "_" + str(int(datetime.datetime.now().timestamp())) + ".json"
		else: 
			current_log_path = log_path + "event_data_" + str(int(datetime.datetime.now().timestamp())) + ".json"

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()

	if not loop: 
		while True: 
			try: 
				with open(current_log_path, 'r') as f:
					cluster_event_data = json.load(f)
			except Exception as e: 
				print(f"Caught an exception: {e}")
				print("Re-executing code...")
				continue
			else:
				print("Logs cleared successfully.")
				break

	while True:
		clusters = {"onprem": onprem_api, "cloud": cloud_api}
		for type in clusters:
			api = clusters[type]
			if api is not None:
				events = api.list_event_for_all_namespaces()
				event_data = cluster_event_data[type]

				# TODO: Determine what to do with message data - item.message
				instances = retrieve_node_instance(api)
				event_data['node_instances'] = instances
				
				for item in events.items:
					event_reason = item.reason
					#logger.debug("Event reason: ~~~ --- !!! " + str(event_reason))
					if event_reason == 'Pulling':
						involved_object = item.involved_object
						if involved_object.kind == 'Pod': 
							pod_name = involved_object.name 
							pull_start_time = item.first_timestamp 
							event_data['image_pull_start_times'][pod_name] = int(pull_start_time.timestamp())
					elif event_reason == 'Pulled':
						involved_object = item.involved_object 
						if involved_object.kind == 'Pod': 
							pod_name = involved_object.name 
							pull_end_time = item.first_timestamp 
							event_data['image_pull_end_times'][pod_name] = int(pull_end_time.timestamp())
					elif event_reason == 'Created':
						involved_object = item.involved_object 
						if involved_object.kind == 'Pod': 
							pod_name = involved_object.name 
							container_creation_time = item.first_timestamp 
							event_data['container_creation_times'][pod_name] = int(container_creation_time.timestamp())
					elif event_reason == 'Started':
						#TODO: Determine pod termination and deletion metrics
						#logger.debug("Event pod started: ~~~ --- !!! " + str(item))
						involved_object = item.involved_object 
						if involved_object.kind == 'Pod': 
							pod_name = involved_object.name 
							container_start_time = item.first_timestamp 
							event_data['container_start_times'][pod_name] = int(container_start_time.timestamp())
					elif event_reason == 'Scheduled':
						involved_object = item.involved_object 
						if involved_object.kind == 'Pod': 
							pod_name = involved_object.name 
							message = item.message
							match = re.search(r"Successfully assigned (\S+) to (\S+)", message) #e.g. "Successfully assigned default/sleep-1-541823-wkbz7 to gke-starburst-default-pool-8bec73e3-81j81"
							if match:
								_ = match.group(1)
								node_name = match.group(2)
								# TODO: Save pod scheduled time
								event_data['scheduled_nodes'][pod_name] = node_name
					elif event_reason == 'SuccessfulCreate':
						#TODO: Determine difference between job metrics and pod metrics
						involved_object = item.involved_object 
						if involved_object.kind == 'Job': 
							job_name = involved_object.name 
							message = item.message
							match = re.search(r"Created pod: (\S+)", message) # e.g. "Created pod: sleep-2-476460-zzz6h"
							if match:
								pod_name = match.group(1)
								event_data['job_pods'][job_name] = pod_name

							job_creation_time = item.first_timestamp 
							event_data['job_creation_times'][job_name] = int(job_creation_time.timestamp()) #[pod_name] = int(job_creation_time.timestamp())
					elif event_reason == 'Completed':
						#https://komodor.com/learn/exit-codes-in-containers-and-kubernetes-the-complete-guide/
						#TODO: Determine difference between job metrics and pod metrics
						involved_object = item.involved_object 
						if involved_object.kind == 'Job': 
							job_name = involved_object.name 
							job_completion_time = item.first_timestamp
							event_data['job_completion_times'][job_name] = int(job_completion_time.timestamp())

		# TODO: Save job hyperparameters directly into job events metadata	
		with open(current_log_path, "w") as f:
			json.dump(cluster_event_data, f)

		if not loop: 
			break 

		# Retrieve data each second 
		time.sleep(log_frequency)
	
	return 0

def log_parser(log_file, new_file, strings): 
	'''
	Parse only lines from a log file such that the selected lines contain a specific substring 
	'''
	import re

	parsed_logs = []
	with open('./' + log_file, 'r') as f:
		for line in f:
			if re.search(': ~~~ ', line):
				parsed_logs.append(line.strip())

	with open('./' + new_file, 'w') as f:
		for line in parsed_logs:
			f.write(line + '\n')

	return parsed_logs

"""Misc Utils"""

def pull_vm_scheduler_logs(event_number=0, force=True):
	'''
	Pulls log data running a GCP VM running in the cloud to your local computer to analyze data in evaluation.ipynb 
	#TODO: Generalize this function for different GKE clusters, acccounts, and filepaths
	#TODO: Set local python path
	'''
	gcp_path = 'suryaven@sky-scheduler:/home/suryaven/test/starburst/starburst/logs/archive/{}/'.format(event_number)
	local_path = '../logs/archive/'

	plot_dirs = ["../logs/", "../logs/archive/"]
	for plot_dir in plot_dirs:
		if not os.path.exists(plot_dir):
			os.mkdir(plot_dir)

	exists = os.path.isdir(local_path + str(event_number) + '/')
	if not exists or force: 
		subprocess.run(['gcloud', 'compute',  'scp', '--recurse', gcp_path, local_path, '--zone', 'us-central1-c',])


def plot_docker_pull_time(event_data=None):
	'''
	Outputs: 
	(1) Docker pull start time
	(2) Docker pull end time

	Design Requirements: 
	(1) Support multiple workloads
		(a) ML Workloads
		(b) Sleep Jobs 

	Possible Designs: 
	(1) Log docker pull time with fluentd then push to prometheus
	(2) Log docker pull time then return as exit value of pod, tracked by kube-state-metris
	(3) Log events from docker lifecycle hooks (e.g. Pulling, Pulled), then store and track them with kube-state-metrics
	(4) Create custom k8s event
	(x) Something else

	Possible Tools: 
	(1) Flamegraph 
	(2) FluentD
	(3) Openshift Logging: https://docs.openshift.com/container-platform/4.8/logging/cluster-logging-eventrouter.html
	(4) Kubewatch: https://www.cncf.io/blog/2021/12/21/extracting-value-from-the-kubernetes-events-feed/
	(5) Event: https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/
	(6) Grafana Agent: https://www.cncf.io/blog/2023/03/13/how-to-use-kubernetes-events-for-effective-alerting-and-monitoring/ 
	(x) Something else

	# TODO: Store docker pull time
	'''
	image_pull_times = []
	if event_data: 
		clusters = {"onprem": event_data['onprem'], "cloud": event_data['cloud']}
	for type in clusters: 
		cluster = clusters[type]
		if cluster is not None: 
			# TODO: Plot all pods running on the same node together
			'''
			Parse `kube_pod_info` --> if node name is not found, then pod not scheduled onto a node
			'''
			image_pull_start_times = cluster['image_pull_start_times']
			image_pull_end_times = cluster['image_pull_end_times']
			#print(image_pull_start_times)
			#print(image_pull_end_times)
			
			for pod in image_pull_start_times: 
				image_pull_time = image_pull_end_times[pod] - image_pull_start_times[pod]
				image_pull_times.append(image_pull_time)
	
	fig, ax = plt.subplots()
	ax.hist(image_pull_times, bins=5)

	plt.xlabel('Image Pull Time (Seconds)')
	plt.ylabel('Frequency')
	
	plt.show()

	return image_pull_times