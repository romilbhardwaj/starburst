import numpy as np

DEFAULT_HYPERPARAMETERS = {
	"job_type": "sleep", 
	"image": "gcr.io/deeplearning-platform-release/pytorch-gpu.1-12",
    "setup_script": "nvidia-smi --query-gpu=index --format=csv,noheader && sleep 1000",
	"uniform_arrival": 1, 
	"uniform_submission": False,
	"waiting_policy": "fifo_onprem_only", # ignore
	"policy": "fixed", 
	"time_constrained": True,
	#"onprem_cluster_nodes": 4,
	"cluster_size": 4,
	#"onprem_cpu_per_node": 8,
	"cpus_per_node": 8, 
	"gpus_per_node": 8, 
	"cloud_cluster_nodes": 4, 
	"cloud_cpu_per_node": 8,  
	"random_seed": 0,
	'total_jobs': 125,
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
	"train_names": ['test'],
	"train_dist": [1], 
	"use_new_cluster": True, 
	"onprem_cluster": "gke_sky-burst_us-central1-c_starburst",
    "cloud_cluster": "gke_sky-burst_us-central1-c_starburst-cloud",
    "gpu_workload": False,
    "spill_to_cloud": True,
    "onprem_only": False,
    "collect_runtimes": False,
}

def generate_interval(min=0, max=10, intervals=10):
	return np.linspace(min, max, num=intervals+1).tolist()


bash_script = """
#!/bin/bash
echo "Hello, World!"
echo "This is a multiline Bash script."
echo "You can include multiple lines of commands here."
"""
single_string = bash_script.strip().replace('\n', ';')
'''
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
python $SCRIPT_DIR/huggingface-bert-wikitext.py \
--dataset wikitext-2 --per_device_train_batch_size 32 \
--hidden_size 128 \
--num_hidden_layers 2 \
--num_attention_heads 4 \
--num_train_epochs 1
'''

