import numpy as np 
import matplotlib.pyplot as plt
import os 
import time

'''
Design Layout

1. Generate Job Hyperparameters
	a. Hyperparameters
		i. Arrival Time
		ii. Sleep Time
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
		curr_time += np.random.exponential(scale=3.0)
		times.append(curr_time)
	plt.eventplot(times)
	plt.savefig('../plots/arrival_times.png')
	return times

def submit_jobs(arrival_times, timeout): 
	""" Submits a a default job for each time stamp of the inputed arrival times """
	total_jobs = len(arrival_times)
	start_time = time.time()
	job = 0 
	while True: 
		curr_time = time.time()
		if job < total_jobs and curr_time > arrival_times[job] + start_time: 
			job += 1
			os.system('python3 -m starburst.drivers.submit_job --job-yaml ../../examples/default/example_job.yaml')	
		elif curr_time >= start_time + timeout:
			break

def sampled_job(arrival_time, sleep_time, workload):
	""" Generalizes job submission to perform hyperparameter sweep """

	# TODO: Finalize design
	return 

def main():
	times = arrival_times(10)
	submit_jobs(times, 30)

if __name__ == '__main__':
    main()