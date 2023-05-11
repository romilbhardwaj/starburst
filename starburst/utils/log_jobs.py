from prometheus_api_client import PrometheusConnect
import matplotlib.pyplot as plt
import plot_jobs #read_trace
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
#import ..skyburst



# TODO: Integrate kubecost or GCP calculator
# TODO: Include accurate cloud specific costs (e.g. network, disk, instance type)
# TODO: Submit cloud quotas requests

# TODO: Change unkown value from default cost of e2-standard-8 to better value
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

# Connect to Prometheus
onprem = PrometheusConnect(url="http://34.67.143.10:30000/", disable_ssl=True)
cloud = PrometheusConnect(url="http://34.28.53.85:30000/", disable_ssl=True)

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

def plot_docker_pull_time(event_data=None):
	# TODO: Store docker pull time
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

def plot_instance_run_time():
	# TODO: 
	return 0 

def plot_job_index():
	# TODO: Add pod logs for cpu_index
	'''
	- K8s uses fractional CPU and has fine-grain control with 100ms refresh rate [ROMIL]
	'''

	# TODO: Add pod logs for gpu_index
	'''
	- K8s assigns GPU without fine-grain control [ROMIL]
	'''

	# TODO: Add pod logs for thread_index
	'''
	Design 1: 
	- Use bash command to send values to fluentd logs

	Design 2: 
	- Use k8s api to determine which cpu and thread a pod is running on 
	'''
	return 

def average_waiting_time():
	# TODO: Store waiting times from scheduler
	return 0

def average_job_running_time(jobs):
	# TODO: Compute average of all job runtimes
	runtimes = jobs['runtime']
	fig, ax = plt.subplots()
	ax.hist(runtimes, bins=5)
	plt.xlabel('Job Runtime')
	plt.ylabel('Frequency')
	plt.show()
	return sum(runtimes)/len(runtimes)

def average_jct():
	return average_job_running_time() + average_waiting_time()

#total_job_volume = 1155998.77277777
#job_makespan = 2559.3205555555555
#diff_df['norm_system_utilization'] = total_job_volume/(job_makespan*diff_df['cluster_size']*sim_df['gpus_per_node'].iloc[0])
#x_axis = 'norm_system_utilization'

def plot_job_intervals(jobs, num_nodes, save=False, path=None, subplt=None, plt_index=None, tag=None, scale=1, plot_sweep=False, dim=(-100, 100, 0, 100), ratio=(1, 1), gpus_per_node=8):
	axs = plot_jobs.plot_trace_spacetime_and_spillover(jobs, num_nodes, save=save, path=path, subplt=subplt, plt_index=plt_index, tag=tag, scale=scale, plot_sweep=False, dim=dim, ratio=ratio, gpus_per_node=gpus_per_node)
	return axs

def parse_prometheus_logs(onprem=onprem, cloud=cloud):
	# TODO: Plot cloud and onprem cluster jobs together
	job_names = {}
	jobs = {'idx':[], 'runtime':[], 'arrival':[], 'num_gpus':[], 'allocated_gpus':[], 'start':[]}

	all_nodes = set()
	nodes = {}
	node_id = 0

	clusters = {"onprem": onprem, "cloud": cloud}
	for type in clusters: 
		cluster = clusters[type]
		if cluster is not None: 
			# TODO: Plot all pods running on the same node together
			'''
			Parse `kube_pod_info` --> if node name is not found, then pod not scheduled onto a node
			'''

			start_times = cluster.get_current_metric_value('kube_pod_start_time')
			end_times = cluster.get_current_metric_value('kube_pod_completion_time')
			pod_info = cluster.get_current_metric_value('kube_pod_info')
			#print(end_times)

			pod_start_times = {}
			pod_end_times = {}
			pod_nodes = {}
			
			min_arrival = math.inf
			# Get start times
			for pod in start_times: 
				pod_name = pod['metric']['pod']
				pod_start_time = int(pod['value'][1])
				#min_arrival = min(min_arrival, pod_start_time)
				pod_start_times[pod_name] = pod_start_time
			
			#print(pod_start_times.values())
			#print(min_arrival)
				

			#for pod in pod_start_times: 
			#	pod_start_times[pod] -= min_arrival
			
			#print(pod_start_times.values())

			for pod in end_times: 
				pod_name = pod['metric']['pod']
				pod_end_time = int(pod['value'][1])
				pod_end_times[pod_name] = pod_end_time
			
			#for pod in pod_end_times: 
			#	pod_end_times[pod] -= min_arrival

			for pod in pod_info: 
				pod_name = pod['metric']['pod']
				if pod_name in pod_start_times: 
					pod_node = pod['metric']['node']
					all_nodes.add(pod_node)
					pod_nodes[pod_name] = pod_node

			pod_completion_times = {}
			for pod in pod_start_times:
				if pod in pod_end_times:
					#print(pod)
					#min_arrival = min(min_arrival, pod_start_times[pod])
					pod_completion_times[pod] = [pod_start_times[pod], pod_end_times[pod]]
			#print(pod_completion_times)
			'''
			for pod in pod_completion_times: 
				value = pod_completion_times[pod]
				pod_completion_times[pod] = [value[0] - min_arrival, value[1] - min_arrival]
			'''

			intervals = pod_completion_times
			#fig, ax = plt.subplots()

			'''
			for i, (key, value) in enumerate(intervals.items()):
				#value = intervals[key]
				#print(str(value[1]-value[0]) + " " + str(value[0]))
				ax.barh(i, width=(value[1]-value[0]), left=value[0], height=0.5, label=key)
			'''

			# Job Trace Format
			for n in all_nodes: 
				#nodes[node_id] = n
				nodes[n] = node_id
				node_id += 1

			#job_names = {}
			#jobs = {'idx':[], 'runtime':[], 'arrival':[], 'num_gpus':[], 'allocated_gpus':[], 'start':[]}
			print(all_nodes)
			print(nodes)
			for i, (key, value) in enumerate(intervals.items()):
				job_names[i] = key
				jobs['idx'].append(i)
				jobs['runtime'].append(value[1] - value[0])
				jobs['arrival'].append(value[0])
				jobs['num_gpus'].append(1)
				jobs['allocated_gpus'].append({nodes[pod_nodes[key]]: [1]})
				if type == "cloud":
					jobs['start'].append(None)
				else: 
					jobs['start'].append(value[0])
			
			'''
			node_values = {}
			for i, (key, value) in enumerate(intervals.items()):
				curr_node = pod_nodes[key]
				if curr_node not in node_values: 
					node_values[curr_node] = {"width":[], "left": [], "label": []}
				node_values[curr_node]["width"].append(value[1] - value[0])
				node_values[curr_node]["left"].append(value[0])
				node_values[curr_node]["label"].append(key)
			
			for node in node_values: 
				#ax.barh(node, width=node_values[node]["width"], left=node_values[node]["left"], height=0.5, label=node_values[node]["label"])
				ax.barh(node_values[node]["label"], width=node_values[node]["width"], left=node_values[node]["left"], height=0.5, label=node_values[node]["label"])

			# Node Graph
			ax.set_yticks(range(len(all_nodes)))
			ax.set_yticklabels(list(all_nodes))
			ax.invert_yaxis()
			ax.set_xlabel('Time')
			ax.set_ylabel('Node Name')
			'''

			'''
			# Pod Graph
			ax.set_yticks(range(len(intervals)))
			ax.set_yticklabels(list(intervals.keys()))
			ax.invert_yaxis()
			ax.set_xlabel('Time')
			ax.set_ylabel('Interval Name')
			'''
			
			#plt.show()
			#plt.savefig('../plots/job_intervals.png')
		
	min_arrival = min(jobs['arrival'])
	jobs['arrival'] = [i - min_arrival for i in jobs['arrival']]
	jobs['start'] = [i - min_arrival if i is not None else None for i in jobs['start']]
	return jobs, len(all_nodes)

