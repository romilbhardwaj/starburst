from prometheus_api_client import PrometheusConnect
import matplotlib.pyplot as plt

# Connect to Prometheus
prom = PrometheusConnect(url="http://34.67.143.10:30000/", disable_ssl=True)

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

def plot_job_intervals():
	# TODO: Plot all pods running on the same node together
	'''
	Parse `kube_pod_info` --> if node name is not found, then pod not scheduled onto a node
	'''

	# Define the query
	query = 'kube_pod_start_time'

	# Get the data
	data = prom.get_current_metric_value(query)
	#print(data)

	start_times = prom.get_current_metric_value('kube_pod_start_time')
	end_times = prom.get_current_metric_value('kube_pod_completion_time')
	pod_info = prom.get_current_metric_value('kube_pod_info')
	#print(end_times)

	pod_start_times = {}
	pod_end_times = {}
	pod_nodes = {}
	all_nodes = set()

	# Get start times
	for pod in start_times: 
		pod_name = pod['metric']['pod']
		pod_start_time = int(pod['value'][1])
		pod_start_times[pod_name] = pod_start_time

	for pod in end_times: 
		pod_name = pod['metric']['pod']
		pod_end_time = int(pod['value'][1])
		pod_end_times[pod_name] = pod_end_time

	for pod in pod_info: 
		pod_name = pod['metric']['pod']
		if pod_name in pod_start_times: 
			pod_node = pod['metric']['node']
			all_nodes.add(pod_node)
			pod_nodes[pod_name] = pod_node

	pod_completion_times = {}
	for pod in pod_start_times:
		if pod in pod_end_times: 
			pod_completion_times[pod] = [pod_start_times[pod], pod_end_times[pod]]
	#print(pod_completion_times)

	intervals = pod_completion_times
	fig, ax = plt.subplots()

	'''
	for i, (key, value) in enumerate(intervals.items()):
		#value = intervals[key]
		#print(str(value[1]-value[0]) + " " + str(value[0]))
		ax.barh(i, width=(value[1]-value[0]), left=value[0], height=0.5, label=key)
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
	# Pod Graph
	ax.set_yticks(range(len(intervals)))
	ax.set_yticklabels(list(intervals.keys()))
	ax.invert_yaxis()
	ax.set_xlabel('Time')
	ax.set_ylabel('Interval Name')
	'''
	plt.show()
	plt.savefig('../plots/job_intervals.png')