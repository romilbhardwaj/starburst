import copy
import datetime
import json
import logging
import os
import re
import time

from kubernetes import client, config

from  starburst.sweep import sweep_logger, utils

EVENT_DATA_TEMPLATE = {
		'container_creation_times': {},
		'container_start_times': {},
		'image_pull_start_times': {},
		'image_pull_end_times': {},
		'scheduled_nodes': {},
		'job_creation_times': {},
		'job_completion_times': {},
		'job_pods': {}, 
		'node_instances': {},
		'gpu_index':{},
		'node_name': {}
}
EVENT_LOG_FREQUENCY = 1

logger = logging.getLogger(__name__)

def write_cluster_event_data(batch_repo=None, cluster_event_data=None, tag=None, onprem_cluster="", cloud_cluster="", index=None):
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
	Normal  Completed  52m   kubelet            Job completed
	'''


	log_path = sweep_logger.LOG_DIRECTORY.format(name=batch_repo) + '/events/'
	current_log_path = log_path + tag + ".yaml"

	# TODO Verify if they will interfere
	config.load_kube_config(context=onprem_cluster)
	onprem_api = client.CoreV1Api()

	config.load_kube_config(context=cloud_cluster)
	cloud_api = client.CoreV1Api()

	end = False 
	while True:
		clusters = {"onprem": onprem_api, "cloud": cloud_api}
		for type in clusters:
			api = clusters[type]
			if api is not None:
				# TODO: Rate Limitted 
				events = api.list_event_for_all_namespaces()
				event_data = cluster_event_data[type]
				# TODO: Determine what to do with message data - item.message
				instances = retrieve_node_instance(api)
				event_data['node_instances'] = instances
				# TODO: Integrate GPU INDEX logging
				# TODO: gpu_index = api.read_namespaced_pod_log(name=pod_name, namespace="default")
				try: 
					pod_list = api.list_namespaced_pod(namespace="default")
					for gpu_pod in pod_list.items:
						gpu_pod_name = gpu_pod.metadata.name
						if "chakra" not in gpu_pod_name and "prepull" not in gpu_pod_name:
							gpu_index = api.read_namespaced_pod_log(name=gpu_pod_name, namespace="default")
							event_data['gpu_index'][gpu_pod_name] = gpu_index
							#pod = api.read_namespaced_pod(name=pod_name, namespace="default")
							# TODO: Verify node_name is parsed properly 
							event_data['node_name'][gpu_pod_name] = gpu_pod.spec.node_name

				except Exception as e: 
					logger.debug("POD LOG ERROR CAUGHT: " + str(e))
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
							event_data['scheduled_nodes'][pod_name] = message
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
							logger.debug(f'Logged Job Completion Time for job {job_name} at time {job_completion_time}')
		# TODO: Save job hyperparameters directly into job events metadata	
		utils.save_yaml_object(cluster_event_data, current_log_path)
		time.sleep(EVENT_LOG_FREQUENCY)

		p1_log = sweep_logger.LOG_DIRECTORY.format(name=batch_repo) + '/debug/' + 'event_logger.log'
		with open(p1_log, "a") as f:
			f.write("retrieved event p1 " + str(index) + '\n')

		if end: 
			with open(p1_log, "a") as f:
				f.write("reached end of p1 " + str(index) + '\n')
			return 0

		signal_file = "../sweep_logs/"+ batch_repo + '/signal.lock' 
		if os.path.exists(signal_file):
			# TODO: Loop one last time
			end = True 

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

def logger_service(tag=None, batch_repo=None, onprem_cluster="", cloud_cluster="", index=None):
	cluster_event_data = {
		'onprem': copy.deepcopy(EVENT_DATA_TEMPLATE),
		'cloud': copy.deepcopy(EVENT_DATA_TEMPLATE)
	}
	write_cluster_event_data(batch_repo=batch_repo, cluster_event_data=cluster_event_data, tag=tag, onprem_cluster=onprem_cluster, cloud_cluster=cloud_cluster, index=index)