def parse_event_logs(cluster_event_data=None, submission_data=None, event_time=None, avoid_congestion=True):#onprem_event_logs = None, cloud_event_logs = None):
	# TODO: Plot cloud and onprem cluster jobs together
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

	#clusters = {"onprem": onprem, "cloud": cloud}
	clusters = {"onprem": onprem_event_logs, "cloud": cloud_event_logs}
	for type in clusters:
		cluster = clusters[type]
		if cluster is not None:
			# TODO: Plot all pods running on the same node together
			'''
			Parse `kube_pod_info` --> if node name is not found, then pod not scheduled onto a node
			'''
			start_times = cluster['container_start_times']
			#pod_end_times = cluster['pod_end_times']
			creation_times = cluster['job_creation_times']
			completion_times = cluster['job_completion_times']
			pod_nodes = cluster['scheduled_nodes']
			job_pods = cluster['job_pods']
			pod_jobs = {value: key for key, value in job_pods.items()}

			node_instances = cluster['node_instances']
			print("START TIMES " + str(creation_times))

			job_start_times = {}
			job_end_times = {}
			pod_start_times = {}

			for pod in start_times:
				pod_name = pod
				pod_start_time = start_times[pod]
				pod_start_times[pod_name] = pod_start_time
			
			min_arrival = math.inf

			# Get start times
			for job in creation_times:
				job_name = job #pod['metric']['pod']
				job_start_time = creation_times[job] #int(pod['value'][1])
				job_start_times[job_name] = job_start_time
				#pod_start_times[job] = job
			
			for job in completion_times:
				job_name = job #pod['metric']['pod']
				job_end_time = completion_times[job] #int(pod['value'][1])
				job_end_times[job_name] = job_end_time

			for pod in pod_nodes:
				pod_name = pod #pod['metric']['pod']
				all_nodes.add(pod_nodes[pod])
				'''
				if pod_name in pod_start_times:
					pod_node = pod['metric']['node']
					all_nodes.add(pod_node)
					pod_nodes[pod_name] = pod_node
				'''

			# TODO: Set start times to pod start times
			# TODO: Set end times to job end times associated with the pod that started
			#job_completion_times = {}
			#for job in job_start_times:
			job_times = {}
			for job in job_start_times:
				if job in job_end_times:
					#job_completion_times[job] = [job_start_times[job], job_end_times[job]]
					job_times[job] = [job_start_times[job], job_end_times[job]]

			print("JOB START, JOB END -- TIMES")
			print(job_times)

			#scheduled_times = {}
			pod_times = {}
			for pod in pod_start_times:
				# TODO: Create pod
				job = pod_jobs[pod]
				if job in job_end_times:
					#job_completion_times[job] = [job_start_times[job], job_end_times[job]]
					pod_times[job] = [pod_start_times[pod], job_end_times[job]]
			
			print("POD START, JOB END -- TIMES")
			print(pod_times)
			#intervals = job_completion_times
			
			# TODO: Pass in a bool to look at JCT when assuming scheduled time vs. sumbission time
			#if avoid_congestion:
			#	intervals = job_times
			#else:
			#	intervals = pod_times #scheduled_times
			#intervals = pod_times
			#intervals = job_times
			intervals = pod_times 
			
			# TRACKING DIFFERENT TIMES: 
			# Job Start time, Pod Start Time, Pod Scheduled Time
			# Note: Pod only starts after pod has been scheduled ~ pod start == pod scheduled 
			
			# Delta 1:
			# Waiting Time: Scheduled Time - Job Start Time
			# Run Time: Job End Time - Scheduled Time

			# Delta 2: Pod End Time - Job End Time
			# Waiting Time: Scheduled Time - Pod Start Time
			# Run Time: Job End Time - Scheduled Time
			#intervals = job_times

			# Job Trace Format
			for n in all_nodes:
				nodes[n] = node_id
				node_id += 1

			#print(all_nodes)
			#print(pod_nodes)
			#print(nodes)
			#print(len(intervals))
			#print(intervals)
			#print(len(submission_data))
			for i, (key, value) in enumerate(intervals.items()):
				#print(len(intervals))
				#print("index " + str(i))
				#print(key)
				
				#job_id
				#s = "sleep-26-100444"
				# TODO: Note that event_job_id = job_data + 1
				job_id = re.findall(r'\d+', key)[0]
				#print("job_id" + str(job_id))
				# sleep-26-100444 - format
				job_names[i] = key
				jobs['idx'].append(int(job_id) - 1)#i)
				jobs['runtime'].append(value[1] - value[0])
				jobs['arrival'].append(value[0])
				jobs['num_gpus'].append(1)

				#if i >= len(submission_data) - 2:
				#	print("reached")
				#	break

				#if job_id in submission_data:
				jobs['cpus'].append(submission_data[job_id]['workload']['cpu'])

				# TODO: Implement Delta 3 and Delta 4

				# Delta 3: 
				# Runtime: Job End Time - Pod Start Time
				# Waiting Time: Pod Start Time - Job Submit Time 

				# Delta 4 
				# Runtime: Job End Time - Pod Start Time
				# Waiting Time: Pod Start Time - Job Scheduled Time  

				# JCT = Wait Time + Run Time 
				#import pdb; pdb.set_trace()

				# Waiting Time: Pod Start Time (Arrival) - Job Submit Time (WITH CONGESTION)   
				# Waiting Time: Pod Start Time (Arrival) - Job Scheduled Time (AVOID CONGESTION)
				#import pdb; pdb.set_trace()
				if avoid_congestion:
					#intervals = job_times
					#submit_time = submission_data[job_id]['scheduler_submit_time']
					#job_int = int(job_id)
					
					submit_time = cluster['job_creation_times'][key] # JOB START TIME
					
					#job_val = job_pods[key] 
					#submit_time = cluster['container_start_times'][job_val] # POD START TIME

					#cluster['job_creation_times'][job_id]
					#cluster['container_start_times'][job_pods[key]]
				else:
					#intervals = pod_times 
					# Set job submit time
					submit_time = submission_data[job_id]['scheduler_submit_time'] # JOB SUBMISSION TIME

					# SCHEDULER SUBMIT TIME IS TRUE ARRIVAL
					#NOTE: Scheduler_submit_time == Job submit time

				#submit_time = submission_data[job_id]['scheduler_submit_time']
				#if submit_time:
				jobs['submission_time'].append(submit_time)
				#submission_data[job_id]['scheduler_submit_time'])

				if not submit_time:
					jobs['wait_times'].append(0)
				else:
					#jobs['wait_time'].append(value[0] - submit_time)
					#import pdb; pdb.set_trace()
					#jobs['wait_times'].append(submit_time - value[0])
					jobs['wait_times'].append(value[0] - submit_time)

					#jobs['wait_time'].append(0)
				#import pdb; pdb.set_trace()

				#if key in job_pods:
				if job_pods[key] in pod_nodes:
					#jobs['allocated_gpus'].append({nodes[pod_nodes[job_pods[key]]]: [1]})
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
		#print(jobs['wait_time'])
		#import pdb; pdb.set_trace()
		
	# TODO: Determine if logs should be initialized to submission_time or arrival_time
	#print(jobs['arrival'])

	if not jobs['arrival']:
		print("No job arrival times logged!")

	#print(jobs)
	#min_arrival = min(jobs['arrival']) #min(jobs['submission_time']) #min(jobs['arrival'])
	#print(jobs['arrival'])
	#print(jobs['submission_time'])
	#print(jobs['wait_time'])
	#time.sleep(10000)

	#Normalize times based on minimum submission time 
	min_arrival = min(jobs['submission_time']) #min(jobs['arrival'])
	jobs['arrival'] = [i - min_arrival for i in jobs['arrival']]
	jobs['submission_time'] = [i - min_arrival for i in jobs['submission_time']]
	jobs['start'] = [i - min_arrival if i is not None else None for i in jobs['start']]


	#jobs = {'idx':[], 'runtime':[], 'arrival':[], 'num_gpus':[], 'allocated_gpus':[], 'start':[], 'instance_type':[], 'node_index': [], 'node': [], 'cpus': [], 'submission_time': [], 'wait_time':[]}

	jobs['arrival'] = np.array(jobs['arrival'])
	jobs['num_gpus'] =  np.array(jobs['num_gpus'])
	#'cluster_size'
    #'gpus_per_node'

	#print("NODE NAMES: ")
	#print(all_nodes)
	#print(len(all_nodes))
	
	return jobs, len(all_nodes), hyperparameters

