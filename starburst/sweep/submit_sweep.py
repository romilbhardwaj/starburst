import argparse
import copy
import itertools
import logging
import multiprocessing as mp
import os 
import psutil
import time
from typing import Dict, List


import starburst.drivers.main_driver as driver 
from  starburst.sweep import job_generator, sweep_logger, sweeps, utils
from starburst.sweep.services import job_submission, event_logger

DEFAULT_CONFIG = sweeps.DEFAULT_CONFIG

logger = logging.getLogger(__name__)

def clear_prior_sweeps(retry_limit: int = 1) -> None:
	"""
	Deletes all prior sweeps from the cluster.

	Args:
		retry_limit (int): Number of times to retry deleting a sweep before giving up.
	"""
	current_pid = os.getpid()
	for _ in range(retry_limit):
		# Get a list of all processes.
		processes = psutil.process_iter()
		found_submit_process = False
		for process in processes:
			try:
				# Obtain process name and CMD line arguments.
				name = process.name()
				cmdline = process.cmdline()
				# Check for prior sweeps and if the prior sweep is not this current sweep.
				if name == 'python3' and 'submit_jobs.py' in cmdline and process.pid != current_pid:
					# terminate the process
					process.terminate()
					found_submit_process = True
			except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
				pass
		if not found_submit_process:
			break

def generate_runs(sweep_config: dict) -> List[dict]: 
	"""
	Takes specified fixed values and generates grid of hyperparameters based on varying values

	Args:
		sweep_config (dict): Dictionary of hyperparameters to sweep over.
	"""
	list_type_args = ['cpu_sizes', 'cpu_dist', 'gpu_sizes', 'gpu_dist']

	# Split sweep_config into fixed and varied hyperparameters.
	base_config = copy.deepcopy(sweeps.DEFAULT_CONFIG)
	varied_config = {}
	for key, value in sweep_config.items():
		if not isinstance(value, list):
			base_config[key] = value
		elif isinstance(value, list) and key in list_type_args \
			and not isinstance(value[0], list):
			base_config[key] = value
		else:
			varied_config[key] = value
	
	# Generate carteisan production across varied hyperparameters.
	keys = []
	values = []
	for key, value in varied_config.items():
		keys.append(key)
		values.append(value)
	grid_search = itertools.product(*values)

	# Generate runs from cartesian product.
	runs = {}
	for run_index, trial in enumerate(grid_search):
		for key_index, key in enumerate(keys):
			base_config[key] = trial[key_index]
		runs[run_index] = copy.deepcopy(base_config)
	return runs

def launch_run(run_config: dict, sweep_name: str, run_index: int = 0):
	run_config = utils.RunConfig(run_config)
	
	# Generate jobs and their corresponding arrival times.
	jobs = job_generator.generate_jobs(run_config=run_config)
	job_yaml_path = f'{sweep_logger.LOG_DIRECTORY.format(name=sweep_name)}jobs/{run_index}.yaml'
	utils.save_yaml_object(jobs, job_yaml_path)

	clusters = {"onprem": run_config.onprem_cluster, "cloud": run_config.cloud_cluster}
	p0 = mp.Process(target=driver.custom_start, args=(driver.GRPC_PORT, run_config.sched_tick, clusters['onprem'], clusters['cloud'], run_config.waiting_policy, run_config.wait_time, jobs, sweep_name, run_index, run_config.policy))
	p0.start()
	
	while not utils.check_empty_cluster(clusters=clusters):
		logger.debug(f'Cleaning cluster pods, jobs, and event logs...')
		utils.clear_clusters(clusters=clusters)
		time.sleep(1)
	logger.debug(f'Starting Run ID: {run_index}.')
	
	# TODO: Delete file
	signal_file = sweep_logger.LOG_DIRECTORY.format(name=sweep_name) + '/signal.lock' 
	try:
		os.unlink(signal_file)
	except Exception as e: 
		pass 

	p1 = mp.Process(target=event_logger.logger_service, args=(str(run_index), sweep_name, clusters['onprem'], clusters['cloud'], str(run_index)))
	p1.start()

	job_submission_service = mp.Process(target=job_submission.job_submission_service, args=(jobs, clusters, sweep_name, run_index))
	job_submission_service.start()
	job_submission_service.join()
	
	# TODO: Write file 
	with open(signal_file, "w") as f:
		pass
	p1.join()
	p0.terminate()
	logger.debug("Terminated Scheduler...")
	return 0
	
def sweep_pipeline(sweep_config: str):
	"""
	Runs a hyperparameter sweep on the cluster.

	Args:
		sweep_config (str): Path to YAML file containing sweep configuration.
	"""
	# 1) Clean Sweeps from prior runs.
	clear_prior_sweeps(retry_limit=3)

	# 2) Create Log directory for sweep
	current_timestamp = sweep_logger.create_log_directory()

	# 3) Load sweep config and generate runs.
	sweep_dict = utils.load_yaml_file(sweep_config)
	runs_dict = generate_runs(sweep_dict)
	utils.save_yaml_object(runs_dict, sweep_logger.LOG_DIRECTORY.format(name=current_timestamp)+ "sweep.yaml")

	# 4) Launch runs in sequence.
	for run_idx in runs_dict.keys():
		launch_run(run_config=runs_dict[run_idx],
	     		   sweep_name=current_timestamp,
				   run_index=str(run_idx))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Submit a sweep of synthetically generated jobs.')
	parser.add_argument(
		'--config',
		type=str,
		default='../../scripts/cpu_sweep.yaml',
		help='Input YAML config for sweep.')
	parser.add_argument('--debug',
		     action='store_true',
			 help='Enable debug mode')
	args = parser.parse_args()
	sweep_pipeline(sweep_config=args.config)