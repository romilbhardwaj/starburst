import logging
import re
import time
from typing import Dict, Optional
import time
import yaml
from kubernetes import client, config
from kubernetes.client import models

from starburst.types.job import Job

client.rest.logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class KubernetesManager(object):
	""" Kubernetes manager.

	Provides helper methods to:
	1. Submit job YAMLs to Kubernetes
	2. Get job status
	3. Get cluster resources
	"""

	def __init__(self, kube_context=None):
		# Load kubernetes config for the given context
		config.load_kube_config(context=kube_context)
		# Create kubernetes client
		self.core_v1 = client.CoreV1Api()
		self.batch_v1 = client.BatchV1Api()


	def get_total_cluster_resources(self):
		""" Get cluster resources. """
		nodes = self.core_v1.list_node()
		total_res = {
			"cpu": 0,
			"memory": 0,
			"gpu": 0,
		}
		for node in nodes.items:
			total_res["cpu"] += int(node.status.capacity["cpu"])
			total_res["memory"] += int(node.status.capacity["memory"][:-2])
			total_res["gpu"] += int(node.status.capacity.get("nvidia.com/gpu", 0))
		return total_res

	def get_total_cluster_resource_usage(self):
		""" Get cluster resources usage """
		nodes = self.core_v1.list_node()
		total_res = {
			"cpu": 0,
			"memory": 0,
			"gpu": 0,
		}
		for node in nodes.items:
			total_res["cpu"] += int(node.status.allocatable["cpu"])
			total_res["memory"] += int(node.status.allocatable["memory"][:-2])
			total_res["gpu"] += int(node.status.allocatable.get("nvidia.com/gpu", 0))
		return total_res

	@staticmethod
	def parse_resource_cpu(resource_str):
		""" Parse CPU string to cpu count. """
		unit_map = {'m': 1e-3, 'K': 1e3}
		value = re.search(r'\d+', resource_str).group()
		unit = resource_str[len(value):]
		return float(value) * unit_map.get(unit, 1)

	@staticmethod
	def parse_resource_memory(resource_str):
		""" Parse resource string to megabytes. """
		unit_map = {'Ki': 2 ** 10, 'Mi': 2 ** 20, 'Gi': 2 ** 30, 'Ti': 2 ** 40}
		value = re.search(r'\d+', resource_str).group()
		unit = resource_str[len(value):]
		return float(value) * unit_map.get(unit, 1) / (
					2 ** 20)  # Convert to megabytes

	def get_cluster_resources(self):
		start_time = time.perf_counter()
		curr_time = time.perf_counter()
		logger.debug("Started get_cluster_resources(): ~~~ --- " + str(curr_time-start_time))
		# Load the kubeconfig
		config.load_kube_config()

		# Create an API client
		api_instance = client.CoreV1Api()

		# Initialize total resources
		total_cpu = 0
		total_memory = 0

		# Set pagination parameters
		limit = None # 50
		continue_token = ""

		while True:
			# Get a batch of nodes
			nodes, _, _ = api_instance.list_node_with_http_info(limit=limit, _continue=continue_token)

			# Loop through each node and sum their resources
			for node in nodes.items:
				cpu_capacity = int(node.status.capacity['cpu'])
				memory_capacity = int(node.status.capacity['memory'].rstrip('Ki'))

				total_cpu += cpu_capacity
				total_memory += memory_capacity

			# Check if there are more nodes to fetch
			if nodes.metadata._continue:
				continue_token = nodes.metadata._continue
			else:
				break

		curr_time = time.perf_counter()
		logger.debug("Completed get_cluster_resources(): ~~~ --- " + str(curr_time-start_time))
		logger.debug(str(total_cpu))
		logger.debug(str(total_memory))
		return total_cpu, total_memory

	## Get cluster resources
	#total_cpu, total_memory = get_cluster_resources()

	#print(f"Total CPU: {total_cpu} cores")
	#print(f"Total Memory: {total_memory / 1024**2:.2f} GiB")
	def stream_state():
		# TODO: Implement asynchronous function that updates cluster state with each schedule event
		return 

	def get_state():
		# TODO: Retrieves data from dictionary that finds state 
		return

	def get_allocatable_resources_per_node(self) -> Dict[str, Dict[str, int]]:
		""" Get allocatable resources per node. """
		# Get the nodes and running pods
		start_time = time.perf_counter()
		curr_time = time.perf_counter()

		logger.debug("Started get_allocatable_resources_per_node(): ~~~ --- " + str(curr_time-start_time))
		#nodes = self.core_v1.list_node().items
		#pods = self.core_v1.list_pod_for_all_namespaces(watch=False).items
		#logger.debug("list_node() Output: ~~~ --- " + str(nodes))
		#logger.debug("list_pod_for_all_namespaces() Output: ~~~ --- " + str(nodes))

		# TODO: Don't reiniate the kubeconfig and use the default values 
		#config.load_kube_config()
		#api_instance = client.CoreV1Api()

		api_instance = self.core_v1
		limit = None #50
		continue_token = ""
		nodes, _, _ = api_instance.list_node_with_http_info(limit=limit, _continue=continue_token)
		pods, _, _ = api_instance.list_pod_for_all_namespaces_with_http_info(limit=limit, _continue=continue_token)#watch=False)
		#logger.debug("list_node_with_http_info() Output: ~~~ --- " + str(nodes))
		#logger.debug("list_pod_for_all_namespaces_with_http_info() Output: ~~~ --- " + str(nodes))

		nodes = nodes.items
		pods = pods.items

		#logger.debug("All Nodes: ~~~ --- " + str(nodes))
		#logger.debug("All Pods: ~~~ --- " + str(pods))

		curr_time = time.perf_counter()
		logger.debug("Completed get_allocatable_resources_per_node(): ~~~ --- " + str(curr_time-start_time))
		
		# Get a batch of nodes
		# TODO: Verify that nodes information is correct
		#nodes, _, _ = api_instance.list_node_with_http_info(limit=limit, _continue=continue_token)
		# TODO: Verify that pod information is correct

		# Initialize a dictionary to store available resources per node
		available_resources = {}
		running_pods = set() #{}

		for node in nodes:
			name = node.metadata.name
			total_cpu = self.parse_resource_cpu(node.status.allocatable['cpu'])
			total_memory = self.parse_resource_memory(
				node.status.allocatable['memory'])
			total_gpu = int(node.status.allocatable.get('nvidia.com/gpu', 0))

			used_cpu = 0
			used_memory = 0
			used_gpu = 0

			for pod in pods:
				#logger.debug("Pod resource information: ~~~ --- " + str(pod))
				if pod.spec.node_name == name and pod.status.phase in ['Running', 'Pending'] and pod.metadata.namespace == 'default':
					running_pods.add(pod.metadata.name)
					for container in pod.spec.containers:
						if container.resources.requests:
							used_cpu += self.parse_resource_cpu(
								container.resources.requests.get('cpu', '0m'))
							used_memory += self.parse_resource_memory(
								container.resources.requests.get('memory',
																 '0Mi'))
							used_gpu += int(container.resources.requests.get(
								'nvidia.com/gpu', 0))
							'''
							used_resources = {
								"cpu": used_cpu,
								"memory": used_memory,
								"gpu": used_gpu
							}
							logger.debug("Used resources form can_fit(): ~~~ --- " + str(used_resources))
							'''
			
			used_resources = {
				"cpu": used_cpu,
				"memory": used_memory,
				"gpu": used_gpu
			}
			logger.debug("Used resources form can_fit(): ~~~ --- " + str(used_resources))
			#time.sleep(1000000000)
			available_cpu = total_cpu - used_cpu
			available_memory = total_memory - used_memory
			available_gpu = total_gpu - used_gpu

			available_resources[name] = {
				'cpu': available_cpu,
				'memory': available_memory, # MB
				'gpu': available_gpu
			}

		logger.debug("Available resources from can_fit(): ~~~ --- " + str(available_resources))

		return available_resources, running_pods

	def job_running(self, job_name=None, namespace=None):
		def find_job_with_substring(jobs, substring):
			for job in jobs:
				if substring in job.metadata.name:
					return job.metadata.name
			return None
		
		limit = None
		continue_token = ""
		job_list, _, _ = self.batch_v1.list_namespaced_job_with_http_info(namespace="default", limit=limit, _continue=continue_token)      
		#logger.debug(f'job name submitted {job_name}')  
		real_job_name = find_job_with_substring(job_list.items, job_name)
		logger.debug("FINDING JOB " +  str(job_name) + " Found: " + str(real_job_name))
		if real_job_name: 
			job = self.batch_v1.read_namespaced_job_status_with_http_info(name=real_job_name, namespace="default")
			logger.debug("NEW JOB STATUS " + str(job[0].status) + " JOB NAME " +  str(job_name) + " Found: " + str(real_job_name))
			#, limit=limit, _continue=continue_token)
			'''
			# Check the job status
			if job.status.active is not None:
				# Job is currently active, it's not waiting in the queue
				print("Job is active and running.")
			elif job.status.conditions is not None:
				# Job is waiting in the queue
				print("Job is waiting in the queue.")
			else:
				# Job is completed
				print("Job has completed.")
			return
			'''
			return job[0].status.active
		else: 
			return 0 
	
	'''
	def empty_queue(self): 
		
		job = self.batch_v1.read_namespaced_job_status_with_http_info .read_namespaced_job(name=job_name, namespace=namespace)
		
		# Check the job status
		if job.status.active is not None:
			# Job is currently active, it's not waiting in the queue
			print("Job is active and running.")
		elif job.status.conditions is not None:
			# Job is waiting in the queue
			print("Job is waiting in the queue.")
		else:
			# Job is completed
			print("Job has completed.")
		return
	'''

	def can_fit(self, job: Job) -> Optional[str]:
		""" Check if a job can fit in the cluster. """
		#self.get_cluster_resources()
		start_time = time.perf_counter()
		curr_time = time.perf_counter()
		logger.debug("Started can_fit(): ~~~ --- " + str(curr_time-start_time))
		job_resources = job.resources

		# TODO: if previous has been scheduled than can move on
		
		cluster_resources, running_pods = self.get_allocatable_resources_per_node()
		
		for node_name, node_resources in cluster_resources.items():
			if node_resources["cpu"] >= job_resources.get("cpu", 0) and \
					node_resources["memory"] >= job_resources.get("memory", 0) and \
					node_resources["gpu"] >= job_resources.get("gpu", 0):
				curr_time = time.perf_counter()
				logger.debug("Completed can_fit(): ~~~ --- " + str(curr_time-start_time))
				return node_name
		curr_time = time.perf_counter()
		logger.debug("Completed can_fit(): ~~~ --- " + str(curr_time-start_time))
		return None

	def submit_job(self, job: Job):
		""" Submit a YAML which contains the Kubernetes Job declaration using the batch api """
		start_time = time.perf_counter()
		curr_time = time.perf_counter()
		logger.debug("Started submit_job(): ~~~ --- " + str(curr_time-start_time))
		# Parse the YAML file into a dictionary
		job_dict = yaml.safe_load(job.job_yaml)
		# Create a Kubernetes job object from the dictionary
		k8s_job = models.V1Job()
		# Append random string to job name to avoid name collision
		k8s_job.metadata = models.V1ObjectMeta(name=str(job_dict['metadata']['name']))# + '-' + job.job_id)
		k8s_job.spec = models.V1JobSpec(template=job_dict['spec']['template'])
		self.batch_v1.create_namespaced_job(namespace="default", body=k8s_job)
		curr_time = time.perf_counter()
		logger.debug("Completed submit_job(): ~~~ --- " + str(curr_time-start_time))

	def get_job_status(self, job_name):
		""" Get job status. """
		job = self.batch_v1.read_namespaced_job_status(job_name, namespace="default")
		return job.status
	