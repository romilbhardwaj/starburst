import numpy as np

DEFAULT_HYPERPARAMETERS = {
	"sleep": True, 
	"image": "gcr.io/deeplearning-platform-release/pytorch-gpu.1-12",
    "setup_script": "nvidia-smi --query-gpu=index --format=csv,noheader && sleep 1000",
	"uniform_arrival": 1, 
	"uniform_submission": False,
	"waiting_policy": "fifo_onprem_only",
	"time_constrained": True,
	#"onprem_cluster_nodes": 4,
	"cluster_size": 4,
	#"onprem_cpu_per_node": 8,
	"cpus_per_node": 8, 
	"gpus_per_node": 8, 
	"cloud_cluster_nodes": 4, 
	"cloud_cpu_per_node": 8,  
	"random_seed": 0,
	'total_jobs': 100,
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
	"use_new_cluster": True, 
	"onprem_cluster": "gke_sky-burst_us-central1-c_starburst",
    "cloud_cluster": "gke_sky-burst_us-central1-c_starburst-cloud",
    "gpu_workload": False
}

def generate_interval(min=0, max=10, intervals=10):
	return np.linspace(min, max, num=intervals+1).tolist()

SWEEPS = {
	"32": { # Real world workload
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 0.5,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [10],
            "arrival_rate": [1] 
        }
    },
    "31": { # Testing small and large batches for onprem only and cloud spillover
		"fixed_values": {
            "batch_time": 60, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 0.5,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [60],
            "arrival_rate": [1],
            #"setup_script": "/tasks/*.sh"
        }
    },
	"30": { # Testing small and large batches for onprem only and cloud spillover
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 0.5,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [10],
            "arrival_rate": [1],
            #"setup_script": "/tasks/*.sh"
        }
    },
	"29": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 0.5,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [10],
            "arrival_rate": [1] 
        }
    },
	"28": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 0.5,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [10],
            "arrival_rate": [1] 
        }
    },
	"27": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [2, 5, 10],
            "arrival_rate": [1] 
        }
    },
	"26": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [10],
            "arrival_rate": [1] 
        }
    },
    "25": {
		"description": "debug why fifo constant wait sends all jobs to cloud with high arrival rate (i.e. low inter-arrival time)",
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 30,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.3
        },
	    "varying_values": {	
            "uniform_arrival": [3],
            "wait_time": [10],
            "arrival_rate": [1]
        }
    },
	"24": {
		"description": "debug why fifo constant wait sends all jobs to cloud with high arrival rate (i.e. low inter-arrival time)",
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.3
        },
	    "varying_values": {	
            "uniform_arrival": [0.25, 0.75],
            "wait_time": [10],
            "arrival_rate": [1] 
        }
    },
	"23": {
		"description": "debug why fifo constant wait sends all jobs to cloud with high arrival rate (i.e. low inter-arrival time)",
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.5
        },
	    "varying_values": {	
            "uniform_arrival": [0.25, 0.75],
            "wait_time": [10],
            "arrival_rate": [1] 
        }
    },
	"22": {
		"description": "debug why fifo constant wait sends all jobs to cloud with high arrival rate (i.e. low inter-arrival time)",
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "uniform_arrival": [0.75],
            "wait_time": [10],
            "arrival_rate": [1] 
        }
    },
	"21": {
		"description": "debug why fifo constant wait sends all jobs to cloud with high arrival rate (i.e. low inter-arrival time)",
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "uniform_arrival": [1.5],
            "wait_time": [2, 5],
            "arrival_rate": [1] 
        }
    },
	"20": {
		"description": "debug why fifo constant wait sends all jobs to cloud with high arrival rate (i.e. low inter-arrival time)",
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "uniform_arrival": [0.75],
            "wait_time": [2, 5],
            "arrival_rate": [1] 
        }
    },
    "19": { #CIFAR RESNET JOB Varying wait timeouts with different arrival rates
		"fixed_values": {
			"sleep": False, 
			"image": "gcr.io/sky-burst/skyburst:latest",
            "setup_script": "python /tasks/pytorch-cifar10-resnet50.py",
            "batch_time": 60 * 10, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2, #5,#10,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "uniform_arrival": [60], 
            "wait_time": [60],
            "arrival_rate": [1] 
        }
    },
	"18": { #MNIST JOB Varying wait timeouts with different arrival rates
		"fixed_values": {
			"sleep": False, 
			"image": "gcr.io/sky-burst/skyburst:latest",
            "setup_script": "python /tasks/pytorch-mnist.py",
            "batch_time": 60 * 10, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2, #5,#10,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "uniform_arrival": [60], 
            "wait_time": [60],
            "arrival_rate": [1] 
        }
    },
    "17": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": False, 
            "uniform_arrival": 2,#5,#10,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "arrival_rate": [0.25, 0.5, 1, 2], #jobs/sec
            "wait_time": [2, 10],
            "arrival_rate": [1] 
        }
    },
    "16b": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "arrival_rate": [0.75, 1.5, 3, 6, 9], #TODO: Figure out the optimal values
            "wait_time": [2, 5, 10],
            "arrival_rate": [1] 
        }
    },
    "16": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,#5,#10,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "uniform_arrival": [0.75, 1.5, 3, 6, 9], # PREV:  [3, 6, 9] # NOTE: Cpu_dist not used when running gpu_jobs based on generate_jobs()
            "wait_time": [2, 5, 10],
            "arrival_rate": [1] 
        }
    },
	"15": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,#5,#10,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
        },
	    "varying_values": {	
            "uniform_arrival": [3, 6, 9], # NOTE: Cpu_dist not used when running gpu_jobs based on generate_jobs()
            "wait_time": [5],
            "arrival_rate": [1] 
        }
    },
	"14": { #8 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 300, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 2,#5,#10,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "gpu_workload": True
        },
	    "varying_values": {	
            "cpu_dist": [[0.7, 0.15, 0.1, 0.05]], # NOTE: Cpu_dist not used when running gpu_jobs based on generate_jobs()
            "wait_time": [5], #,3,4,5,6,7,8],
            "arrival_rate": [1] 
        }
    },
	"13": { #2 GPU, Multi gpu node test without cluster congestion
		"fixed_values": {
            "batch_time": 60, 
            "mean_duration": 5,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2],
            "gpu_dist": [0.2, 0.8],
            "uniform_submission": True, 
            "uniform_arrival": 10,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "gpu_workload": True
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [2,3,4,5,6,7,8],
            "arrival_rate": [1] 
        }
    },
	"12": { #Single node gpu test without cluster congestion
		"fixed_values": {
            "batch_time": 60, 
            "mean_duration": 5,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1],
            "gpu_sizes": [1, 1],
            "gpu_dist": [0.5, 0.5],
            "uniform_submission": True, 
            "uniform_arrival": 10,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "gpu_workload": True
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [2,3,4,5,6,7,8],
            "arrival_rate": [1] 
        }
    },
    "11": { #Single node gpu test with longer job time to ensure gpu index value is saved
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1],
            "gpu_sizes": [1, 1],
            "gpu_dist": [0.5, 0.5],
            "uniform_submission": True, 
            "uniform_arrival": 0.5,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "gpu_workload": True
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [2,3,4,5,6,7,8],
            "arrival_rate": [1] 
        }
    },
	"10": { #Single node gpu test
		"fixed_values": {
            "batch_time": 180, 
            "mean_duration": 5,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1],
            "gpu_sizes": [1, 1],
            "gpu_dist": [0.5, 0.5],
            "uniform_submission": True, 
            "uniform_arrival": 0.5,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "gpu_workload": True
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [2,3,4,5,6,7,8],
            "arrival_rate": [1] 
        }
    },
	"9": { #CPU death test
        "fixed_values": {
            "batch_time": 180, 
            "mean_duration": 5,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1, 2, 4],
            "uniform_submission": True, 
            "uniform_arrival": 0.5,
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [2,3,4,5,6,7,8],
            "arrival_rate": [1] 
        }
    },
	"8": { #GPU Smoke test
        "fixed_values": {
            "batch_time": 30, 
            "mean_duration": 1,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1],
            "gpu_dist": [1],
            "uniform_submission": True, 
            "uniform_arrival": 1,
            "onprem_cluster": "test1",
            "cloud_cluster": "test2",
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [1, 5],
            "arrival_rate": [1] 
        }
    },
	"7": { #Uniform wait -- smoke test scheduler
        "fixed_values": {
            "batch_time": 180, 
            "mean_duration": 5,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1, 2, 4],
            "uniform_submission": True, 
            "uniform_arrival": 10,
            "onprem_cluster": "test1",
            "cloud_cluster": "test2",
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [1, 5],
            "arrival_rate": [1] 
        }
    },
	"6": { #Uniform wait -- smoke test scheduler
        "fixed_values": {
            "batch_time": 180, 
            "mean_duration": 5,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1, 2, 4],
            "uniform_submission": True, 
            "uniform_arrival": 10,
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [1, 5],
            "arrival_rate": [1] 
        }
    },
	"5": { #Uniform wait -- smoke test scheduler
        "fixed_values": {
            "batch_time": 180, 
            "mean_duration": 5,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1, 2, 4],
            "uniform_submission": True, 
            "uniform_arrival": 10,
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [0.5, 5],
            "arrival_rate": [1] 
        }
    },
	"4": { #Uniform wait -- smoke test scheduler
        "fixed_values": {
            "batch_time": 180, 
            "mean_duration": 5,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1, 2, 4],
            "uniform_submission": True, 
            "uniform_arrival": 30
        },
	    "varying_values": {	
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [0.5, 5],
            "arrival_rate": [1, 1, 1] 
        }
    },
    "3": {
        "fixed_values" : {
            "batch_time": 180,
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1, 2, 4],
            "uniform_submission": True,
            "uniform_arrival": 4
        },
        "varying_values" :{
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [3],
            "arrival_rate": [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3]
        }
    },
    "2": {
        "fixed_values" : {
            "batch_time": 180,
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1, 2, 4],
        },
        "varying_values" :{
            "cpu_dist": [[0.6, 0.25, 0.15]],
            "wait_time": [3],
            "arrival_rate": [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3]
        }
    },
    "1": {
        "fixed_values" : {
            "batch_time": 120,
            "mean_duration": 10,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[1, 2, 4],
        },
        "varying_values" :{
            "cpu_dist": [[0.2, 0.4, 0.4], [0, 0.5, 0.5], [0, 0, 1]],	
            "wait_time": [0.1, 2.5, 5, 10],
            "arrival_rate": [1/i for i in generate_interval(0.1, 3, 4)],
        }
    }
}

cluster = {
    'name': "starburst_cpu",
    'network': 'skypilot-vpc',
    'initial_node_count': 1,
    #'master_auth': {
    #	'username': 'admin',
    #	'password': 'passwordpassword'
    #},
    'node_config': {
        'machine_type': 'n1-standard-1',
        'disk_size_gb': 100,
        'oauth_scopes': [
            'https://www.googleapis.com/auth/compute',
            'https://www.googleapis.com/auth/devstorage.read_write',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring'
        ]
    }
}