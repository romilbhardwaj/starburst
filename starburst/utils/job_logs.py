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

# TODO: Integrate kubecost or GCP calculator
# TODO: Include accurate cloud specific costs (e.g. network, disk, instance type)
# TODO: Submit cloud quotas requests

GCP_PRICES = {
	"e2-medium": 0.038795,
	"e2-standard-8": 0.31036
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
}

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
			print(image_pull_start_times)
			print(image_pull_end_times)
			
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

def plot_job_intervals(jobs, num_nodes, save=False, path=None, subplt=None, plt_index=None, tag=None):
	plot_jobs.plot_trace_spacetime_and_spillover(jobs, num_nodes, save=save, path=path, subplt=subplt, plt_index=plt_index, tag=tag)

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

def parse_event_logs(cluster_event_data=None, submission_data=None):#onprem_event_logs = None, cloud_event_logs = None):
	# TODO: Plot cloud and onprem cluster jobs together

	hyperparameters = None
	if 'hyperparamters' in submission_data: 
		hyperparameters = submission_data['hyperparameters']

	job_names = {}
	jobs = {'idx':[], 'runtime':[], 'arrival':[], 'num_gpus':[], 'allocated_gpus':[], 'start':[], 'instance_type':[], 'node_index': [], 'node': [], 'cpus': [], 'submission_time': []}

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
			#pod_start_times = cluster[]
			#pod_end_times = cluster[]
			start_times = cluster['job_creation_times']
			end_times = cluster['job_completion_times']
			pod_nodes = cluster['scheduled_nodes']
			job_pods = cluster['job_pods']
			node_instances = cluster['node_instances']

			pod_start_times = {}
			pod_end_times = {}
			#pod_nodes = {}
			
			min_arrival = math.inf

			# Get start times
			for pod in start_times: 
				pod_name = pod #pod['metric']['pod']
				pod_start_time = start_times[pod] #int(pod['value'][1])
				pod_start_times[pod_name] = pod_start_time
			
			for pod in end_times: 
				pod_name = pod #pod['metric']['pod']
				pod_end_time = end_times[pod] #int(pod['value'][1])
				pod_end_times[pod_name] = pod_end_time

			for pod in pod_nodes: 
				pod_name = pod #pod['metric']['pod']
				all_nodes.add(pod_nodes[pod])
				'''
				if pod_name in pod_start_times: 
					pod_node = pod['metric']['node']
					all_nodes.add(pod_node)
					pod_nodes[pod_name] = pod_node
				'''

			pod_completion_times = {}
			for pod in pod_start_times:
				if pod in pod_end_times:
					pod_completion_times[pod] = [pod_start_times[pod], pod_end_times[pod]]
			
			intervals = pod_completion_times

			# Job Trace Format
			for n in all_nodes: 
				nodes[n] = node_id
				node_id += 1

			print(all_nodes)
			print(pod_nodes)
			print(nodes)
			print(len(intervals))
			print(intervals)
			print(len(submission_data))
			for i, (key, value) in enumerate(intervals.items()):
				#print(len(intervals))
				print("index " + str(i))
				#print(key)
				
				#job_id 
				#s = "sleep-26-100444"
				# TODO: Note that event_job_id = job_data + 1
				job_id = re.findall(r'\d+', key)[0]
				print("job_id" + str(job_id))
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
				jobs['submission_time'].append(submission_data[job_id]['submit_time'])

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
		
	# TODO: Determine if logs should be initialized to submission_time or arrival_time
	min_arrival = min(jobs['arrival']) #min(jobs['submission_time']) #min(jobs['arrival'])
	jobs['arrival'] = [i - min_arrival for i in jobs['arrival']]
	jobs['submission_time'] = [i - min_arrival for i in jobs['submission_time']]
	jobs['start'] = [i - min_arrival if i is not None else None for i in jobs['start']]

	print("NODE NAMES: ")
	print(all_nodes)
	print(len(all_nodes))
	return jobs, len(all_nodes)

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


