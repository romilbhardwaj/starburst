import numpy as np

DEFAULT_CONFIG = {
	#====================================================================================================#
	#                                            Sweep Parameters										 #
	#====================================================================================================#
	# Sweep currently supports 3 types of jobs: CPU sleep jobs ('cpu_sleep'), GPU sleep jobs ('gpu_sleep'), and
	# real-life GPU training jobs ('gpu_train').
	'workload_type': 'cpu_sleep',
	# Total time (in seconds) where incoming jobs are submitted. After this time, no more jobs are submitted.
	'submit_time': 300,
	# Random seed for the job generator. This is used to generate the same set of jobs across different runs.
	'random_seed': 13,
	#====================================================================================================#
	#                                       Job Generation Parameters									 #
	#====================================================================================================#
	# Job arrival distribution. Currently, we support two types of distributions: uniform and poisson.
	'arrival_dist': 'uniform', # 'uniform', 'poisson'
	# Job arrival parameter. This defines the average time between job arrivals.
	'arrival_param': 10, 
	# Minimum job arrival time. This is used to prevent jobs from being too close to each other.
	# Note: Do not set it to be less than 3 seconds. Otherwise, the scheduler may not work properly.
	'min_arrival_time': 3,
	# Job duration distribution, which is assumed to be exponential.
	'mean_duration': 30,
	# Minimum job duration. This is used to prevent jobs from being too short.
	'min_duration': 30,
	# Maximum job duration. This is used to prevent jobs from being too long (to save cloud costs).
	'max_duration': 10000,
	# Distribution of CPU resources requested by jobs. Applies for `workload_type: cpu_sleep` 
	# List of CPU sizes (in cores) that jobs can request.
	'cpu_sizes': [1,2,4,8,16,32],
	# List of probabilities for each CPU size. The length of cpu_dist must be equal to the length of cpu_sizes.
	'cpu_dist': [0, 0.2, 0.2, 0.2, 0.2, 0.2], 
	# Distribution of GPU resources requested by jobs. Applies for `workload_type: gpu_sleep, gpu_train` 
	# List of GPU sizes that jobs can request. Multi-node jobs are not supported.
	'gpu_sizes': [1,2,4,8],
	# List of probabilities for each GPU size. The length of gpu_dist must be equal to the length of gpu_sizes.
	# The default distribution follows the jobs in the Microsoft Philadelphia Deep Learning cluster.
	'gpu_dist': [0.7, 0.15, 0.1, 0.05],
	# Docker image for all jobs. Pods are launched with this docker image.
	'image': 'gcr.io/deeplearning-platform-release/pytorch-gpu.1-12',
	#====================================================================================================#
	#                                           Cluster Parameters										 #
	#====================================================================================================#
	# GKE cluster name for on-prem cluster. This is used to submit jobs to the on-prem cluster.
	'onprem_cluster': 'gke_sky-burst_us-central1-c_starburst',
	# GKE cluster name for cloud cluster. This is used to submit jobs to the cloud cluster.
	'cloud_cluster': 'gke_sky-burst_us-central1-c_starburst-cloud',

	"waiting_policy": "fifo_onprem_only", # ignore
	"policy": "fixed", 
	#"onprem_cluster_nodes": 4,
	"cluster_size": 4,
	#"onprem_cpu_per_node": 8,
	"cpus_per_node": 8, 
	"gpus_per_node": 8, 
	"cloud_cluster_nodes": 4, 
	"cloud_cpu_per_node": 8,  
	"wait_time": 0,
	"time_out": 5,
	"use_new_cluster": True, 
	"gpu_workload": False,
	"spill_to_cloud": True,
	"onprem_only": False,
}

