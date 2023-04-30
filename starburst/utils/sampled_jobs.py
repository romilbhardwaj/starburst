import numpy as np 
import matplotlib.pyplot as plt
import os 
import time
import datetime
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from kubernetes import client, config
from datetime import datetime
from starburst.drivers import main_driver
import json
from kubernetes import client, config
import job_logs
import multiprocessing as mp
import starburst.drivers.main_driver as driver 
import subprocess
import copy
import itertools
from collections import defaultdict
from collections import OrderedDict
import atexit 

'''
Design Layout [DRAFT 2]

- Sweep Requirements -> Cluster -> Add Logs -> Parse Logs -> Analyze Sweep Requirements -> Plot
- Input Requirements -> Grid Search Values 

Design Layout [DRAFT 1]

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

DEFAULT_PARAMS = {
	"policy": "fifo_onprem_only",
	"time_constrained": True,
	"onprem_cluster_nodes": 4,
	"onprem_cpu_per_node": 8,
	"cloud_cluster_nodes": 4, 
	"cloud_cpu_per_node": 8,  
	"random_seed": 0,
	"num_jobs": 100,
	"batch_time": 300,
	"wait_time": 0,
	"time_out": 5,
	"mean_duration": 30,
	"arrival_rate": 1,
	"cpu_sizes": [1,2,4,8,16,32],
	"cpu_dist": [0, 0.2, 0.2, 0.2, 0.2, 0.2], 
	"gpu_sizes": [1,2,4,8,16,32],
	"gpu_dist": [0, 0.2, 0.2, 0.2, 0.2, 0.2],
	"memory_sizes": [100, 500, 1000, 50000],
	"memory_dict": [0.25, 0.25, 0.25, 0.25],
}

"""
Core Dictionaries
- Job Dictionary
- TODO: Sweep Dictionary 

Core Functions
- Sweep 
	- Generate_Sweep()
"""

class Config:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

def generate_jobs(hyperparameters): 
	jobs = {}
	hp = Config(hyperparameters)
	jobs = {}
	jobs['hyperparameters'] = hyperparameters
	arrivals = []
	np.random.seed(hp.random_seed)

	job_index = 0#1
	submit_time = 0
	while True:
		if hp.time_constrained and submit_time > hp.batch_time:
			break
		elif job_index >= hp.num_jobs:
			break
		job = {}
		submit_time += np.random.exponential(scale=hp.arrival_rate)
		job_duration = np.random.exponential(scale=hp.mean_duration)
		cpus = int(np.random.choice(hp.cpu_sizes, p=hp.cpu_dist))
		gpus = min(0, int(np.random.exponential(scale=2)))
		memory = min(0, int(np.random.exponential(scale=50)))
		job['submit_time'] = submit_time
		job['scheduler_submit_time'] = None
		job['job_duration'] = job_duration
		workload = {"gpu": gpus, "cpu":cpus, "memory":memory}
		job['workload'] = workload
		jobs[job_index] = job
		arrivals.append((job_index, submit_time))
		job_index += 1
	return jobs, arrivals

def save_jobs(jobs, repo, tag):
	log_path = "../logs/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path = "../logs/archive/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path += repo + "/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path += "jobs/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	current_log_path = log_path + tag + ".json"
	with open(current_log_path, "w") as f:
		json.dump(jobs, f)

def submit(jobs={}, arrivals=[], timestamp=None, index=None):
	start_time = time.time()
	curr_time = time.time()
	job_index = 0 #1
	total_jobs = len(arrivals) #len(jobs)
	submit_times = {}
	
	while True:
		curr_time = time.time()
		#print(str(job_index) + " " + str(total_jobs) +  " " + str(curr_time) + " " + str(arrivals[job_index]) + " " + str(start_time))
		#print(arrivals)
		#print(job_index)
		if job_index < total_jobs and curr_time > arrivals[job_index][1] + start_time:
			job = jobs[job_index]
			generate_sampled_job_yaml(job_id=job_index, sleep_time=job["job_duration"], workload=job['workload'])
			#os.system('python3 -m starburst.drivers.submit_job --job-yaml ../../examples/sampled/sampled_job.yaml')
			subprocess.run(['python3', '-m', 'starburst.drivers.submit_job', '--job-yaml', '../../examples/sampled/sampled_job.yaml'])
			submit_time = time.time()

			#if job_index not in submit_times: 
			#	submit_times[job_index] = []
			submit_times[job_index] = submit_time

			job_index += 1
		#TODO: Improve stop condition -- wait until last job completes
		
		if job_index >= total_jobs: 
			break

		'''
		elif (arrivals != []) and (curr_time >= start_time + arrivals[-1][1] + jobs["hyperparameters"]["time_out"]): 
			print("Job Connection Time Out...")
			break
		'''
	
	trial_data_path = "../logs/archive/" + str(timestamp) + "/jobs/" + str(index) + ".json"
	job_data = {}
	with open(trial_data_path, "r") as f: #"../logs/event_data.json", "r") as f:
		job_data = json.load(f)

	for i in range(len(arrivals)):
		#job_data[str(i)]['submit_time'] = submit_times[i]
		# TODO: add scheduler_submit_time value in addition to submit_time 
		job_data[str(i)]['scheduler_submit_time'] = submit_times[i] 

	with open(trial_data_path, "w") as f: #"../logs/event_data.json", "r") as f:
		#job_data = json.dump(f)
		json.dump(job_data, f)

	return 

def execute(hyperparameters, repo, tag): 
	jobs, arrivals = generate_jobs(hyperparameters)
	save_jobs(jobs, repo, tag)
	submit(jobs, arrivals)

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
	print("Started Clearing Logs...")

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()
	onprem_api_batch = client.BatchV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()
	cloud_api_batch = client.BatchV1Api()

	cluster_apis = [(onprem_api, onprem_api_batch), (cloud_api, cloud_api_batch)]

	for apis in cluster_apis:
		api, api_batch = apis
		# Delete all event logs in the cluster
		api.delete_collection_namespaced_event(
			namespace='default',  # Replace with the namespace where you want to delete the events
			body=client.V1DeleteOptions(),
		)

		jobs_list = api_batch.list_namespaced_job(namespace='default')
		for job in jobs_list.items:
			api_batch.delete_namespaced_job(
				name=job.metadata.name, 
				namespace='default', 
				body=client.V1DeleteOptions(
					propagation_policy='Foreground', 
					grace_period_seconds=0
					)
			)
	
	print("Completed Clearing Logs...")

def log(tag=None, batch_repo=None, loop=True):
	event_data = job_logs.event_data_dict()
	job_logs.write_cluster_event_data(batch_repo=batch_repo, event_data=event_data, tag=tag, loop=loop)

def empty_cluster():
	'''
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()

	cluster_apis = [onprem_api, cloud_api]
	namespace = "default"
	'''
	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst")
	onprem_api = client.CoreV1Api()
	onprem_api_batch = client.BatchV1Api()

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()
	cloud_api_batch = client.BatchV1Api()

	cluster_apis = [(onprem_api, onprem_api_batch), (cloud_api, cloud_api_batch)]
	namespace="default"

	for apis in cluster_apis:
		api, api_batch = apis
		pods = api.list_namespaced_pod(namespace)
		running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
		if running_pods:
			return False

		jobs = api_batch.list_job_for_all_namespaces()
		running_jobs = [job.status.succeeded for job in jobs.items if job.status.succeeded != 1] # if pod.status.phase == "Running"]
		#print(running_jobs)
		#time.sleep(1000)
		if running_jobs:
			return False 

		"""
		'status': {'active': None,
		'completed_indexes': None,
		'completion_time': datetime.datetime(2023, 4, 30, 7, 3, 35, tzinfo=tzutc()),
		'conditions': [{'last_probe_time': datetime.datetime(2023, 4, 30, 7, 3, 35, tzinfo=tzutc()),
						'last_transition_time': datetime.datetime(2023, 4, 30, 7, 3, 35, tzinfo=tzutc()),
						'message': None,
						'reason': None,
						'status': 'True',
						'type': 'Complete'}],
		'failed': None,
		'ready': 0,
		'start_time': datetime.datetime(2023, 4, 30, 7, 3, 29, tzinfo=tzutc()),
		'succeeded': 1,
		'uncounted_terminated_pods': {'failed': None, 'succeeded': None}}}
		"""

	'''
	for api in cluster_apis:
		pods = api.list_namespaced_pod(namespace)
		running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
		if running_pods:
			return False
	'''
	
	'''
	for api in cluster_apis:
		jobs = api.list_job_for_all_namespaces()
		running_jobs = [job.status for job in jobs.items]# if pod.status.phase == "Running"]
		print(running_jobs)
		time.sleep(1000)
		if running_jobs:
			return False
	'''

	return True 

def run(hyperparameters, batch_repo, index):
	hp = Config(hyperparameters)
	jobs, arrivals = generate_jobs(hyperparameters=hyperparameters)
	save_jobs(jobs=jobs, repo=batch_repo, tag=index)
	c1, c2 = mp.Pipe()
	grpc_port = 10000 #50051
	p0 = mp.Process(target=driver.custom_start, args=(None, c2, grpc_port, 1, "gke_sky-burst_us-central1-c_starburst","gke_sky-burst_us-central1-c_starburst-cloud",hp.policy, hp.wait_time, jobs))
	p0.start()
	
	clear_logs()
	while (c1.poll() == False) or (not (len(c1.recv()) == 0 and empty_cluster())):
		print("Cleaning Logs and Cluster....")
		print("Connected: " + str(c1.poll()) + " - Empty Job Queue: " + str(len(c1.recv()) == 0) + " - Empty Cluster: " + str(empty_cluster()) )
		time.sleep(1)
	clear_logs()
	
	tag = str(index)
	p1 = mp.Process(target=log, args=(tag, batch_repo, True))
	p2 = mp.Process(target=submit, args=(jobs, arrivals, batch_repo, index))
	p1.start()
	p2.start()

	while (p2.is_alive()) or (c1.poll() == False) or (not (len(c1.recv()) == 0 and empty_cluster())):
		print("Wait for Job to Complete....")
		print("p2 alive status: " + str(p2.is_alive()))
		print("Job Queue: " + str(c1.recv()))
		time.sleep(1)

	#atexit.register(func=log, args=(tag, batch_repo, False)
	# TODO: Ensure p2 dies only after all submitted jobs have completed
	# TODO: Ensure p1 only dies after all p2 jobs have been properly logged -- force it to log one last time before closing 

	p1.terminate()

	p1 = mp.Process(target=log, args=(tag, batch_repo, False))
	p1.start()
	while (p1.is_alive()):
		print("Saving last logs....")
		print("p1 alive status: " + str(p1.is_alive()))
		time.sleep(1)

	p0.terminate()
	
	return 0 

def run_sweep(sweep={}):#, fixed_values=OrderedDict(), varying_values=OrderedDict()):
	sweep_timestamp =  str(int(datetime.now().timestamp()))
	sweep_dir = "../logs/archive/" + sweep_timestamp + "/"
	if not os.path.exists(sweep_dir):
		os.mkdir(sweep_dir)
	sweep_path = sweep_dir + "sweep.json"

	with open(sweep_path, "w") as f:
		json.dump(sweep, f)

	for i in range(len(sweep) - 2):
		hp = sweep[i]
		run(hp, sweep_timestamp, str(i))

	return sweep_timestamp

def submit_sweep(fixed_values=OrderedDict(), varying_values=OrderedDict()):
	sweep = generate_sweep(fixed_values=fixed_values, varying_values=varying_values)
	#save_sweep(sweep=sweep, fixed_values=fixed_values, varying_values=varying_values)
	time_stamp = run_sweep(sweep)
	return time_stamp

def plot_sweep(sweep_timestamp=0, fixed_values=OrderedDict(), varying_values=OrderedDict()):
	print("Analyzing and plotting data...")
	job_logs.analyze_sweep(event_number=sweep_timestamp)#, fixed_values=fixed_values, varying_values=varying_values)
	print("Plotting complete...")
	return 

def generate_sweep(fixed_values=OrderedDict(), varying_values=OrderedDict()): 
	"""
	Takes specified fixed values and generates grid of hyperparameters based on varying values 
	"""
	# TODO: Integrate hpo tool (e.g. optuna)
	# TODO: Specify grid search values, then plot them

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
	sweep={}
	sweep["fixed_values"] = fixed_values
	sweep["varying_values"] = varying_values
	# DEFAULT VALUES
	hyperparameters = copy.deepcopy(DEFAULT_PARAMS)
	
	# FIXED VALUES
	for key, value in fixed_values.items(): 
		hyperparameters[key] = value

	# VARYING VALUES
	# TODO: Create cartesian product of values then iterate through the values and map them to a job index

	keys = []
	values = []
	for key, value in varying_values.items():
		keys.append(key)
		values.append(value)

	#values = values[::-1]

	grid_search = itertools.product(*values)
	
	for trial_index, trial in enumerate(grid_search):
		for key_index, key in enumerate(keys):
			hyperparameters[key] = trial[key_index]
		sweep[trial_index] = copy.deepcopy(hyperparameters)

	'''
	# SWEEP 1
	hyperparameters["policy"] = "fifo_wait"

	for cpu_dist in cpu_dists: 
		for w in wait_times:
			for a in arrival_rates:
				hyperparameters["cpu_dist"] = cpu_dist
				hyperparameters["arrival_rate"] = a
				hyperparameters["wait_time"] = w
				sweep[index] = copy.deepcopy(hyperparameters)
				index += 1
	'''

	'''
	# SWEEP 2
	hyperparameters["policy"] = "fifo_onprem_only"

	for cpu_dist in cpu_dists: 
		for a in arrival_rates:
			hyperparameters["cpu_dist"] = cpu_dist
			hyperparameters["arrival_rate"] = a
			sweep[index] = copy.deepcopy(hyperparameters)
			index += 1			
	'''

	'''
	# SWEEP 3
	hyperparameters["policy"] = "time_estimator"

	for cpu_dist in cpu_dists: 
		for a in arrival_rates:
			hyperparameters["arrival_rate"] = a
			hyperparameters["wait_time"] = w
			sweep[index] = hyperparameters
			index += 1
	'''
	
	return sweep

def generate_interval(min=0, max=10, intervals=10):
	return np.linspace(min, max, num=intervals+1).tolist()[1:]

def main():
	"""
	Note: Only execute sweep through the main function, since mp package fails otherwise
	"""
	hyperparameters = copy.deepcopy(DEFAULT_PARAMS)
	
	fixed_values = {
		"num_jobs": 5,
		"batch_time": 5, 
		"mean_duration": 1,
		"policy": "fifo_wait",
		"cpu_sizes":[1, 2, 4],
		"cpu_dist": [0.2, 0.4, 0.4]
	}

	fixed_values = OrderedDict(fixed_values)
	
	"""Varying values from outer most to inner most loop"""
	varying_values = {	
		"cpu_dist": [[0.2, 0.4, 0.4], [0, 0.5, 0.5], [0, 0, 1]],	
		"wait_time": generate_interval(0, 10, 3),
		"arrival_rate": generate_interval(0, hyperparameters["mean_duration"] * (1 / (hyperparameters["onprem_cluster_nodes"] * hyperparameters["onprem_cpu_per_node"])) * 4, 3)[1:],
	}
	varying_values = OrderedDict(varying_values)
	submit_sweep(fixed_values=fixed_values, varying_values=varying_values)
	#sweep = generate_sweep(fixed_values=fixed_values, varying_values=varying_values)
	#print(sweep)
	return 

if __name__ == '__main__':
    main()
	#pass

"""
MISC FUNCTIONS
"""

def start_scheduler(policy="fifo_onprem_only", onprem_cluster="gke_sky-burst_us-central1-c_starburst", cloud_cluster="gke_sky-burst_us-central1-c_starburst-cloud"):
	os.system('python3 -m starburst.drivers.main_driver --policy {} --onprem_k8s_cluster_name {} --cloud_k8s_cluster_name {}'.format(policy, onprem_cluster, cloud_cluster))
	#subprocess.run(['python3', '-m', 'starburst.drivers.main_driver' '--policy', policy, '--onprem_k8s_cluster_name', onprem_cluster,'--cloud_k8s_cluster_name', cloud_cluster])
	#python3 -m starburst.drivers.main_driver --policy fifo_onprem_only --onprem_k8s_cluster_name gke_sky-burst_us-central1-c_starburst --cloud_k8s_cluster_name gke_sky-burst_us-central1-c_starburst-cloud
	#starburst, driver.custom_start(onprem_k8s_cluster_name=onprem_cluster, cloud_k8s_cluster_name=cloud_cluster, policy=policy)
	return 

def view_submitted_arrival_times(num_jobs = 100, batch_time=100): 
	batches = 5
	fig, axs = plt.subplots(nrows=5, ncols=1)
	arrival_rates = np.linspace(0, 8, num=batches+1).tolist()[1:]
	
	arrival_times = []
	for i in range(len(arrival_rates)):
		ar = arrival_rates[i]
		times = submit_jobs(time_constrained=True, batch_time=batch_time, arrival_rate=ar, sleep_mean=10, submit=False)
		arrival_times.append(times)
		axs[i].eventplot(times)
		axs[i].set_ylabel(str(ar))
		axs[i].set_xlim((0, 800))
		axs[i].set_yticks([])

	plt.show()

def hyperparameter_sweep(batch_time=500, num_jobs=100, sleep_mean=30, timeout=10, policy="fifo_wait"):
	# TODO: Vary and log jobs with different arrival rates
	arrival_intervals = 5
	waiting_intervals = 3
	arrival_rates = np.linspace(0, 5, num=arrival_intervals+1).tolist()[1:]
	waiting_times = np.linspace(0, 30, num=waiting_intervals+1).tolist()

	#job_data = {}
	batch_repo = str(int(datetime.now().timestamp()))

	for wait in waiting_times:  
		q = mp.Queue()
		c1, c2 = mp.Pipe()
		p0 = mp.Process(target=driver.custom_start, args=(q, c2, 10000, 1, "gke_sky-burst_us-central1-c_starburst","gke_sky-burst_us-central1-c_starburst-cloud",policy, wait,))

		p0.start()
		# TODO: Vary wait_time (i.e. time_out for each arrival_rate) 
		# TODO: Save the same job resource requirements when regenerating them for each wait_time value
		# TODO: Determine better design than restarting scheduler for each new wait_time value
		# TODO: Save job submission data as an array -- [[time, JobObject], ..., [time, JobObject]]
		for ar in arrival_rates:
			#batch_job
			while (c1.poll() == False) or (not (len(c1.recv()) == 0 and empty_cluster())):
				print("Cleaning Logs and Cluster....")
				# TODO: Figure out why the function pauses after this print statement
				# TODO: manually delete any remaining jobs 
				print("Connection Value: " + str(c1.recv()))
				time.sleep(1)
			clear_logs()
			
			tag = str(wait) + "_" + str(ar)
			p1 = mp.Process(target=start_logs, args=(tag, batch_repo,))
			p2 = mp.Process(target=submit_jobs, args=(True, batch_time, num_jobs, ar, sleep_mean, timeout, False, True, batch_repo, {}, 42, tag, wait))
			p1.start()
			p2.start()

			while (p2.is_alive()) or (c1.poll() == False) or (not (len(c1.recv()) == 0 and empty_cluster())):
				print("Wait for Job to Cxomplete....")
				print("p2 alive status: " + str(p2.is_alive()))
				print("Job Queue: " + str(c1.recv()))
				# TODO: manually delete any remaining jobs 
				time.sleep(1)

			p1.terminate()
			# TODO: only start next arrival rate one the queue is empty again
			# TODO: check how to find if starburst queue is empty
			# TODO: check when not more jobs being processed in the cluster
 
		p0.terminate()
	return 0

def submit_jobs(time_constrained = True, batch_time=10, num_jobs=10, arrival_rate=0.5, sleep_mean=10, timeout=5, plot_arrival_times=False, submit=True, batch_repo=None, hyperparameters={}, random_seed=0, tag="job", wait_time=0): #arrival_times, 
	""" Submits a a default job for each time stamp of the inputed arrival times """
	hyperparameters = {
		"random_seed": 42,
		"num_jobs": num_jobs, #0,
		"batch_time": batch_time,
		"wait_time": wait_time,
		"time_out": timeout, #0,
		"mean_sleep": sleep_mean, #0,
		"arrival_rate": arrival_rate, #0, 
		"cpu_sizes": [1,2,4,8,16,32],
		"cpu_dist": [0, 0.2, 0.2, 0.2, 0.2], 
		"gpu_sizes": [1,2,4,8,16,32],
		"gpu_dist": [0, 0.2, 0.2, 0.2, 0.2],
		"memory_sizes": [100, 500, 1000, 50000],
		"memory_dict": [0.25, 0.25, 0.25, 0.25],
	}
	# TODO: Set random seed, to allow same values given the variables
	np.random.seed(random_seed)

	#batch_times = []
	total_jobs = num_jobs #len(arrival_times)
	job = 0

	cpu_size = [1, 2, 4]
	cpu_dist = [0.2, 0.4, 0.4]
	hyperparameters['cpu_sizes'] = cpu_size
	hyperparameters['cpu_dist'] = cpu_dist

	'''
	submit_time = 0
	arrival_times = []
	print(arrival_rate)
	for i in range(num_jobs):
		submit_time += np.random.exponential(scale=arrival_rate)#0.5)
		arrival_times.append(submit_time)
	'''
	if time_constrained: 
		submit_time = 0
		submitted_jobs = 0
		arrival_times = []
		while submit_time <= batch_time: 
			# TODO: Reset seed before each call to np.random.x()
			np.random.seed(random_seed) 
			submit_time += np.random.exponential(scale=arrival_rate)#0.5)
			arrival_times.append(submit_time)
			submitted_jobs += 1 
	else: 
		submit_time = 0
		arrival_times = []
		#print(arrival_rate)
		for i in range(num_jobs):
			submit_time += np.random.exponential(scale=arrival_rate)#0.5)
			arrival_times.append(submit_time)
	
	if not submit: 
		return arrival_times	

	if plot_arrival_times: 
		plt.eventplot(arrival_times)
		plt.savefig('../plots/arrival_times.png')

	job_cpu_size = {}
	job_sleep_time = {}
	#job_data = {}
	# TODO: Verify hyperparamters gets parsed successfully by read_submission_data()
	job_data = {'hyperparameters': hyperparameters}

	log_path = "../logs/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path = "../logs/archive/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path += batch_repo + "/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path += "jobs/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	
	#current_log_path = log_path + str(arrival_rate) + ".json"
	current_log_path = log_path + tag + ".json"


	start_time = time.time()
	curr_time = time.time()
	submitted_jobs = 0
	while True:
	#while curr_time <= start_time + batch_time:  
		curr_time = time.time()
		#print("job submissions: " + str(start_time) + " " + str(curr_time) + " " + str(timeout))
		if job < total_jobs and curr_time > arrival_times[job] + start_time:
			job_values = {}
			

			job += 1
			#job_values["id"] = job
			#print(job)
			job_duration = np.random.exponential(scale=sleep_mean)#60) #np.random.normal(10, 3) 
			job_values["duration"] = job_duration
			#cpu_index = int(np.random.uniform(low=0, high=3)) #0.2 #min(0, int(np.random.exponential(scale=3)))
			#cpu_index = np.random.choice(cpu_size, p=cpu_dist)
			
			cpus = int(np.random.choice(cpu_size, p=cpu_dist)) #cpu_size[cpu_index]
			job_values['cpus'] = cpus
			gpus = min(0, int(np.random.exponential(scale=2)))
			job_values['gpus'] = gpus
			memory = min(0, int(np.random.exponential(scale=50)))
			job_values['memory'] = memory
			job_cpu_size[job] = cpus
			job_sleep_time[job] = job_duration
			job_workload = {"gpu": gpus, "cpu":cpus, "memory":memory}
			generate_sampled_job_yaml(job_id=job, sleep_time=job_duration, workload=job_workload)#10)
			submit_time = int(datetime.now().timestamp())
			job_values['submit_time'] = submit_time

			job_data[job] = job_values
			os.system('python3 -m starburst.drivers.submit_job --job-yaml ../../examples/sampled/sampled_job.yaml')	
		elif (arrival_times != []) and (curr_time >= start_time + arrival_times[-1] + timeout): 
			print("Time Out...")
			break
		'''
		elif curr_time >= start_time + timeout:
			print("Time Out...")
			break
		'''

		# TODO: Save job hyperparameters directly into job events metadata	
		with open(current_log_path, "w") as f:
			json.dump(job_data, f)