def view_real_arrival_times(event_number=None):#cluster_data_path=None, submission_data_path=None):
	costs = {}
	if event_number: #cluster_data_path and submission_data_path: 
		cluster_data_path = "../logs/archive/" + str(event_number) + "/events/"
		submission_data_path = "../logs/archive/" + str(event_number) + "/jobs/"
		files = os.listdir(cluster_data_path)
		num_graphs = len(files) #-2#+ 1 #2
		fig, axs = plt.subplots(nrows=num_graphs, ncols=1)
		#fig, axs = plt.subplots(nrows=2, ncols=1)
		# Iterate over the files and check if they have the ".json" extension
		#for file in files:
		file_count = 0 
		for i in range(len(files)):
			file = files[i]
			print("FILE NAME " + file)
			cluster_log_path = cluster_data_path + file
			submission_log_path = submission_data_path + file
			print("CLUSTER LOG PATH")
			print(cluster_log_path)
			cluster_event_data = read_cluster_event_data(cluster_log_path=cluster_log_path)
			submission_data = read_submission_data(submission_log_path=submission_log_path)
			jobs, num_nodes = parse_event_logs(cluster_event_data=cluster_event_data, submission_data=submission_data)#data)
			
			#cost = job_logs.cloud_cost(jobs=jobs, num_nodes=num_nodes)
			#costs[file] = cost
			plot_dir = "../logs/archive/plots/"
			if not os.path.exists(plot_dir):
				#os.mkdir(archive_path)
				os.mkdir(plot_dir)

			plot_path = "../logs/archive/plots/" + file[:-5] + ".png"
			print(plot_path)
			plot_job_intervals(jobs, num_nodes, save=True, path=plot_path, subplt=axs, plt_index=i, tag=str(file))
			
			#job_logs.plot_job_intervals(jobs, num_nodes)
			
			#if file.endswith(".json"):
			#	log_path = log_path + str(file)
			#	break 
			
			file_count += 1
			if file_count >= num_graphs: 
				break 
			
	#return costs
	plt.show()

	return 

def analyze_sweep(event_number=None):#path=None):
	"""Takes each batch job file and computes values (e.g. cloud cost, system utilization)"""

	'''
	0.1 -> 0.01137
	0.2 -> 0.00931
	0.3 -> 0.01448
	0.4 -> 0.00862
	0.5 -> 0.01500
	'''
	#costs = {}
	metrics = {}
	if event_number: #path: 
		cluster_data_path = "../logs/archive/" + str(event_number) + '/events/'
		submission_data_path = "../logs/archive/" + str(event_number) + '/jobs/'
		files = os.listdir(cluster_data_path)#path)
		#exempt_files = []
		files = sorted(files)

		# Iterate over the files and check if they have the ".json" extension
		for i in range(len(files)):
		#for file in files:
			#log_path = path + file
			#print(log_path)
			#data = read_cluster_event_data(cluster_log_path=log_path)
			#jobs, num_nodes = parse_event_logs(data)
			file = files[i]
			print("FILENAME: " + file)
			cluster_log_path = cluster_data_path + file
			submission_log_path = submission_data_path + file

			print(cluster_log_path)
			cluster_event_data = read_cluster_event_data(cluster_log_path=cluster_log_path)
			submission_data = read_submission_data(submission_log_path=submission_log_path)
			jobs, num_nodes = parse_event_logs(cluster_event_data=cluster_event_data, submission_data=submission_data)
			hyperparameters = submission_data['hyperparameters']

			cost, cost_density, system_utilization = compute_metrics(jobs=jobs, num_nodes=num_nodes)
			metrics[i] = {"cost": cost, "cost_density": cost_density, "system_utilization": system_utilization, "hyperparameters": hyperparameters}
			#costs[file] = cost
			
			#job_logs.plot_job_intervals(jobs, num_nodes)
			
			#if file.endswith(".json"):
			#	log_path = log_path + str(file)
			#	break 
	# TODO: Compute baseline cost and cost savings
	#print(metrics)
	#time.sleep(1000)
	graph_metrics(metrics)#, hyperparameters)
	return metrics

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
	start = jobs['start']
	max_arrival = max(jobs['arrival'])
	min_arrival = min(jobs['arrival'])
	total_time = 0 

	for i in range(len(runtimes)):
		print(start[i])
		runtime = runtimes[i] / (60 * 60)
		#total_time += runtime
		instance_type = instance_types[i]
		instance_cost_per_hour = GCP_PRICES[instance_type]
		total_time += runtimes[i]
		if start[i] == None: 
			cloud_cost += runtime * instance_cost_per_hour
		else: 
			onprem_cost += runtime * instance_cost_per_hour

	# TODO: Ensure accurate system utilization values		
	job_makespan = (4 * 8 * (max_arrival - min_arrival)) # 4 nodes per cluster w/ 8 CPU's each
	total_job_volume = total_time
	norm_system_utilization = job_makespan/total_job_volume

	return (cloud_cost, onprem_cost), (cloud_cost/total_time, onprem_cost/total_time), norm_system_utilization


