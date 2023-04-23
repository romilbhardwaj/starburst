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
	#for ar in arrival_rates: 
	for i in range(len(arrival_rates)):
		ar = arrival_rates[i]
		#times = submit_jobs(num_jobs=num_jobs, arrival_rate=ar, sleep_mean=10, submit=False)
		times = submit_jobs(time_constrained=True, batch_time=batch_time, arrival_rate=ar, sleep_mean=10, submit=False)
		arrival_times.append(times)
		axs[i].eventplot(times)
		axs[i].set_ylabel(str(ar))
		axs[i].set_xlim((0, 800))#100))#times[-1]))
		axs[i].set_yticks([])

	plt.show()
	#print(arrival_times)
'''
def view_real_arrival_times_redacted(path=None):
	
	costs = {}
	if path: 
		files = os.listdir(path)
		fig, axs = plt.subplots(nrows=len(files), ncols=1)
		# Iterate over the files and check if they have the ".json" extension
		#for file in files:
		for i in range(len(files)):
			file = files[i]
			log_path = path + file
			print(log_path)
			cluster_data = job_logs.read_cluster_event_data(cluster_log_path=log_path)
			jobs, num_nodes = job_logs.parse_event_logs(cluster_data)#data)

			submission_data = job_logs.read_submission_data(submission_log_path=log_path)

			#cost = job_logs.cloud_cost(jobs=jobs, num_nodes=num_nodes)
			#costs[file] = cost
			plot_dir = "../logs/archive/plots/"
			if not os.path.exists(plot_dir):
				#os.mkdir(archive_path)
				os.mkdir(plot_dir)

			plot_path = "../logs/archive/plots/" + file[:-5] + ".png"
			print(plot_path)
			job_logs.plot_job_intervals(jobs, num_nodes, save=True, path=plot_path, subplt=axs, plt_index=i, tag=str(file))
			
			#job_logs.plot_job_intervals(jobs, num_nodes)
			
			#if file.endswith(".json"):
			#	log_path = log_path + str(file)
			#	break 
	#return costs
	plt.show()

	return 
'''

def submit_jobs(time_constrained = True, batch_time=10, num_jobs=10, arrival_rate=0.5, sleep_mean=10, timeout=5, plot_arrival_times=False, submit=True, batch_repo=None, hyperparameters={}): #arrival_times, 
	""" Submits a a default job for each time stamp of the inputed arrival times """
	hyperparameters = {
		"num_jobs": 0,
		"time_out": 0,
		"mean_sleep": 0,
		"arrival_rate": 0, 
		"cpu_sizes": [1,2,4,8,16,32],
		"cpu_dist": [0, 0.2, 0.2, 0.2, 0.2], 
		"gpu_sizes": [1,2,4,8,16,32],
		"gpu_dist": [0, 0.2, 0.2, 0.2, 0.2],
		"memory_sizes": [100, 500, 1000, 50000],
		"memory_dict": [0.25, 0.25, 0.25, 0.25],
	}

	#batch_times = []
	total_jobs = num_jobs #len(arrival_times)
	job = 0

	cpu_size = [1, 2, 4]
	cpu_dist = [0.2, 0.4, 0.4]

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
	job_data = {}

	log_path = "../logs/archive/jobs/"
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	log_path += batch_repo + "/"#str(int(datetime.now().timestamp())) + '/'
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	current_log_path = log_path + str(arrival_rate) + ".json" #"job.json"


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
			job_data[job] = job_values
			submit_time = int(datetime.now().timestamp())
			job_values['submit_time'] = submit_time
			os.system('python3 -m starburst.drivers.submit_job --job-yaml ../../examples/sampled/sampled_job.yaml')	
		elif (arrival_times != []) and (curr_time >= start_time + arrival_times[-1] + timeout): 
			print("Time Out...")
			break
		'''
		elif curr_time >= start_time + timeout:
			print("Time Out...")
			break
		'''
		
		#current_log_path = log_path + "job.json"
		with open(current_log_path, "w") as f:
			json.dump(job_data, f)
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
	# TODO: Run job_logs.write_cluster_event_data()
	#print('reached')
	event_data = job_logs.event_data_dict()
	job_logs.write_cluster_event_data(batch_repo=batch_repo, event_data=event_data, tag=tag)

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