TRAINING_JOBS = {
	# TODO: make sure to specify the gpu size per models 
	# Vision models
    
    "efficientnet-v2": {
	    "train_script": "/tasks/pytorch-cifar10-efficientnet_v2_m.py", # TODO: support argparse 
	    "estimated_training_runtime": 600, #10 minutes
	    "gpu_runtimes": {
            1: 0,
            2: 0, 
            4: 0,
            8: 0
        },
        "epochs": {
            1: 0,
            2: 0, 
        }
    },
    "mobilenet-v3": {
	    "train_script": "/tasks/pytorch-cifar10-mobilenet_v3_small.py",
	    "estimated_training_runtime": 600, #10 minutes
	    "gpu_runtimes": {
            1: 0,
            2: 0, 
            4: 0,
            8: 0
        },
        "epochs": {
            1: 0,
            2: 0, 
        }
    },
    "resnet-101": {
	    "train_script": "/tasks/pytorch-cifar10-resnet101.py",
	    "estimated_training_runtime": 0, # Unverified
	    "gpu_runtimes": {
            1: 0,
            2: 0, 
            4: 0,
            8: 0
        },
        "epochs": {
            1: 0,
            2: 0, 
        }
    },
    "resnet-50": {
	    "train_script": "/tasks/pytorch-cifar10-resnet50.py",
	    "estimated_training_runtime": 0, # Unverified
	    "gpu_runtimes": {
            1: 0,
            2: 0, 
            4: 0,
            8: 0
        },
        "epochs": {
            1: 0,
            2: 0, 
        }
    },
    "resnext-50": {
	    "train_script": "/tasks/pytorch-cifar10-resnext50_32x4d.py",
	    "estimated_training_runtime": 0, # Unverified
	    "gpu_runtimes": {
            1: 0,
            2: 0, 
            4: 0,
            8: 0
        },
        "epochs": {
            1: 0,
            2: 0, 
        }
    },
    "vgg11": {
	    "train_script": "/tasks/pytorch-cifar10-vgg11.py",
	    "estimated_training_runtime": 0, # Unverified
	    "gpu_runtimes": {
            1: 0,
            2: 0, 
            4: 0,
            8: 0
        },
        "epochs": {
            1: 0,
            2: 0, 
        }
    },
    # Language models
    "bert-tiny-wikitext-2": {
        "train_script": "/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --gradient_accumulation_steps 2", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "bert-mini-wikitext-2": {
        "train_script": "/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "bert-small-wikitext-2": {
        "train_script": "/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --hidden_size 512 --num_hidden_layers 4 --num_attention_heads 8", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "bert-tiny-wikitext-103": {
        "train_script": "/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --gradient_accumulation_steps 2", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
	    "epochs": {
            0: 0
        }
    },
    "bert-mini-wikitext-103": {
        "train_script": "/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 16 --hidden_size 256 --num_hidden_layers 4 --num_attention_heads 4", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "bert-small-wikitext-103": {
        "train_script": "/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --hidden_size 512 --num_hidden_layers 4 --num_attention_heads 8", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-tiny-wikitext-2": {
        "train_script": "/tasks/huggingface-gpt-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4  --gradient_accumulation_steps 2", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-mini-wikitext-2": {
        "train_script": "/tasks/huggingface-gpt-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-small-wikitext-2": {
        "train_script": "/tasks/huggingface-gpt-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 4 --n_embd 768 --n_layer 12 --n_head 12", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-tiny-wikitext-103": {
        "train_script": "/tasks/huggingface-gpt-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4 --gradient_accumulation_steps 2", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-mini-wikitext-103": {
        "train_script": "/tasks/huggingface-gpt-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-small-wikitext-103": {
        "train_script": "/tasks/huggingface-gpt-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 4 --n_embd 768 --n_layer 12 --n_head 12", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-tiny-wmt-16": {
        "train_script": "/tasks/huggingface-gpt-wmt16.py --language_pair fi-en --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4 --gradient_accumulation_steps 2", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-mini-wmt-16": {
        "train_script": "/tasks/huggingface-gpt-wmt16.py --language_pair fi-en --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    "gpt2-small-wmt-16": {
        "train_script": "/tasks/huggingface-gpt-wmt16.py --language_pair fi-en --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "epochs": {
            0: 0
        }
    },
    # Misc models
    "pytorch-regression": {
	    "train_script": "python /tasks/pytorch-regression.py", 
	    "estimated_training_runtime": 5
    },
    "sklearn-breast_cancer-random_forest": {
	    "train_script": "python /tasks/sklearn-breast_cancer-random_forest.py",
	    "estimated_training_runtime": 5
    },
    "pytorch-mnist": {
	    "train_script": "python /tasks/pytorch-mnist.py",
	    "estimated_training_runtime": 300 #5 minutes
    }
}

all_language_models = ["bert-tiny-wikitext-2", "bert-mini-wikitext-2", "bert-small-wikitext-2", "bert-tiny-wikitext-103", "bert-mini-wikitext-103", "bert-small-wikitext-103", "gpt2-tiny-wikitext-2", "gpt2-mini-wikitext-2", "gpt2-small-wikitext-2", "gpt2-tiny-wikitext-103", "gpt2-mini-wikitext-103", "gpt2-small-wikitext-103", "gpt2-tiny-wmt-16", "gpt2-mini-wmt-16", "gpt2-small-wmt-16"],
all_vision_models = ["efficientnet-v2", "mobilenet-v3", "resnet-101", "resnet-50", "resnext-50", "vgg11"]

language_models_modified = ["bert-tiny-wikitext-2", "bert-mini-wikitext-2", "bert-small-wikitext-2", "bert-tiny-wikitext-103", "bert-mini-wikitext-103", "bert-small-wikitext-103", "gpt2-tiny-wikitext-2", "gpt2-mini-wikitext-2", "gpt2-tiny-wikitext-103", "gpt2-mini-wikitext-103", "gpt2-small-wikitext-103", "gpt2-tiny-wmt-16", "gpt2-mini-wmt-16"]

all_models = language_models_modified + all_vision_models

SWEEPS = {
	"2": { # High System Util - nowait, constant wait, compute wait, starburst
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 900, 
            "mean_duration": 30,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": False, 
            "uniform_arrival": 4,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_starburst-sleep',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3,
		    "spill_to_cloud": False,
		    "arrival_rate": 0.75, 
        },
	    "varying_values": {	
		    "policy": ['constant', 'starburst', 'constant_optimal'], # Computes the optimal values
            "arrival_rate": [0.25],
	        "wait_time": [3],
        }
    },
    "1": { # High System Util - nowait, constant wait, compute wait, starburst
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 60, 
            "mean_duration": 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": False, #True, 
            "uniform_arrival": 4,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_starburst-sleep',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3,
		    "spill_to_cloud": False,
		    "arrival_rate": 0.75, 
        },
	    "varying_values": {	
		    "policy": ['constant', 'starburst', 'constant_optimal'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [0.75] 
        }
    },
    "0": { # Philly trace sweep - nowait, constant wait, compute wait, starburst
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 120, 
            "mean_duration": 120,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": False, #True, 
            "uniform_arrival": 4,
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3,
		    "spill_to_cloud": False,
		    "arrival_rate": 0.75, 
        },
	    "varying_values": {	
		    "policy": ['starburst', 'constant', 'constant_optimal'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [0.75] 
        }
    },
}