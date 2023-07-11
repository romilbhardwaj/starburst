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
import starburst.sweep.submit_sweep as submit_sweep
import pandas as pd
import subprocess
import numpy as np
import yaml

"""
# TODO: Integrate kubecost or GCP calculator
# TODO: Submit cloud quotas requests
"""

SIGNAL_FILE = ""
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

def retrieve_events_df(event_number=None, avoid_congestion=False, only_dict=False):	
	"""Turns all logs from sweep into a pandas dataframe for analysis"""
	
	events_dfs = {}
	if event_number:
		cluster_data_path = "../sweep_logs/" + str(event_number) + '/events/'
		submission_data_path = "../sweep_logs/" + str(event_number) + '/jobs/'
		sweep_data_path = "../sweep_logs/" + str(event_number) + "/sweep.yaml"
		with open(sweep_data_path, "r") as f:
			sweep_data = yaml.safe_load(f)
		sweep_df = pd.DataFrame.from_dict(sweep_data)

		files = os.listdir(cluster_data_path)

		for i in range(len(files)):
			#import pdb; pdb.set_trace()
			log_file = file = str(i) + ".log"
			file = str(i) + ".yaml" #".json"
			cluster_log_path = cluster_data_path + file
			submission_log_path = submission_data_path + file
			cloud_log_path = cluster_data_path + log_file

			try:
				cluster_event_data = read_cluster_event_data(cluster_log_path=cluster_log_path)
				submission_data = read_submission_data(submission_log_path=submission_log_path)
			except Exception as e:
				print(e)
				continue
			#cloud_log_df = pd.read_csv(cloud_log_path, delimiter='\n', sep=None, header=None)#sep=' ', header=None)
			with open(cloud_log_path, "r") as f:
				cloud_log_list = f.read().split('\n')

			cluster_event_data_df = pd.DataFrame.from_dict(cluster_event_data)
			submission_data_df = pd.DataFrame.from_dict(submission_data)

			events_dfs[i] = (cluster_event_data_df, submission_data_df, cloud_log_list)

	if only_dict: 
		return cluster_event_data, sweep_data
	#return cluster_event_data_df, submission_data_df, sweep_data_df
	return events_dfs, sweep_df

def retrieve_pod_logs(cluster="", file_name="cluster_pod_logs.txt"):
	config.load_kube_config(context=cluster)
	api = client.CoreV1Api()
	resps = []
	while True: 
		pod_list = api.list_namespaced_pod(namespace="default")
		for pod in pod_list.items:
			pod_name = pod.metadata.name
			resp1 = api.read_namespaced_pod_log(name=pod_name, namespace="default")
			#resp2 = api.read_namespaced_pod_status(name=pod_name, namespace="default")
			resps.append(pod_name)
			resps.append(resp1)
			#resps.append(resp2)
		break 
	
	with open(file_name, 'w') as f:
		f.write(str(resps))
	return

def retrieve_pod_data(cluster="", file_name="cluster_pod_data.txt"):
	config.load_kube_config(context=cluster)
	api = client.CoreV1Api()
	while True: 
		pod_list = api.list_namespaced_pod(namespace="default")
		break

	with open(file_name, 'w') as f:
		f.write(str(pod_list))
	return pod_list

def retrieve_node_data(cluster="", file_name="cluster_node_data.txt"):
	config.load_kube_config(context=cluster)
	api = client.CoreV1Api()
	while True: 
		node_list = api.list_node().items
		break
	with open(file_name, 'w') as f:
		f.write(str(node_list))
	return node_list

def retrieve_raw_events():
	config.load_kube_config(context="")
	api = client.CoreV1Api()
	events = api.list_event_for_all_namespaces()
	text_file = open("../../local/artifacts/raw_logs.txt", "w")
	n = text_file.write(str(events))
	text_file.close()

def read_cluster_event_data(cluster_log_path=None):
	if not cluster_log_path: 
		cluster_log_path = "../sweep_logs/"
		files = os.listdir(cluster_log_path)

		for file in files:
			if file.endswith(".yaml"): #(".json"):
				cluster_log_path += str(file)
				break 

	with open(cluster_log_path, "r") as f:
		loaded_data = yaml.safe_load(f) #json.load(f)

	return loaded_data

def read_submission_data(submission_log_path=None):
	if submission_log_path: 
		with open(submission_log_path, "r") as f:
			loaded_data = yaml.safe_load(f) #json.load(f)
		return loaded_data
	return {}

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
	local_path = '../sweep_logs/'

	plot_dirs = ["../sweep_logs/"]
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