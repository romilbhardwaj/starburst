from prometheus_api_client import PrometheusConnect
import matplotlib.pyplot as plt
import read_trace
import math

# Connect to Prometheus
onprem = PrometheusConnect(url="http://34.67.143.10:30000/", disable_ssl=True)
cloud = PrometheusConnect(url="http://34.28.53.85:30000/", disable_ssl=True)

def plot_hybrid_jobs():
	# TODO: Return jobs that migrate to multiple clusters
	return 

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

# TODO: Integrate kubecost or GCP calculator
# TODO: Include accurate cloud specific costs (e.g. network, disk, instance type)
# TODO: Submit cloud quotas requests

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

def cloud_cost(jobs, num_nodes): 
	# TODO: Compute steady state value i.e. remove cloud cost from first X and last X jobs
	# TODO: Compute total value i.e. beg to end simulation cost --> compute start and end time for each node
	arrivals = jobs['arrival']
	runtimes = jobs['runtime']
	terminations = arrivals + runtimes
	start_time = min(arrivals)
	end_time = max(terminations)
	total_time = end_time - start_time
	cost = AWS_PRICES['vCPU'] * total_time/60
	return cost * num_nodes

def plot_job_intervals(jobs, num_nodes):
	read_trace.plot_trace_spacetime_and_spillover(jobs, num_nodes)

def parse_jobs(onprem=onprem, cloud=cloud):
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