def increase_ttl():
	# TODO: Determine feasible design before implementation
	'''
	Outputs: 
	(1) Nothing

	Design Requirements: 
	(1) Increase eventTTL value for any k8s cluster
		(a) Support GKE clusters

	Possible Designs: 
	(1) Use k8s python client to modify cluster's eventTTL value
	(x) Something else

	Possible Tools: 
	(1) kube-apiserver -> configures api objects (e.g pods, services)
	(x) Something else
	'''
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	api = client.CoreV1Api()
	api_instance = client.ApiregistrationV1Api()
	resource_name = 'v1'
	group_name = ''
	api_version = 'v1'
	api_response = api_instance.get_api_resources()#group=group_name, version=api_version, name=resource_name)
	print(api_response)
	#return
	configuration = api_response.to_dict()['schema']['openAPIV3Schema']['properties']['spec']['properties']['containers']['items'][0]['properties']['args']['items'][0]['properties']

	# Modify the eventTTL field
	configuration['value']['items'].append('--event-ttl=1h')

	# Update the kube-apiserver with the modified configuration
	api_instance.patch_api_service(name='v1', body={'spec': {'containers': [{'args': configuration['value']['items']}]}})
	return 

def retrieve_pod_data():
	# Load the Kubernetes configuration from the default location
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")

	# Create a Kubernetes API client
	api = client.CoreV1Api()

	# Get a list of all pods in the default namespace
	while True: 
		pod_list = api.list_namespaced_pod(namespace="default")
		print(pod_list)
		break
	return

def retrieve_node_instance(api):
	#config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	#api = client.CoreV1Api()
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