# all_language_models = ["bert-tiny-wikitext-2", "bert-mini-wikitext-2", "bert-small-wikitext-2", "bert-tiny-wikitext-103", "bert-mini-wikitext-103", "bert-small-wikitext-103", "gpt2-tiny-wikitext-2", "gpt2-mini-wikitext-2", "gpt2-small-wikitext-2", "gpt2-tiny-wikitext-103", "gpt2-mini-wikitext-103", "gpt2-small-wikitext-103", "gpt2-tiny-wmt-16", "gpt2-mini-wmt-16", "gpt2-small-wmt-16"],

all_vision_models = ["efficientnet-v2", "mobilenet-v3", "resnet-101", "resnet-50", "resnext-50", "vgg11"]

language_models_modified = ["bert-tiny-wikitext-2", "bert-mini-wikitext-2", "bert-small-wikitext-2", "bert-tiny-wikitext-103", "bert-mini-wikitext-103", "bert-small-wikitext-103", "gpt2-tiny-wikitext-2", "gpt2-mini-wikitext-2", "gpt2-tiny-wikitext-103", "gpt2-mini-wikitext-103", "gpt2-small-wikitext-103", "gpt2-tiny-wmt-16", "gpt2-mini-wmt-16"]

all_models = language_models_modified + all_vision_models
# PHILLY - 0.7 * 1 + 0.15 * 2 + 0.1 * 4 + 0.05 * 8 = 1.8
SWEEPS = {
"102": { # Testing CPU sleep jobs
	"fixed_values": {
		"workload_type": "cpu",
		"batch_time": 30, 
		"mean_duration": 3,
		"waiting_policy": "fifo_wait",
		"cpu_dist": [1], #[0.25, 0.25, 0.25, 0.25],
		"cpu_sizes": [1], #[0.1, 0.2, 0.4, 0.8],#[1, 2, 4, 8], #[i * 11 for i in [1, 2, 4, 8]],
		"gpu_dist": [0.7, 0.15, 0.1, 0.05], #Philly Distribution
		"gpu_sizes": [1, 2, 4, 8],
		# Arrival distrubtionm 'arrival_dist': "uniform" or "exponential"
		# Arrival rate/param 'arrival_param/rate': 10
		"uniform_submission": True, #True, 
		"uniform_arrival": 10,
		"onprem_cluster": 'mluo-onprem', #'mluo-onprem',#'gke_sky-burst_us-central1-c_skyburst-gpu',
		"cloud_cluster": 'mluo-cloud',#'mluo-cloud',#'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
		"cluster_size": 2,
		"gpus_per_node": 8,
		"sched_tick": 0.1,
		"wait_time": 5, 
		"spill_to_cloud": False,
		"sample_real_workloads": False,
		"job_type": "sleep",
		"image": "gcr.io/sky-burst/skyburst:latest",
	},
	"varying_values": {	
		"policy": ['constant'], # Computes the optimal values
		"wait_time": [15],
		"arrival_rate": [10],
	}
},
"101": { # Testing CPU sleep jobs
	"fixed_values": {
		"workload_type": "cpu",
		"batch_time": 3 * 60 * 60, 
		"mean_duration": 45 * 60,
		"waiting_policy": "fifo_wait",
		"cpu_dist": [1], #[0.25, 0.25, 0.25, 0.25],
		"cpu_sizes": [1], #[0.1, 0.2, 0.4, 0.8],#[1, 2, 4, 8], #[i * 11 for i in [1, 2, 4, 8]],
		"gpu_dist": [0.7, 0.15, 0.1, 0.05], #Philly Distribution
		"gpu_sizes": [1, 2, 4, 8],
		"uniform_submission": False, #True, 
		"uniform_arrival": 4,
		"onprem_cluster": 'gke_sky-burst_us-central1-c_mluo-onprem',#'gke_sky-burst_us-central1-c_skyburst-gpu',
		"cloud_cluster": 'gke_sky-burst_us-central1-c_mluo-cloud',#'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
		"cluster_size": 1,
		"gpu_workload": True, # TODO: Remove since not used
		"gpus_per_node": 8,
		"sched_tick": 0.1,
		"wait_time": 5, 
		"spill_to_cloud": False,
		"arrival_rate": 0.75, # Maxes at 4k jobs bc 3 second interarrival rate
		"sample_real_workloads": False, #True,
		"job_type": "sleep", #"train",
		"image": "gcr.io/sky-burst/skyburst:latest",
	},
	"varying_values": {	
		"policy": ['constant', 'starburst', 'constant_optimal'], # Computes the optimal values
		"wait_time": [15],
		"arrival_rate": [32/(60*60)] # job/second ~ 45 minutes per job jobs per hour / 32 gpu cluster  -- system util 75 -- 32 jobs ~ 1.3 jobs * 32 jobs = 41jobs (1 gpu ~ 45min per job) -- 41 / 2 ~ 21 jobs per hour 
	}
},
"60": { # True overloaded -- VERIFIED 
	"fixed_values": {
		"batch_time": 3 * 60 * 60, 
		"mean_duration": 45 * 60,
		"waiting_policy": "fifo_wait",
		"cpu_dist":[0.25, 0.25, 0.25, 0.25],
		"cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		"gpu_dist": [0.7, 0.15, 0.1, 0.05], #Philly Distribution
		"gpu_sizes": [1, 2, 4, 8],
		"uniform_submission": False, #True, 
		"uniform_arrival": 4,
		"onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
		"cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
		"cluster_size": 1,
		"gpu_workload": True,
		"gpus_per_node": 8,
		"sched_tick": 0.1,
		"wait_time": 5, 
		"spill_to_cloud": False,
		"arrival_rate": 0.75, # Maxes at 4k jobs bc 3 second interarrival rate
		"sample_real_workloads": True,
		"job_type": "train",
		"image": "gcr.io/sky-burst/skyburst:latest",
	},
	"varying_values": {	
		"policy": ['constant', 'starburst', 'constant_optimal'], # Computes the optimal values
		"wait_time": [15],
		"arrival_rate": [32/(60*60)] # job/second ~ 45 minutes per job jobs per hour / 32 gpu cluster  -- system util 75 -- 32 jobs ~ 1.3 jobs * 32 jobs = 41jobs (1 gpu ~ 45min per job) -- 41 / 2 ~ 21 jobs per hour 
	}
},
"49": { # Final Sweep -- OVERLOADED util 
	"fixed_values": {
		"batch_time": 5 * 60 * 60, 
		"mean_duration": 45 * 60,
		"waiting_policy": "fifo_wait",
		"cpu_dist":[0.25, 0.25, 0.25, 0.25],
		"cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		"gpu_dist": [0.7, 0.15, 0.1, 0.05], #Philly Distribution
		"gpu_sizes": [1, 2, 4, 8],
		"uniform_submission": False, #True, 
		"uniform_arrival": 4,
		"onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
		"cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
		"cluster_size": 1,
		"gpu_workload": True,
		"gpus_per_node": 8,
		"sched_tick": 0.1,
		"wait_time": 5, 
		"spill_to_cloud": False,
		"arrival_rate": 0.75, # Maxes at 4k jobs bc 3 second interarrival rate
		"sample_real_workloads": True,
		"job_type": "train",
		"image": "gcr.io/sky-burst/skyburst:latest",
	},
	"varying_values": {	
		"policy": ['constant', 'starburst', 'constant_optimal'], # Computes the optimal values

		"wait_time": [15], # TODO: Specify 10~15 seconds wait -- moved from 5 to 15 
		"arrival_rate": [32/(60*60)] # Moved from 20 to 32 -- job/second ~ 45 minutes per job jobs per hour / 32 gpu cluster  -- system util 75 -- 32 jobs ~ 1.3 jobs * 32 jobs = 41jobs (1 gpu ~ 45min per job) -- 41 / 2 ~ 21 jobs per hour 
	}
},
}