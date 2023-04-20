import numpy as np 
import matplotlib.pyplot as plt
import os 
import time
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from kubernetes import client, config
from datetime import datetime
from starburst.drivers import main_driver
import json
from kubernetes import client, config
import job_logs
import multiprocessing as mp
import starburst.drivers.main_driver as driver 

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

def start_scheduler(policy="fifo_onprem_only", onprem_cluster="gke_sky-burst_us-central1-c_starburst", cloud_cluster="gke_sky-burst_us-central1-c_starburst-cloud"):
	os.system('python3 -m starburst.drivers.main_driver --policy {} --onprem_k8s_cluster_name {} --cloud_k8s_cluster_name {}'.format(policy, onprem_cluster, cloud_cluster))	
	#starburst, driver.custom_start(onprem_k8s_cluster_name=onprem_cluster, cloud_k8s_cluster_name=cloud_cluster, policy=policy)
	return 

def submit_jobs(num_jobs=10, arrival_rate=0.5, sleep_mean=10, timeout=60, plot_arrival_times=False): #arrival_times, 
	""" Submits a a default job for each time stamp of the inputed arrival times """

	total_jobs = num_jobs #len(arrival_times)
	start_time = time.time()
	job = 0

	cpu_size = [1, 2, 4]
	cpu_dist = [0.2, 0.4, 0.4]

	curr_time = 0
	arrival_times = []
	for i in range(num_jobs):
		curr_time += np.random.exponential(scale=arrival_rate)#0.5)
		arrival_times.append(curr_time)

	if plot_arrival_times: 
		plt.eventplot(arrival_times)
		plt.savefig('../plots/arrival_times.png')

	job_cpu_size = {}
	job_sleep_time = {}

	while True: 
		curr_time = time.time()
		if job < total_jobs and curr_time > arrival_times[job] + start_time: 
			job += 1
			#print(job)
			job_duration = np.random.exponential(scale=sleep_mean)#60) #np.random.normal(10, 3) 
			#cpu_index = int(np.random.uniform(low=0, high=3)) #0.2 #min(0, int(np.random.exponential(scale=3)))
			#cpu_index = np.random.choice(cpu_size, p=cpu_dist)
			cpus = int(np.random.choice(cpu_size, p=cpu_dist)) #cpu_size[cpu_index]
			gpus = min(0, int(np.random.exponential(scale=2)))
			memory = min(0, int(np.random.exponential(scale=50)))
			job_cpu_size[job] = cpus
			job_sleep_time[job] = job_duration
			job_workload = {"gpu": gpus, "cpu":cpus, "memory":memory}
			generate_sampled_job_yaml(job_id=job, sleep_time=job_duration, workload=job_workload)#10)
			os.system('python3 -m starburst.drivers.submit_job --job-yaml ../../examples/sampled/sampled_job.yaml')	
		elif curr_time >= start_time + timeout:
			break
		with open("../logs/cpu/cpu_workload.json", "w") as f:
			json.dump(job_cpu_size, f)
		with open("../logs/sleep/sleep_time.json", "w") as f:
			json.dump(job_sleep_time, f)

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

def clear_logs():
	# TODO: Automate log cleaning
	# TODO: Remove logs and both onprem and cloud cluster

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()

	cluster_apis = [onprem_api, cloud_api]

	for api in cluster_apis:
		# Delete all event logs in the cluster
		api.delete_collection_namespaced_event(
			namespace='default',  # Replace with the namespace where you want to delete the events
			body=client.V1DeleteOptions(),
		)

def start_logs(tag=None):
	# TODO: Run job_logs.write_cluster_event_data()
	#print('reached')
	event_data = job_logs.event_data_dict()
	job_logs.write_cluster_event_data(event_data=event_data, tag=tag)

def test():
	print("hello")

def empty_cluster():
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()

	cluster_apis = [onprem_api, cloud_api]
	namespace = "default"

	for api in cluster_apis:
		pods = api.list_namespaced_pod(namespace)
		running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
		if running_pods: 
			return False 
	
	return True 

def hyperparameter_sweep():
	# TODO: Vary and log jobs with different arrival rates
	arrival_rates = [0.1, 0.2, 0.3, 0.4, 0.5]
	driver.custom_start()
	starburst, event_sources, event_loop = driver.custom_start(onprem_k8s_cluster_name="gke_sky-burst_us-central1-c_starburst",  cloud_k8s_cluster_name="gke_sky-burst_us-central1-c_starburst-cloud", policy="fifo_wait")
	#p0 = mp.Process(target=start_scheduler, args=("fifo_wait",))
	#driver.start_events(starburst, event_sources, event_loop)
	p0 = mp.Process(target=driver.custom_start, args=(10000, 1, "gke_sky-burst_us-central1-c_starburst","gke_sky-burst_us-central1-c_starburst-cloud","fifo_wait",))
	#p0 = mp.Process(target=driver.start_events, args=(starburst, event_sources, event_loop,))
	#p2 = mp.Process(target=submit_jobs, args=(100, 0.5, 300, False))#(num_jobs=100, timeout=300, arrival_rate=ar,))
	p0.start()

	#p2.start()
	#print("p2 reached")
	#p0.join()
	
	#p2.join()
	#return
	#print("p0 joined")

	#print("reached")
	for ar in arrival_rates:
		starburst = driver.starburst_scheduler
		print(starburst)
		while not (len(starburst.job_queues) == 0 and empty_cluster()): 
			print("Waiting....")
			time.sleep(1)
		
		p1 = mp.Process(target=start_logs, args=("arrival_rate_" + str(ar),))
		p2 = mp.Process(target=submit_jobs, args=(10, ar, 10, 30, False))
		p3 = mp.Process(target=clear_logs)
		p3.start()
		p3.join()
		
		p1.start()
		time.sleep(5)
		p2.start()
		p2.join()
		time.sleep(5)
		p1.terminate()
		#clear_logs()
		
		time.sleep(5)

		# TODO: only start next arrival rate one the queue is empty again
		# TODO: check how to find if starburst queue is empty
		# TODO: check when not more jobs being processed in the cluster 
	
	p0.terminate()

	return 0 

def main():
	#times = arrival_times(10000)#10)
	#start_scheduler(policy="fifo_wait")
	#submit_jobs(num_jobs=10000, timeout=10000000) #arrival_times=times
	hyperparameter_sweep()

if __name__ == '__main__':
    main()
	#pass


'''
def arrival_times(num_jobs = 100, arrival_rate = 0.5):
	""" Generates arrival times of jobs into an array and plots values """
	curr_time = 0
	times = []
	for i in range(num_jobs):
		curr_time += np.random.exponential(scale=arrival_rate)#0.5)
		times.append(curr_time)
	plt.eventplot(times)
	plt.savefig('../plots/arrival_times.png')
	return times
'''