def view_real_arrival_times(event_number=None, scale=1, plot_sweep=False, get_data=False, dim=(-100, 100, 0, 100), ratio=(1, 1), gpus_per_node=8, avoid_congestion=True):#cluster_data_path=None, submission_data_path=None):
	costs = {}
	if event_number: #cluster_data_path and submission_data_path: 
		cluster_data_path = "../logs/archive/" + str(event_number) + "/events/"
		submission_data_path = "../logs/archive/" + str(event_number) + "/jobs/"
		sweep_data_path = "../logs/archive/" + str(event_number) + '/sweep.json'
		sweep_data = read_submission_data(submission_log_path=sweep_data_path)

		files = os.listdir(cluster_data_path)
		num_graphs = len(files) #-2#+ 1 #2
		#fig, axs = plt.subplots(nrows=num_graphs, ncols=1, figsize=(5*scale, 30*scale))
		fig, axs = plt.subplots(nrows=num_graphs, ncols=1, figsize=(ratio[0]*scale, ratio[1]*scale))
		#fig, axs = plt.subplots(nrows=2, ncols=1)
		# Iterate over the files and check if they have the ".json" extension
		#for file in files:
		file_count = 0 
		for i in range(len(files)):
			file = files[i]
			#print("FILE NAME " + file)
			cluster_log_path = cluster_data_path + file
			submission_log_path = submission_data_path + file

			'''
			# TODO: Skip the plot if a specific file cannot be found
			#if cluster_log_path not in 
			cluster_log_path_file = cluster_log_path + ".json"
			submission_data_path_file = submission_data_path + ".json"
			
			print("CHECKING FILES: " + cluster_log_path_file + " " + submission_data_path_file)
			if not os.path.isfile(cluster_log_path_file):
				continue

			if not os.path.isfile(submission_data_path_file):
				continue
			'''

			#print("CLUSTER LOG PATH")
			#print(cluster_log_path)
			try:
				cluster_event_data = read_cluster_event_data(cluster_log_path=cluster_log_path)
				submission_data = read_submission_data(submission_log_path=submission_log_path)
				jobs, num_nodes, hps = parse_event_logs(cluster_event_data=cluster_event_data, submission_data=submission_data, event_time=event_number, avoid_congestion=avoid_congestion)#time_stamp=event_number)
			except Exception as e:
				print(e)
				continue 	
		
			events = cluster_event_data
			submissions = submission_data
			if get_data: 
				return jobs, events, submissions

			#cost = job_logs.cloud_cost(jobs=jobs, num_nodes=num_nodes)
			#costs[file] = cost
			plot_dir = "../logs/archive/plots/"
			if not os.path.exists(plot_dir):
				#os.mkdir(archive_path)
				os.mkdir(plot_dir)

			plot_path = "../logs/archive/plots/" + file[:-5] + ".png"
			#print(plot_path)
		
			#if plot_sweep:
			#"wait " + str(jobs_wait['wait_time'][i]) +  " arr " + str(jobs_wait['arrival_rate'][i] 
			'''
			{"hyperparameters": {"waiting_policy": "fifo_wait", "time_constrained": true, "cluster_size": 4, "cpus_per_node": 8, "cloud_cluster_nodes": 4, "cloud_cpu_per_node": 8, "random_seed": 0, "total_jobs": 100, "batch_time": 2, "wait_time": 0.0, "time_out": 5, "mean_duration": 10, "arrival_rate": 0.016666666666666666, "cpu_sizes": [1, 2, 4], "cpu_dist": [0, 0.5, 0.5], "gpu_sizes": [1, 2, 4, 8, 16, 32], "gpu_dist": [0, 0.2, 0.2, 0.2, 0.2, 0.2], "memory_sizes": [100, 500, 1000, 50000], "memory_dict": [0.25, 0.25, 0.25, 0.25]},
			'''
			tag = str(file)
			tag = ""
			varying_values = sweep_data['varying_values'] #varying_values
			for value in varying_values: 
				tag += str(submission_data['hyperparameters'][value])
				tag += " | "
			#for 

			axs = plot_job_intervals(jobs, num_nodes, save=True, path=plot_path, subplt=axs, plt_index=i, tag=tag, scale=scale, plot_sweep=plot_sweep, dim=dim, ratio=ratio, gpus_per_node=gpus_per_node)
			#else:
			#	plot_job_intervals(jobs, num_nodes, save=False, path=plot_path, subplt=axs, plt_index=i, tag=str(file), scale=scale, plot_sweep=plot_sweep)
	
			#job_logs.plot_job_intervals(jobs, num_nodes)
			
			#if file.endswith(".json"):
			#	log_path = log_path + str(file)
			#	break 
			
			file_count += 1
			if file_count >= num_graphs: 
				break 
			
	#return costs
	#plt.tight_layout()
	plt.show()

	return 

def analyze_df(jobs_df):
	# TODO: Compute baseline cost and cost savings
	#cost, cost_density, system_utilization = compute_metrics(jobs=jobs, num_nodes=num_nodes)
	#metrics[i] = {"cost": cost, "cost_density": cost_density, "system_utilization": system_utilization, "hyperparameters": hyperparameters}
	return jobs_df

def retrieve_df(event_number=None, graph=False, avoid_congestion=False):
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
			file = str(i) + ".json"
			cluster_log_path = cluster_data_path + file
			submission_log_path = submission_data_path + file

			try: 
				cluster_event_data = read_cluster_event_data(cluster_log_path=cluster_log_path)
				submission_data = read_submission_data(submission_log_path=submission_log_path)
				jobs, num_nodes, hps = parse_event_logs(cluster_event_data=cluster_event_data, submission_data=submission_data, avoid_congestion=avoid_congestion)
			except Exception as e:
				continue 
			
			hyperparameters = submission_data['hyperparameters']

			for k, v in hyperparameters.items(): 
				jobs[k] = v

			sweep_metrics = sweep[str(i)]
			for k, v in sweep_metrics.items(): 
				jobs[k + "_sweep"] = v
 			
			all_jobs[i] = jobs

	jobs_df = pd.DataFrame.from_dict(all_jobs)
	jobs_df = jobs_df.transpose()
	return jobs_df

def analyze_sweep(event_number=None, graph=False, avoid_congestion=False):#, fixed_values=OrderedDict(), varying_values=OrderedDict()):#path=None):
	"""Takes each batch job file and computes values (e.g. cloud cost, system utilization)"""

	metrics = {}
	all_jobs = {}
	if event_number:
		cluster_data_path = "../logs/archive/" + str(event_number) + '/events/'
		submission_data_path = "../logs/archive/" + str(event_number) + '/jobs/'
		sweep_data_path = "../logs/archive/" + str(event_number) + "/sweep.json"
		with open(sweep_data_path, "r") as f: #"../logs/event_data.json", "r") as f:
			sweep = json.load(f)

		#exempt_files = []
		files = os.listdir(cluster_data_path)
		#files = sorted(files)

		# Iterate over the files and check if they have the ".json" extension
		for i in range(len(files)):
			file = str(i) + ".json" #files[i]
			print("FILENAME: " + file)
			#cluster_log_path = cluster_data_path + file
			#submission_log_path = submission_data_path + file

			# TODO: Skip the plot if a specific file cannot be found
			#if cluster_log_path not in 
			'''
			cluster_log_path_file = cluster_data_path + file
			submission_data_path_file = submission_data_path + file
			
			print("CHECKING FILES: " + cluster_log_path_file + " " + submission_data_path_file)
			if not os.path.isfile(cluster_log_path_file):
				continue

			if not os.path.isfile(submission_data_path_file):
				continue
			'''

			cluster_log_path = cluster_data_path + file
			submission_log_path = submission_data_path + file

			print(cluster_log_path)
			try: 
				cluster_event_data = read_cluster_event_data(cluster_log_path=cluster_log_path)
				submission_data = read_submission_data(submission_log_path=submission_log_path)
				jobs, num_nodes, hps = parse_event_logs(cluster_event_data=cluster_event_data, submission_data=submission_data, avoid_congestion=avoid_congestion)
			except Exception as e:
				continue 
			

			# TODO: Compute baseline cost and cost savings
			#cost, cost_density, system_utilization = compute_metrics(jobs=jobs, num_nodes=num_nodes)
			#metrics[i] = {"cost": cost, "cost_density": cost_density, "system_utilization": system_utilization, "hyperparameters": hyperparameters}
			
			hyperparameters = submission_data['hyperparameters']
			job_metrics = compute_metrics(jobs=jobs, num_nodes=num_nodes)
			#job_metrics["hyperparameters"] = hyperparameters

			for k, v in hyperparameters.items(): 
				job_metrics[k] = v
				jobs[k] = v

			#jobs[]

			sweep_metrics = sweep[str(i)]
			for k, v in sweep_metrics.items(): 
				job_metrics[k] = v
				
			for k, v in job_metrics.items(): 
				if k == 'cloud_cost':
					jobs['total_cloud_cost'] = v
				elif k == 'avg_jct': 
					jobs[k] = v
		
			metrics[i] = job_metrics
			all_jobs[i] = jobs
			
			#if file.endswith(".json"):
			#	log_path = log_path + str(file)
			#	break 

	#print(metrics)
	#time.sleep(1000)
	fixed_values = OrderedDict(sweep['fixed_values'])
	varying_values = OrderedDict(sweep['varying_values'])
	print(fixed_values)
	print(varying_values)

	if graph: 
		graph_metrics(metrics=metrics, fixed_values=fixed_values, varying_values=varying_values)

	return metrics, all_jobs

