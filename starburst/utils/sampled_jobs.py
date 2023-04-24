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

def view_submitted_arrival_times(num_jobs = 100, batch_time=100): 
	batches = 5
	fig, axs = plt.subplots(nrows=5, ncols=1)
	#arrival_rates = [(i + 1) for i in range(10)]
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

class Config:
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)

def generate_jobs(hyperparameters): 
	jobs = {}
	hyperparameters = {
		"time_constrained": True,
		"random_seed": 42,
		"num_jobs": 100,
		"batch_time": 300,
		"wait_time": 0,
		"time_out": 5,
		"mean_sleep": 40,
		"arrival_rate": 1,
		"cpu_sizes": [1,2,4,8,16,32],
		"cpu_dist": [0, 0.2, 0.2, 0.2, 0.2], 
		"gpu_sizes": [1,2,4,8,16,32],
		"gpu_dist": [0, 0.2, 0.2, 0.2, 0.2],
		"memory_sizes": [100, 500, 1000, 50000],
		"memory_dict": [0.25, 0.25, 0.25, 0.25],
	}
	hp = Config(hyperparameters)
	jobs = {}
	jobs['hyperparameters'] = hyperparameters
	arrivals = []
	np.random.seed(hp.random_seed)
	job_index = 0
	submit_time = 0
	while True: 
		if hp.time_constrained and submit_time > hp.batch_time: 
			break 
		elif job_index >= hp.num_jobs: 
			break 
		job = {}
		job_index += 1
		np.random.seed(hp.random_seed) 
		submit_time += np.random.exponential(scale=hp.arrival_rate)
		np.random.seed(hp.random_seed) 
		job_duration = np.random.exponential(scale=hp.sleep_mean)
		np.random.seed(hp.random_seed) 
		cpus = int(np.random.choice(hp.cpu_sizes, p=hp.cpu_dist))
		np.random.seed(hp.random_seed) 
		gpus = min(0, int(np.random.exponential(scale=2)))
		np.random.seed(hp.random_seed) 
		memory = min(0, int(np.random.exponential(scale=50)))
		job['submit_time'] = submit_time
		job['job_duration'] = job_duration
		workload = {"gpu": gpus, "cpu":cpus, "memory":memory}
		job['workload'] = workload
		jobs[job_index] = job
		arrivals.append(job_index, submit_time)
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

def submit(jobs, arrivals):
	start_time = time.time()
	curr_time = time.time()
	job_index = 0
	total_jobs = len(jobs) - 1
	while True:
		curr_time = time.time()
		if job < total_jobs and curr_time > arrivals[job] + start_time:
			job = jobs[job_index]
			job_index += 1
			generate_sampled_job_yaml(job_id=job_index, sleep_time=job["duration"], workload=job['workload'])
			os.system('python3 -m starburst.drivers.submit_job --job-yaml ../../examples/sampled/sampled_job.yaml')	
		elif (arrivals != []) and (curr_time >= start_time + arrivals[-1] + jobs["hyperparameters"]["time_out"]): 
			print("Job Connection Time Out...")
			break
	return 

def execute(hyperparameters, repo, tag): 
	jobs, arrivals = generate_jobs(hyperparameters)
	save_jobs(jobs, repo, tag)
	submit(jobs, arrivals)

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
		#current_log_path = log_path + "job.json"
		with open(current_log_path, "w") as f:
			json.dump(job_data, f)
		'''
		with open("../logs/cpu/cpu_workload.json", "w") as f:
			json.dump(job_cpu_size, f)
		with open("../logs/sleep/sleep_time.json", "w") as f:
			json.dump(job_sleep_time, f)
		'''

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

	config.load_kube_config(context="gke_sky-burst_us-central1-c_starburst-cloud")
	cloud_api = client.CoreV1Api()

	cluster_apis = [onprem_api, cloud_api]

	for api in cluster_apis:
		# Delete all event logs in the cluster
		api.delete_collection_namespaced_event(
			namespace='default',  # Replace with the namespace where you want to delete the events
			body=client.V1DeleteOptions(),
		)
	
	print("Completed Clearing Logs...")

def start_logs(tag=None, batch_repo=None):
	event_data = job_logs.event_data_dict()
	job_logs.write_cluster_event_data(batch_repo=batch_repo, event_data=event_data, tag=tag)

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

def submit_sweep():
	sweep = generate_sweep()
	run_sweep(sweep)

def generate_sweep(): 
	hyperparameters = {
		"time_constrained": True,
		"random_seed": 42,
		"num_jobs": 100,
		"batch_time": 300,
		"wait_time": 0,
		"time_out": 5,
		"mean_sleep": 40,
		"arrival_rate": 1,
		"cpu_sizes": [1,2,4,8,16,32],
		"cpu_dist": [0, 0.2, 0.2, 0.2, 0.2], 
		"gpu_sizes": [1,2,4,8,16,32],
		"gpu_dist": [0, 0.2, 0.2, 0.2, 0.2],
		"memory_sizes": [100, 500, 1000, 50000],
		"memory_dict": [0.25, 0.25, 0.25, 0.25],
	}
	sweep = {hyperparameters}
	return sweep 

def run_sweep(sweep):
	sweep_timestamp =  str(int(datetime.now().timestamp()))
	for i in range(len(sweep)):
		hp = sweep[i] 
		run(hp, sweep_timestamp, i)
	return 0 

def run(hyperparameters, batch_repo, index):
	hp = Config(hyperparameters)
	q = mp.Queue()
	c1, c2 = mp.Pipe()
	p0 = mp.Process(target=driver.custom_start, args=(q, c2, 10000, 1, "gke_sky-burst_us-central1-c_starburst","gke_sky-burst_us-central1-c_starburst-cloud",hp.policy, hp.wait_time,))
	p0.start()
	
	while (c1.poll() == False) or (not (len(c1.recv()) == 0 and empty_cluster())):
		print("Cleaning Logs and Cluster....")
		time.sleep(1)
	clear_logs()
	
	tag = str(index)
	p1 = mp.Process(target=start_logs, args=(tag, batch_repo,))
	p2 = mp.Process(target=submit_jobs, args=(True, hp.batch_time, hp.num_jobs, hp.arrival_time, hp.sleep_mean, hp.time_out, False, True, batch_repo, {}, hp.random_seed, tag, hp.wait_time))
	p1.start()
	p2.start()

	while (p2.is_alive()) or (c1.poll() == False) or (not (len(c1.recv()) == 0 and empty_cluster())):
		print("Wait for Job to Complete....")
		time.sleep(1)

	p1.terminate()
	p0.terminate()
	return 0 

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

def main():
	#times = arrival_times(10000)#10)
	#start_scheduler(policy="fifo_wait")
	#submit_jobs(num_jobs=10000, timeout=10000000) #arrival_times=times
	#view_submitted_arrival_times()
	#view_real_arrival_times()

	# TODO: Remind users to only execute hyperparameter sweep through the main function, since mp package fails otherwise
	hyperparameter_sweep()
	return 

if __name__ == '__main__':
    main()
	#pass