import numpy as np 
import matplotlib.pyplot as plt
import os 
import time
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from kubernetes import client, config
from datetime import datetime
from starburst.drivers import main_driver

'''
Design Layout

1. Generate Job Hyperparameters
	a. Hyperparameters
		i. Arrival Time
		ii. Sleep Time
			a. 5 min lower bound
			b. 24 hr upper bound
		iii. Workload Size
			a. CPUs
			b. GPUs
2. Insert Hyperparameters into Jinja Job Yaml
3. Submit Batch of Jobs
	a. Same arrival time 
		i. Different sleep time 
		ii. Diferent workload size
	b. Randomly sampled arrival time
		i. Different sleep time
		ii. Different workload size

Example -- Fixed workload and sleep time
- Same workload, same sleep time
	- Varying arrival time
		- Simulate as a poisson process: https://timeseriesreasoning.com/contents/poisson-process/
		- Specify difference between arrival time of two events from exponential distribution
			- Keep a cumalitive sum of the times stored in an array
	- Submit Jobs to Array of Job times
		- Simple loop 
		- Multithreading 
			- https://www.studytonight.com/python/python-threading-timer-object
	

Option 1: 
	- if proability of event is less than generated thresshold then submit job 
	- space betwen two events follows exponential 
'''

def arrival_times(num_jobs):
	""" Generates arrival times of jobs into an array and plots values """
	curr_time = 0
	times = []
	for i in range(num_jobs):
		curr_time += np.random.exponential(scale=2.0)
		times.append(curr_time)
	plt.eventplot(times)
	plt.savefig('../plots/arrival_times.png')
	return times

def start_scheduler(policy="fifo_onprem_only", onprem_cluster="gke_sky-burst_us-central1-c_starburst", cloud_cluster="gke_sky-burst_us-central1-c_starburst-cloud"):
	os.system('python3 -m starburst.drivers.main_driver --policy {} --onprem_k8s_cluster_name {} --cloud_k8s_cluster_name {}'.format(policy, onprem_cluster, cloud_cluster))	

def submit_jobs(arrival_times, timeout): 
	""" Submits a a default job for each time stamp of the inputed arrival times """
	total_jobs = len(arrival_times)
	start_time = time.time()
	job = 0 
	while True: 
		curr_time = time.time()
		if job < total_jobs and curr_time > arrival_times[job] + start_time: 
			job += 1
			print(job)
			job_duration = np.random.normal(10, 3) #exponential(scale=10)
			cpus = 0.1 #min(0, int(np.random.exponential(scale=3)))
			gpus = min(0, int(np.random.exponential(scale=2)))
			memory = min(0, int(np.random.exponential(scale=50)))
			job_workload = {"gpu": gpus, "cpu":cpus, "memory":memory}
			generate_sampled_job_yaml(job_id=job, sleep_time=job_duration, workload=job_workload)#10)
			os.system('python3 -m starburst.drivers.submit_job --job-yaml ../../examples/sampled/sampled_job.yaml')	
		elif curr_time >= start_time + timeout:
			break

def generate_sampled_job_yaml(job_id=0, arrival_time=0, sleep_time=5, workload={"cpu": 0, "memory": 0, "gpu": 0}):
	""" Generalizes job submission to perform hyperparameter sweep """
	# TODO: Finalize design
	output = ""
	env = Environment(
		loader=FileSystemLoader("../../examples/sampled/templates"),
		autoescape=select_autoescape()
	)

	template = env.get_template("sampled_job.yaml.jinja")
	output += template.render({"job":str(job_id), "time":str(sleep_time)})

	set_limits = False

	for w in workload.values():
		print(w)
		if w > 0: 
			set_limits = True
			template = env.get_template("resource_limit.yaml.jinja")
			output += "\n" + template.render()
			break 
	
	for w in workload: 
		if workload[w] > 0: 
			template = env.get_template("{}_resource.yaml.jinja".format(w))
			output += "\n" + template.render({w: workload[w]})

	template = env.get_template("restart_limit.yaml.jinja")
	output += "\n" + template.render()

	job_yaml = open("../../examples/sampled/sampled_job.yaml", "w")
	job_yaml.write(output)
	job_yaml.close()
	return 

def pod_data():
	# Load the Kubernetes configuration from the default location
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")

	# Create a Kubernetes API client
	api = client.CoreV1Api()
	#scheduler = main_driver.SCHEDULER
	#scheduler = main_driver.starburst
	#api = scheduler.onprem_cluster_manager.core_v1

	# Get a list of all pods in the default namespace
	while True: 
		pod_list = api.list_namespaced_pod(namespace="default")
		print(pod_list)
		break

	return

def main():
	times = arrival_times(10)
	#start_scheduler(policy="fifo_wait")
	submit_jobs(times, 30)

if __name__ == '__main__':
    #main()
	pass