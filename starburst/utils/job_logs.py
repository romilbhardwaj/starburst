from prometheus_api_client import PrometheusConnect
import matplotlib.pyplot as plt
import read_trace
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

def cloud_cost(jobs, num_nodes):
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
	for i in range(len(runtimes)):
		print(start[i])
		if start[i] == None: 
			runtime = runtimes[i] / (60 * 60)
			instance_type = instance_types[i]
			instance_cost = GCP_PRICES[instance_type]
			cloud_cost += runtime * instance_cost
		else: 
			runtime = runtimes[i] / (60 * 60)
			instance_type = instance_types[i]
			instance_cost = GCP_PRICES[instance_type]
			onprem_cost += runtime * instance_cost

	return cloud_cost, onprem_cost

def plot_job_intervals(jobs, num_nodes, save=False, path=None, subplt=None, plt_index=None, tag=None):
	read_trace.plot_trace_spacetime_and_spillover(jobs, num_nodes, save=save, path=path, subplt=subplt, plt_index=plt_index, tag=tag)

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
			print(intervals)
			for i, (key, value) in enumerate(intervals.items()):
				#job_id 
				#s = "sleep-26-100444"
				job_id = re.findall(r'\d+', key)[0]
				# sleep-26-100444 - format
				job_names[i] = key
				jobs['idx'].append(int(job_id))#i)
				jobs['runtime'].append(value[1] - value[0])
				jobs['arrival'].append(value[0])
				jobs['num_gpus'].append(1)

				#if job_id in submission_data: 
				jobs['cpus'].append(submission_data[job_id]['cpus'])
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
		
	min_arrival = min(jobs['arrival'])
	jobs['arrival'] = [i - min_arrival for i in jobs['arrival']]
	jobs['start'] = [i - min_arrival if i is not None else None for i in jobs['start']]
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

def graph_benchmark(costs):
	graph = []
	for cost in costs: 
		cost_int = float(cost[:3])
		graph.append((cost_int, costs[cost]))
	data = graph
	x = [x[0] for x in data]
	y1 = [y[1][0] for y in data]
	y2 = [y[1][1] for y in data]
	print(data)
	print(x)
	print(y1)
	print(y2)
	plt.bar(x, y1, width=0.025, label="cloud_cost")
	plt.bar([i + 0.025 for i in x], y2, width=0.025, label="onprem_cost")
	plt.xlabel('Arrival Rate')
	plt.ylabel('Cost ($)')
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

'''
def view_real_arrival_times_redacted_redacted(path=None):
	costs = {}
	if path: 
		files = os.listdir(path)
		fig, axs = plt.subplots(nrows=len(files), ncols=1)
		# Iterate over the files and check if they have the ".json" extension
		#for file in files:
		for i in range(len(files)):
			file = files[i]
			log_path = path + file
			print(log_path)
			cluster_data = read_cluster_event_data(log_path = log_path)
			jobs, num_nodes = parse_event_logs(cluster_data)
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
	#return costs
	plt.show()

	return 
'''


def view_real_arrival_times(cluster_data_path=None, submission_data_path=None):
	costs = {}
	if cluster_data_path and submission_data_path: 
		files = os.listdir(cluster_data_path)
		fig, axs = plt.subplots(nrows=len(files) + 1, ncols=1)
		#fig, axs = plt.subplots(nrows=1, ncols=1)
		# Iterate over the files and check if they have the ".json" extension
		#for file in files:
		file_count = 0 
		for i in range(len(files)):
			file = files[i]
			cluster_log_path = cluster_data_path + file
			submission_log_path = submission_data_path + file

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
			#file_count += 1
			#if file_count >= 2: 
			#	break 
			
	#return costs
	plt.show()

	return 


def benchmark_hyperparamter_search(path=None):
	'''
	0.1 -> 0.01137
	0.2 -> 0.00931
	0.3 -> 0.01448
	0.4 -> 0.00862
	0.5 -> 0.01500
	'''
	costs = {}
	if path: 
		files = os.listdir(path)

		# Iterate over the files and check if they have the ".json" extension
		for file in files:
			log_path = path + file
			print(log_path)
			data = read_cluster_event_data(log_path = log_path)
			jobs, num_nodes = parse_event_logs(data)
			cost = cloud_cost(jobs=jobs, num_nodes=num_nodes)
			costs[file] = cost
			
			#job_logs.plot_job_intervals(jobs, num_nodes)
			
			#if file.endswith(".json"):
			#	log_path = log_path + str(file)
			#	break 
	graph_benchmark(costs)
	return costs

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
					
		with open(current_log_path, "w") as f: #"../logs/event_data.json", "w") as f:
			json.dump(cluster_event_data, f)
	
	return 0 