def graph_metrics(metrics):
	# TODO: Specify the axes along which to graph the costs 
	# TODO: Specify the variables that are varied in generate_sweep(), pass that data into this function 
	#print(costs)
	#graph = {}
	
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

	data = []
	for i in metrics: 
		m = metrics[i]
		#cost = m['cost']
		#cost_value = cost['cost_density'] # dollars/seconds
		#hyperparameters = m['hyperparameters']
		
	#for cost in costs: 
		#cost_int = float(cost[:3])
		#cost_int = float(cost[5:8])
		#arrival_rate = hyperparameters['arrival_rate']
		#wait_time = hyperparameters['wait_time']
		#cpu_dist = hyperparameters['cpu_dist']
		#cpu_dist = str(cpu_dist)
		#policy = hyperparameters['policy']
		#params = (i, str(wait_time), cpu_dist, policy)
		#params = (str(wait_time), cpu_dist, policy, arrival_rate, cost)
		params = {
			"wait_time": m['hyperparameters']['wait_time'], #str(wait_time), 
			"cpu_dist": m['hyperparameters']['cpu_dist'], #cpu_dist, 
			"policy": m['hyperparameters']['policy'], #policy, 
			"arrival_rate": m['hyperparameters']['arrival_rate'], #arrival_rate, 
			"cloud_cost": m['cost'][0],
			"onprem_cost": m['cost'][1],
			"system_utilization": m['system_utilization']
		}

		# TODO: Efficiently group job data by hyperparameter sweep
		# TODO: Group all arrival_rates that have the same policy and waiting time

		# Generate plot format when creating sweep data 
		#group = (params["policy"], params["cpu)"])
		data.append(params)
		'''
		if params in graph: 
			#graph[params].append((arrival_rate, cost_value,))
			#graph[i].append((arrival_rate, cost_value,))
			graph.append(params)
		else: 
			#graph[params] = []
			graph = []
			#graph[params].append((arrival_rate, cost_value,))
			graph.append(params)
			#raph[i] = []
			#graph[i].append((arrival_rate, cost_value,))
		'''

		'''
		if cpu_dist in graph: 
			graph[cpu_dist].append((arrival_rate, cost_value,))
		else: 
			graph[cpu_dist] = []
			graph[cpu_dist].append((arrival_rate, cost_value,))
		'''
		'''
		#graph.append((cost_int, costs[cost]))
		if wait_time in graph: 
			graph[wait_time].append((arrival_rate, cost_value,))
		else: 
			graph[wait_time] = []
			graph[wait_time].append((arrival_rate, cost_value,))
		'''
	'''
	data = graph
	x = [x[0] for x in data]
	y1 = [y[1][0] for y in data]
	y2 = [y[1][1] for y in data]
	y3 = [y[2] for y in data]
	print(data)
	print(x)
	print(y1)
	print(y2)
	plt.bar(x, y1, width=0.025, label="cloud_cost")
	plt.bar([i + 0.025 for i in x], y2, width=0.025, label="onprem_cost")
	plt.xlabel('Arrival Rate')
	plt.ylabel('Cost ($)')
	plt.title('Wait Time ' + str(y3[0]))
	plt.show()
	'''

	#fig, axs = plt.subplots(nrows=len(graph) + 1, ncols=1)
	fig, axs = plt.subplots(nrows=3, ncols=6)

	#plt_index = 0 
	#row = 2
	#for wait in graph:
	#for i in range(len(costs)):
	row = 0 
	plots = []
	#for hp in graph:

	#params = (str(wait_time), cpu_dist, policy, arrival_rate, cost)
	#params = (str(wait_time), cpu_dist, policy, arrival_rate, cost)
	#hps = []
	#for i in range(len(graph)):
	from collections import defaultdict
	#default_dict
	graphs = defaultdict()#{}
	for i in range(len(data)):
		#hp = graph[i]
		#hps.append(hp)
		trial = data[i]
		#i = hp[0]
		#m = metrics[i]
		#wait = graph[cost['hyperparameters']]
		#params = (str(wait_time), cpu_dist, policy, arrival_rate, cost)
		#wait_time, cpu_dist, policy, arrival_rate, cost = hp
		'''
		wait_time = hp["wait_time"]
		cpu_dist = hp["cpu_dist"]
		policy = hp["policy"]
		arrival_rate = hp["arrival_rate"]
		onprem_cost = hp["onprem_cost"]
		cloud_cost = hp["cloud_cost"]
		system_utilization = hp["system_utilization"]
		'''
		#cost = hp["cost"]

		if trial['policy'] == "fifo_wait" and trial['cpu_dist'] == "[0.2, 0.4, 0.4]":
			row = 0
		elif trial['policy'] == "fifo_wait" and trial['cpu_dist'] == "[0, 0.5, 0.5]": 
			row = 1
		elif trial['policy'] == "fifo_onprem_only":
			row = 2 

		#data = graph[hp]
		
		#arrival_rate = [x["arrival_rate"] for x in hp]
		#onprem_cost = [x["onprem_cost"] for x in hp]
		#cloud_cost = [x["cloud_cost"] for x in hp]
		#system_utilization = [x["system_utilization"] for x in hp]
		
		#y1 = [y[1][0] for y in data]
		#y2 = [y[1][1] for y in data]

		#axs[plt_index].bar(x, y1, width=0.025, label="cloud_cost")
		#axs[plt_index].bar([i + 0.025 for i in x], y2, width=0.025, label="onprem_cost")
		plots.append((row, i%6))
		graph = (row, i%6)
		if graph not in graphs: 
			graphs[(row, i%6)] = {
				'arrial_rate': [],
				'cloud_cost': [],
				'onprem_cost': [],
				'system_utilization': []
			}#['arrival_rate'].append(0)
		graphs[(row, i%6)]['arrival_rate'].append(trial['arrival_rate'])
		graphs[(row, i%6)]['cloud_cost'].append(trial['cloud_cost'])
		graphs[(row, i%6)]['onprem_cost'].append(trial['onprem_cost'])  
		graphs[(row, i%6)]['system_utilization'].append(trial['system_utilization'])

	for i in graphs: 
		axs[i[0]][i[1]].plot(arrival_rate, cloud_cost, label="cloud_cost")
		axs[i[0]][i[1]].plot(arrival_rate, onprem_cost, label="onprem_cost")
		axs[i[0]][i[1]].plot(arrival_rate, system_utilization, label="system_utilization")
		axs[i[0]][i[1]].set_xlabel('Arrival Rate (1/lambda)', fontsize=5)
		axs[i[0]][i[0]].set_ylabel('Cost ($)', fontsize=5)
		title =  "Wait time:  " + hp["wait_time"] + " CPU Dist [1, 2, 4] " + hp["cpu_dist"] + " Policy " + hp["policy"]
		axs[row][i % 6].set_title(title, fontsize=5)
	#plt_index += 1
	#print(hp)
	#print(plots)
	#print

	#fig.tight_layout(pad=20.0)#, h_pad=50.0, w_pad=50.0)
	plt.subplots_adjust(hspace=1)
	plt.show()
		

		
	'''
	x = [x[0] for x in data]
	y1 = [y[1][0] for y in data]
	y2 = [y[1][1] for y in data]

	plt.bar(x, y1, label='Y1')
	#plt.bar(x, y2, label='Y2', bottom=y1)

	plt.xlabel('X')
	plt.ylabel('Y')
	plt.legend()
	plt.show()
	'''

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

def cost_difference(row):
	baseline_cost = row['total_cloud_cost_y']
	cost = row['total_cloud_cost_x']
	return baseline_cost - cost

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


def write_cluster_event_data(batch_repo=None, event_data=event_data, tag=None):
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

	# Get a list of all pods in the default namespace
	while True: 
		# Retrieve data each minute 
		time.sleep(5)
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
	
	return 0