def compute_metrics(jobs, num_nodes):
	# TODO: Compute steady state value i.e. remove cloud cost from first X and last X jobs
	# TODO: Compute total value i.e. beg to end simulation cost --> compute start and end time for each node
	# TODO: Only consider jobs with start=None, because they are run on the cloud
	'''
	arrivals = jobs['arrival']
	runtimes = jobs['runtime']
	terminations = arrivals + runtimes
	start_time = min(arrivals)
	end_time = max(terminations)
	total_time = end_time - start_time
	cost = AWS_PRICES['vCPU'] * total_time/60
	'''

	cloud_cost = 0 
	onprem_cost = 0 
	instance_types = jobs['instance_type']
	runtimes = jobs['runtime']
	submission_times = jobs['submission_time']
	wait_times = jobs['wait_times']
	start = jobs['start']

	# NOTE: Job runtime has integer precisions due to granularity of kuberentes event logs
	print(runtimes)
	print(wait_times)
	print(submission_times)

	#time.sleep(1000)
	max_arrival = max(jobs['arrival'])
	min_arrival = min(jobs['arrival'])
	total_time = 0 
	cloud_time = 0 
	onprem_time = 0
	# TODO: Compute JCT = Waitime + Runtime
	job_completion_times = [runtimes[i] + wait_times[i] for i in range(len(runtimes))]
	jct = sum(job_completion_times)/len(job_completion_times)
	'''
	result_dict['stats']['avg_jct'] = (total_waiting_time + total_running_time) / num_jobs
	'''
	print(instance_types)
	#time.sleep(100)
	for i in range(len(runtimes)):
		print(start[i])
		runtime = runtimes[i] / (60 * 60)
		#total_time += runtime
		print(i)
		print(instance_types[i])
		instance_type = instance_types[i]
		instance_cost_per_hour = GCP_PRICES[instance_type]
		total_time += runtimes[i]
		if start[i] == None: 
			cloud_cost += runtime * instance_cost_per_hour
			cloud_time += runtime 
		else: 
			onprem_cost += runtime * instance_cost_per_hour
			onprem_time += runtime

	# TODO: Ensure accurate system utilization values		
	job_makespan = (4 * 8 * (max_arrival - min_arrival)) # 4 nodes per cluster w/ 8 CPU's each
	total_job_volume = total_time
	norm_system_utilization = job_makespan/total_job_volume

	# TODO: Compute the accurate values
	# Sum_local_space = onprem make span
	# Sum_cloud_space = cloud make span 

	cluster_size = 4
	gpus_per_node = 8 
	end_time = max_arrival
	start_time = min_arrival

	# TODO: Change the on

	sum_local_space = onprem_time
	sum_cloud_space = cloud_time
	cluster_utilization = sum_local_space / (cluster_size * gpus_per_node * (end_time - start_time))
	system_utilization = (sum_local_space + sum_cloud_space) / (cluster_size * gpus_per_node * (end_time - start_time))

	'''
	result_dict['stats']['cluster_utilization'] = sum_local_space / (
        simulator_spec['cluster_size'] * simulator_spec['gpus_per_node'] *
        (end_time - start_time))
    result_dict['stats']['system_utilization'] = (
        sum_local_space + sum_cloud_space) / (simulator_spec['cluster_size'] *
                                              simulator_spec['gpus_per_node'] *
                                              (end_time - start_time))
	'''
	
	
	metrics = {
		"runtime": sum_cloud_space + sum_local_space,
		"cloud_cost": cloud_cost,
		"onprem_cost": onprem_cost,
		"system_utilization": system_utilization,
		"cluster_utilization": cluster_utilization,
		"norm_system_utilization": norm_system_utilization,
		#'job_completion_time': jct
		'avg_jct': jct
	}



	#return (cloud_cost, onprem_cost), (cloud_cost/total_time, onprem_cost/total_time), norm_system_utilization
	return metrics

label_dict = {
    'avg_jct': 'Avg. JCT (hr)',
    'cost_mult': '% Cost Savings\nover No Wait',
    'cost_diff': 'Cost Savings\nover No Wait',
    'cluster_size': 'Cluster Size (# Nodes)',
    'norm_system_utilization': 'System Utilization',
    'system_utilization': 'System Utilization',
    'cluster_utilization': 'Cluster Utilization',
    'total_cloud_cost': 'Cloud Cost',
    'arrival_rate': 'Arrival Rate',
}

legend_dict = {
    'constant': 'Constant',
    'linear_runtime': 'Runtime',
    'linear_cost': 'Cost',
    'zero': 'No Wait',
    'linear_runtime_filter_cpu': 'Runtime-Preempt-CPU'
}