def hyperparameter_sweep(batch_time=500, num_jobs=100, sleep_mean=30, timeout=10,):
	# TODO: Vary and log jobs with different arrival rates
	batches = 5
	arrival_rates = np.linspace(0, 8, num=batches+1).tolist()[1:]
	#arrival_rates = [0.1, 0.2, 0.3, 0.4, 0.5]
	#driver.custom_start()
	q = mp.Queue()
	c1, c2 = mp.Pipe()
	#starburst, event_sources, event_loop = driver.custom_start(onprem_k8s_cluster_name="gke_sky-burst_us-central1-c_starburst",  cloud_k8s_cluster_name="gke_sky-burst_us-central1-c_starburst-cloud", policy="fifo_wait")
	#p0 = mp.Process(target=start_scheduler, args=("fifo_wait",))
	#driver.start_events(starburst, event_sources, event_loop)
	p0 = mp.Process(target=driver.custom_start, args=(q, c2, 10000, 1, "gke_sky-burst_us-central1-c_starburst","gke_sky-burst_us-central1-c_starburst-cloud","fifo_wait",))
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
	batch_repo = str(int(datetime.now().timestamp()))

	for ar in arrival_rates:
		#starburst = driver.starburst_scheduler
		#print(starburst)
		print("Job Queue:")
		#print(q.get())
		#clear_logs()
		# TODO: Make sure mp Queue is not empty 
		#while not (len(q.get()) == 0 and empty_cluster()):
		#if not q.empty():
		#jobQueue = c1.recv()
		while (c1.poll() == False) or (not (len(c1.recv()) == 0 and empty_cluster())):
		#while q.empty() or (not (len(q[-1]) == 0 and empty_cluster())): 
			print("Cleaning Logs and Cluster....")
			# TODO: Figure out why the function pauses after this print statement
			#clear_logs()
			# TODO: manually delete any remaining jobs 
			print("Connection Value: " + str(c1.recv()))
			time.sleep(1)
		clear_logs()
		
		#p1 = mp.Process(target=start_logs, args=("arrival_rate_" + str(ar), batch_repo))
		p1 = mp.Process(target=start_logs, args=(str(ar), batch_repo))
		p2 = mp.Process(target=submit_jobs, args=(True, batch_time, num_jobs, ar, sleep_mean, timeout, False, True, batch_repo, {}))
		#p3 = mp.Process(target=clear_logs)
		#p3.start()
		#p3.join()
		
		p1.start()#5)#timeout=5)
		#time.sleep(5)
		p2.start()

		#p2.join()
		#time.sleep(5)
		#clear_logs()
		
		#i = 0
		#while i < 100: 
		#	print("Current Queue " + str(i) )
		#	i += 1
		#print(q.get())

		#while c1.poll():
		#	print(c1.poll())
		#	print(c1.recv())

		#while not (len(q.get()) == 0 and empty_cluster()): 
		#while not c1.recv() or (not (len(c1.recv()) == 0 and empty_cluster())):
		#time.sleep(5)
		#p2.join()
		#p1.join()
		while (p2.is_alive()) or (c1.poll() == False) or (not (len(c1.recv()) == 0 and empty_cluster())):
			print("Wait for Job to Cxomplete....")
			print("p2 alive status: " + str(p2.is_alive()))
			print("Job Queue: " + str(c1.recv()))
			#clear_logs()
			# TODO: manually delete any remaining jobs 
			time.sleep(1)

		#p2.terminate()
		p1.terminate()

		#time.sleep(5)

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

	#hyperparameter_sweep()
	return 

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