import numpy as np
import submit_jobs

DEFAULT_HYPERPARMATERS = submit_jobs.DEFAULT_HYPERPARAMETERS

def generate_interval(min=0, max=10, intervals=10):
	return np.linspace(min, max, num=intervals+1).tolist()

SWEEPS = {
	"6": { # Uniform wait -- smoke test scheduler
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
	"5": { # Uniform wait -- smoke test scheduler
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
	"4": { # Uniform wait -- smoke test scheduler
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