def graph_metrics(metrics=None, fixed_values=OrderedDict(), varying_values=OrderedDict(), x_axis=['arrival_rate', 'system_utilization'], y_axis=['cloud_cost', 'onprem_cost']):
	# TODO: Use metrics as if sim_df
	# TODO: Specify the axes along which to graph the costs 
	# TODO: Specify the variables that are varied in generate_sweep(), pass that data into this function 
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

	'''
	TODO: Goal Format
	sweep1 = ("cpu_dist", 2)
	sweep2 = ("waiting_time", 11)
	sweep3 = ("arrival_rate", 6)

	index = 0 
	for i in range(sweep1[1]): 
		for j in range(sweep2[1]):
			for k in range(sweep3[1]):
				index += 1 
				data[i][j][k] = 0
	'''

	'''
	data = []
	for i in metrics: 
		m = metrics[i]
		params = {}

		# TODO: Remove preset params values, fill it in only based on fixed_values and varying_values
		params = {
			"wait_time": m['hyperparameters']['wait_time'],
			"cpu_dist": m['hyperparameters']['cpu_dist'],
			"policy": m['hyperparameters']['policy'],
			"arrival_rate": m['hyperparameters']['arrival_rate'],
			"cloud_cost": m['cloud_cost'],#['cost'][0],
			"onprem_cost": m['onprem_cost'],#['cost'][1],
			"system_utilization": m['system_utilization'],
			"cluster_utilization": m['cluster_utilization'],
			"job_completion_time": m['job_completion_time']
		}

		for key, value in fixed_values.items():
			params[key] = m['hyperparameters'][key]

		for key, value in varying_values.items():
			params[key] = m['hyperparameters'][key]

		# TODO: Efficiently group job data by hyperparameter sweep
		# TODO: Group all arrival_rates that have the same policy and waiting time
		# TODO: Generate plot format when creating sweep data 

		data.append(params)
	'''

	# TODO: Specify subplots dimensions based on number of varying_values 
	varying_values = list(varying_values.items())
	fixed_values = list(fixed_values.items())
	metrics_df = pd.DataFrame.from_dict(metrics)

	print(varying_values)
	print(fixed_values)
	rows, cols = 1, 1
	if len(varying_values) > 1: 
		key, value = varying_values[-2]
		rows = len(value)
	if len(varying_values) > 2: 
		key, value = varying_values[-3]
		cols = len(value)
	fig, axs = plt.subplots(nrows=rows, ncols=cols)

	#graph_grid = []
	#row = 0 
	#plots = []
	graphs = OrderedDict()
	
	print(varying_values)
	sweep_dimensions = [len(varying_values[i][1]) for i in range(len(varying_values))]
	print(sweep_dimensions)
	plot_dimensions = [[j for j in range(i)] for i in sweep_dimensions[:-1]]
	print("Plot Dimensions ")
	print(plot_dimensions)

	if plot_dimensions: 
		plot_dimensions = itertools.product(*plot_dimensions)
		for dim in plot_dimensions:
			#graph = graphs
			#test = graphs#[0][0]
			#for d in dim: 
			#	test = test[d]
			#graph = test
			graphs[dim] = OrderedDict()
			graphs[dim]['arrival_rate'] = [] #.append(trial['arrival_rate'])
			graphs[dim]['cloud_cost'] = [] #.append(trial['cloud_cost'])
			graphs[dim]['onprem_cost'] = [] #.append(trial['onprem_cost'])  
			graphs[dim]['system_utilization'] = [] #.append(trial['system_utilization'])
			graphs[dim]['cluster_utilization'] = []
			#graphs[dim]['job_completion_time'] = []
			graphs[dim]['avg_jct'] = []
	else:
		dim = 0
		graphs[dim]['arrival_rate'] = [] #.append(trial['arrival_rate'])
		graphs[dim]['cloud_cost'] = [] #.append(trial['cloud_cost'])
		graphs[dim]['onprem_cost'] = [] #.append(trial['onprem_cost'])  
		graphs[dim]['system_utilization'] = [] #.append(trial['system_utilization'])
		graphs[dim]['cluster_utilization'] = []
		#graphs[dim]['job_completion_time'] = []
		graphs[dim]['avg_jct'] = []

	print("GRAPH")
	print(graphs)


	maps = {}
	for i in range(len(metrics)):
	#for i in range(len(data)):
		trial = metrics[i]#data[i]
		# TODO: Specify the row to plot the data based on the varying_values dictionary 
		# TODO: Group the values of the same 1d sweep together (e.g. if first dimesion is arrival_rate, then one graph varies the arrival_rate)
		# TODO: Solve 1d, then 2d, then 3d
		# TODO: Use mod to group values
		#d1 = i % len(varying_values[0][1])
		#d1 = (i // len(varying_values[-1][1])) % len(varying_values[-2][1])
		#d2 = (i // (len(varying_values[-1][1]) * len(varying_values[-2][1]))) % len(varying_values[-3][1])

		# TODO: Clean up plotting using pandas dataframe
		# TODO: Remove indexing methods 
		d2 = (i // len(varying_values[-1][1])) % len(varying_values[-2][1])
		d1 = (i // (len(varying_values[-1][1]) * len(varying_values[-2][1]))) % len(varying_values[-3][1])
		dim = (d1, d2)

		maps[dim] = trial['arrival_rate']
		graphs[dim]['arrival_rate'].append(trial['arrival_rate'])
		graphs[dim]['cloud_cost'].append(trial['cloud_cost'])
		graphs[dim]['onprem_cost'].append(trial['onprem_cost'])  
		graphs[dim]['system_utilization'].append(trial['system_utilization'])
		graphs[dim]['cluster_utilization'].append(trial['cluster_utilization'])
		#graphs[dim]['job_completion_time'].append(trial['job_completion_time'])
		graphs[dim]['avg_jct'].append(trial['avg_jct'])

	print("MAP")
	print(maps)
	print("GRAPH")
	print(graphs)
	#time.sleep(1000)

	'''
	# Arrival Time vs. Cloud Cost [NOT STARTED]
	for dim in graphs: 
		#vals = varying_values[1][0] + " " + str(dim[0]) + " " + varying_values[2][0] + " " + str(dim[1])
		#vals = varying_values[1][0] + " " + str(varying_values[1][1][dim[0]]) + " " + varying_values[2][0] + " " + str(varying_values[2][1][dim[1]])
		#print(vals)
		
		axs[dim].plot(graphs[dim]['arrival_rate'], graphs[dim]['onprem_cost'], label="cloud_cost")
		axs[dim].set_xlabel('arrival_rate', fontsize=5)
		#axs[dim].set_xlabel('Arrival Rate (1/lambda)', fontsize=5)
		axs[dim].set_ylabel('Cost ($)', fontsize=5)
		#title =  "Wait time:  " + hp["wait_time"] + " CPU Dist [1, 2, 4] " + hp["cpu_dist"] + " Policy " + hp["policy"]
		#print(varying_values[1][0] + " ")
		#title = varying_values[1][0] + " " + str(varying_values[1][1][dim[0]]) + " " + varying_values[2][0] + " " + str(varying_values[2][1][dim[1]])
		title = "test"
		#title = varying_values[1][0] + " " + varying_values[1][1][dim[1]] + " " + varying_values[2][0] + " " + varying_values[1][1][dim[2]]
		axs[dim].set_title(title, fontsize=5)
	'''
	
	'''
	# TODO: Cluster Utilization [NOT STARTED]
	for dim in graphs: 
		axs[dim].plot(graphs[dim]['system_utilization'], graphs[dim]['cluster_utilization'], label="cloud_cost")
		axs[dim].set_xlabel('system_utilization', fontsize=5)
		axs[dim].set_ylabel('cluster_utilization', fontsize=5)
		title = "test"
		axs[dim].set_title(title, fontsize=5)
	'''

	xmin = math.inf 
	xmax = -1 * math.inf
	ymin = math.inf
	ymax = -1 * math.inf
	
	
	# TODO: JCT [NOT STARTED]
	# TODO: Incorporate realtime submission time logging for the future
	for dim in graphs: 
		#axs[dim].plot(graphs[dim]['system_utilization'], graphs[dim]['job_completion_time'], label="job_completion_time")
		axs[dim].plot(graphs[dim]['system_utilization'], graphs[dim]['avg_jct'], label="avg_jct")
		axs[dim].set_xlabel('system_utilization', fontsize=5)
		axs[dim].set_ylabel('job_completion_time', fontsize=5)
		title = varying_values[0][0] + " " + str(varying_values[0][1][dim[0]]) + " " + varying_values[1][0] + " " + str(varying_values[1][1][dim[1]])
		axs[dim].set_title(title, fontsize=5)
		
		curr_xmin, curr_xmax = axs[dim].get_xlim()
		curr_ymin, curr_ymax = axs[dim].get_ylim()
		xmin = min(curr_xmin, xmin)
		xmax = max(curr_xmax, xmax)
		ymin = min(curr_ymin, ymin)
		ymax = max(curr_ymax, ymax)

	'''
	def cost_difference(row):
        baseline_cost = row['total_cloud_cost_y']
        cost = row['total_cloud_cost_x']
        return baseline_cost - cost
	'''
	

	# TODO: Reimplement cost_difference without using pandas df [NOT STARTED]
	# TODO: Specify baseline based on dimension -- specify a baseline and a range to normalize
	# TODO: Create a function that finds dimension of all baseline functions
	# TODO: Create a function that finds set of dimensions that need to transformed according to baseline
	'''
	def load_dict_as_dataframe(metrics): 
		df = pd.DataFrame.from_dict(metrics)
		return df 
	'''

	metrics_dt = pd.DataFrame.from_dict(metrics)

	def find_baselines(graph):
		baselines = []
		return baselines

	def find_baseline_range(graph): 
		baseline_range = {}
		return baseline_range
	
	def cost_difference(graphs, baseline_range):
		# TODO: Get cloud costs for 0 wait time 
		baseline_cost = row['total_cloud_cost_y']
		# TODO: Get cloud costs for current wait time 
		cost = row['total_cloud_cost_x']

		return baseline_cost - cost
	

	#graphs = cost_difference(graphs)

	# TODO: Absolute Saving [NOT STARTED] 'cost_diff'
	# TODO: Add a conditional that only allows cost_diff to be applied if data with waiting time 0 can be found
	
	'''
	for dim in graphs: 
		axs[dim].plot(graphs[dim]['system_utilization'], graphs[dim]['absolute_saving'], label="absolute_saving")
		axs[dim].set_xlabel('system_utilization', fontsize=5)
		axs[dim].set_ylabel('absolute_saving', fontsize=5)
		title = varying_values[0][0] + " " + str(varying_values[0][1][dim[0]]) + " " + varying_values[1][0] + " " + str(varying_values[1][1][dim[1]])
		#title = "test"
		axs[dim].set_title(title, fontsize=5)
		
		curr_xmin, curr_xmax = axs[dim].get_xlim()
		curr_ymin, curr_ymax = axs[dim].get_ylim()
		xmin = min(curr_xmin, xmin)
		xmax = max(curr_xmax, xmax)
		ymin = min(curr_ymin, ymin)
		ymax = max(curr_ymax, ymax)

	# TODO: Reimplement cost_multiplier without using pandas df [NOT STARTED]
	def cost_multiplier(row):
		baseline_cost = row['total_cloud_cost_y']
		cost = row['total_cloud_cost_x']
		if baseline_cost == 0 and cost==0:
			return 0
		elif baseline_cost <=10000:
			# Small cloud cost for No wait
			# Savings over small cloud cost is negligible for organizations.
			return 0
		elif baseline_cost == 0 and cost>0:
			return 100
		return 100* (1 - (cost/baseline_cost))

	# TODO: Relative Cost saving [NOT STARTED] 'cost_mult'
	'''
	'''
	for i in graphs:
		axs[i[0]][i[1]].plot(graph[i]['arrival_rate'], graph[i]['cloud_cost'], label="cloud_cost")
		axs[i[0]][i[1]].plot(graph[i]['arrival_rate'], graph[i]['onprem_cost'], label="onprem_cost")
		axs[i[0]][i[1]].plot(graph[i]['arrival_rate'], graph[i]['system_utilization'], label="system_utilization")
		axs[i[0]][i[1]].set_xlabel('Arrival Rate (1/lambda)', fontsize=5)
		axs[i[0]][i[0]].set_ylabel('Cost ($)', fontsize=5)
		title =  "Wait time:  " + hp["wait_time"] + " CPU Dist [1, 2, 4] " + hp["cpu_dist"] + " Policy " + hp["policy"]
		axs[row][i % 6].set_title(title, fontsize=5)
	'''

	#print(graphs)
	
	xlim = (xmin, xmax)
	ylim = (ymin, ymax)

	for ax in axs.flat:
		ax.set_xlim(xlim)
		ax.set_ylim(ylim)

	plt.subplots_adjust(hspace=1)
	plt.show()



def read_cluster_event_data(cluster_log_path=None):#, submission_log_path=None):
	if not cluster_log_path: 
		cluster_log_path = "../logs/"
		files = os.listdir(cluster_log_path)

		# Iterate over the files and check if they have the ".json" extension
		for file in files:
			if file.endswith(".json"):
				cluster_log_path += str(file)
				break 

	with open(cluster_log_path, "r") as f: #"../logs/event_data.json", "r") as f:
		loaded_data = json.load(f)

	return loaded_data

def read_submission_data(submission_log_path=None):
	if submission_log_path: 
		with open(submission_log_path, "r") as f: #"../logs/event_data.json", "r") as f:
			loaded_data = json.load(f)
		return loaded_data
	return {}



def write_cluster_event_data(batch_repo=None, event_data=event_data, tag=None, loop=False):
	global cluster_event_data
	import logging
	#client.rest.logger.setLevel(logging.WARNING)
	logger = logging.getLogger(__name__)
	'''
	Outputs: 
	(1) Store relevant event data in a dictionary continously to disk

	Design Requirements: 
	(1) Track both long and short jobs
		(a) Store data from different experiments efficiently 

	Possible Designs: 
	(1) Update the event data dictionary then save locally as json

	Possible Tools: 
	(1) 
	'''

	'''
	Example Events

	Events:
	Type    Reason     Age   From               Message
	----    ------     ----  ----               -------
	Normal  Scheduled  52m   default-scheduler  Successfully assigned default/sleep-6-481852-sswbd to gke-starburst-default-pool-8bec73e3-81j8
	Normal  Pulling    52m   kubelet            Pulling image "alpine:latest"
	Normal  Pulled     52m   kubelet            Successfully pulled image "alpine:latest" in 118.522763ms
	Normal  Created    52m   kubelet            Created container sleep
	Normal  Started    52m   kubelet            Started container sleep
	'''
	

	log_frequency = 1
	# TODO: Write experiment metadata to job events metadata

	#existing_log_path = "../logs/event_data.json"

	# TODO: Move existing logs to archive
	archive_path = "../logs/archive/"

	# Get a list of all files in the current directory
	log_path = "../logs/"
	files = os.listdir(log_path)

	# Iterate over the files and check if they have the ".json" extension
	for file in files:
		if file.endswith(".json"):
			existing_log_path = str(file)
			os.rename(log_path + existing_log_path, archive_path + existing_log_path)

	'''
	if os.path.exists(existing_log_path):
		if not os.path.exists(archive_path):
			os.mkdir(archive_path)
		os.rename(existing_log_path, archive_path + "event_data_" + str(int(datetime.datetime.now().timestamp())))
	'''
	if batch_repo: 
		log_path = log_path + "archive/" + batch_repo + "/"
		if not os.path.exists(log_path):
			#os.mkdir(archive_path)
			os.mkdir(log_path)
		log_path += 'events/'
		if not os.path.exists(log_path):
			#os.mkdir(archive_path)
			os.mkdir(log_path)
		print("Made directory for hyperparameter search...")
		current_log_path = log_path + tag + ".json"
	else: 
		if tag: 
			current_log_path = log_path + "event_data_" + tag + "_" + str(int(datetime.datetime.now().timestamp())) + ".json"
		else: 
			current_log_path = log_path + "event_data_" + str(int(datetime.datetime.now().timestamp())) + ".json"

	# Load the Kubernetes configuration from the default location
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	# Create a Kubernetes API client
	onprem_api = client.CoreV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()

	'''
	clusters = {"onprem": onprem_api, "cloud": cloud_api}
	for type in clusters: 
		api = clusters[type]
		instances = retrieve_node_instance(api)
		event_data = cluster_event_data[type]
		event_data['node_instances'] = instances
	'''
	if not loop: 
		while True: 
			try: 
				with open(current_log_path, 'r') as f:
					cluster_event_data = json.load(f)
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

	# Get a list of all pods in the default namespace 
	while True:
		#logger
		clusters = {"onprem": onprem_api, "cloud": cloud_api}
		for type in clusters:
			api = clusters[type]
			if api is not None:
				events = api.list_event_for_all_namespaces()
				event_data = cluster_event_data[type]

				# TODO: Determine what to do with message data - item.message
				# TODO: Set TTL value to 30 days
				# TODO: Store events outside the cluster etcd database
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
							#Example message format: "Successfully assigned default/sleep-1-541823-wkbz7 to gke-starburst-default-pool-8bec73e3-81j81"
							match = re.search(r"Successfully assigned (\S+) to (\S+)", message)
							if match:
								_ = match.group(1)
								node_name = match.group(2)
								# TODO: Save pod scheduled time
								#event_data['']
								event_data['scheduled_nodes'][pod_name] = node_name
					elif event_reason == 'SuccessfulCreate':
						#TODO: Determine difference between job metrics and pod metrics
						involved_object = item.involved_object 
						if involved_object.kind == 'Job': 
							#Example message format: Created pod: sleep-2-476460-zzz6h
							job_name = involved_object.name 
							message = item.message
							match = re.search(r"Created pod: (\S+)", message)
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
		with open(current_log_path, "w") as f: #"../logs/event_data.json", "w") as f:
			json.dump(cluster_event_data, f)

		if not loop: 
			break 

		# Retrieve data each minute 
		time.sleep(log_frequency)
	
	return 0

def log_parser(log_file, new_file, strings): 
	'''
	Parse only lines from a log file such that the selected lines contain a specific substring 
	'''
	import re

	parsed_logs = []
	# Open the log file in read mode
	with open('./' + log_file, 'r') as f:
		# Loop over each line in the file
		for line in f:
			# Search for the patterns 'error' and 'warning'
			if re.search(': ~~~ ', line):
				# If the pattern is found, print the line
				#print(line.strip())
				parsed_logs.append(line.strip())

	with open('./' + new_file, 'w') as f:
		for line in parsed_logs:
			f.write(line + '\n')

	return parsed_logs

"""Misc Utils"""
EVENT_SWEEP = 1682925843
EVENT_SWEEP_05_03_2023 = 1683099273
def pull_vm_scheduler_logs(event_number=0):
	#TODO: Create log directory if not located yet
	# TODO: Set local python path
	#export PYTHONPATH=/Users/surya/Documents/sky/starburst
	#subprocess.run(['export', 'PYTHONPATH=/Users/surya/Documents/sky/starburst'])
	gcp_path = 'suryaven@sky-scheduler:/home/suryaven/test/starburst/starburst/logs/archive/{}/'.format(event_number)
	local_path = '../logs/archive/'
	#'/Users/suryaven/Documents/personal/sky/starburst/starburst/logs/archive/'

	plot_dirs = ["../logs/", "../logs/archive/"]
	for plot_dir in plot_dirs:
		if not os.path.exists(plot_dir):
			os.mkdir(plot_dir)
	#'--zone', 'us-central1-c',
	subprocess.run(['gcloud', 'compute',  'scp', '--recurse', gcp_path, local_path, '--zone', 'us-central1-c',])

