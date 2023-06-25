import logging
import numpy as np
import os
from typing import Dict, Tuple

from kubernetes import client, config
import yaml

from starburst.sweep import training_dataset

logger = logging.getLogger(__name__)

class RunConfig:
	def __init__(self, config_dict):
		self.__dict__.update(config_dict)

def load_yaml_file(file_path: str) -> dict:
	"""
	Loads a YAML file from a specified file path.

	Args:
		file_path (str): Path to YAML file.
	"""
	file_path = os.path.abspath(file_path)
	if not os.path.isfile(file_path):
		raise FileNotFoundError(f"Sweep config YAML not found: {file_path}")
	with open(file_path, 'r') as file:
		data = yaml.safe_load(file)
	return data


def save_yaml_object(obj_dict: dict, path: str) -> None:
	"""
	Saves a dictionary of objects to a YAML file.

	Args:
		obj_dict (dict): Dictionary of objects to save.
		path (str): Path to save YAML file.
	"""
	path = os.path.abspath(path)
	yaml_runs = yaml.dump(obj_dict)
	with open(path, "w") as f:
		f.write(yaml_runs)

def sample_gpu_train_job(gpu: int, duration: float) -> Tuple[int, str]:
	"""
	Returns a closest real-life training job closest to (gpu, duration) pair.
	"""
	jobs = [(j[1], j[3]) for j in training_dataset.ESTIMATED_TIMES if j[2] == gpu]
	min_delta = math.inf
	min_id = 0  
	for i in range(len(jobs)):
		delta = abs(jobs[i][0] - duration)
		if delta <= min_delta: 
			min_delta = delta
			min_id = i
	return jobs[min_id]

def check_empty_cluster(clusters: Dict[str, str]) -> bool:
	"""
	Returns true if there are no pods/jobs in both on-prem and cloud clusters.
	"""
	for kube_cluster_name in clusters.values():
		config.load_kube_config(context=kube_cluster_name)
		api = client.CoreV1Api()
		pods = api.list_namespaced_pod(namespace='default')
		for pod in pods.items:
			if "chakra" in pod.metadata.name:
				continue
			return False
	return True 


def clear_clusters(clusters: Dict[str, str]):
	"""
	Automates clearing of cluster state by removing event, logs, and pods on both onprem and cloud cluster.
	"""
	while True:
		try:
			api_batch_list = []
			for kube_cluster_name in clusters.values():
				# Fetching cluster APIs
				config.load_kube_config(context=kube_cluster_name)
				api = client.CoreV1Api()
				api_batch = client.BatchV1Api()
				api_batch_list.append(api_batch)
				# Deleting all jobs.
				jobs_list = api_batch.list_namespaced_job(namespace='default')
				for job in jobs_list.items:
					logger.debug(f'Attempting to Delete {job.metadata.name}')
					api_batch.delete_namespaced_job(
						name=job.metadata.name, 
						namespace='default', 
						body=client.V1DeleteOptions(
							propagation_policy='Foreground', 
							grace_period_seconds=0
							)
					)
				# Deleting all pod events.
				api.delete_collection_namespaced_event(
					namespace='default',
					body=client.V1DeleteOptions(propagation_policy='Foreground', 
							grace_period_seconds=0),
				)
				# Deleting all pods.
				pods = api.list_namespaced_pod(namespace='default')
				for pod in pods.items:
					if "chakra" in pod.metadata.name:
						continue					
					api.delete_namespaced_pod(name=pod.metadata.name, namespace=pod.metadata.namespace, body=client.V1DeleteOptions())
		except Exception as e:
			logger.debug(f'Exception {e} occurred while clearing cluster state. Retrying...')
		else:
			done = True
			for api_batch in api_batch_list:
				jobs_list = api_batch.list_namespaced_job(namespace='default')
				if len(jobs_list.items) != 0:
					done = False 
			if done:
				break