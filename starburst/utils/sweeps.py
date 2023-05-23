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
    "sample_real_workloads": False 
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
TRAINING_TIMES = [(0, 181, 4, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --gradient_accumulation_steps 2'), (1, 182, 8, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --gradient_accumulation_steps 2'), (2, 197, 4, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4'), (3, 188, 8, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4'), (4, 226, 4, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --hidden_size 512 --num_hidden_layers 4 --num_attention_heads 8'), (5, 235, 8, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --hidden_size 512 --num_hidden_layers 4 --num_attention_heads 8'), (6, 4821, 4, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --gradient_accumulation_steps 2'), (7, 7383, 8, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 16 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --gradient_accumulation_steps 2'), (8, 8505, 4, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 16 --hidden_size 256 --num_hidden_layers 4 --num_attention_heads 4'), (9, 7760, 8, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 16 --hidden_size 256 --num_hidden_layers 4 --num_attention_heads 4'), (10, 11972, 4, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --hidden_size 512 --num_hidden_layers 4 --num_attention_heads 8'), (12, 330, 4, '/tasks/huggingface-gpt-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4  --gradient_accumulation_steps 2'), (14, 531, 4, '/tasks/huggingface-gpt-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8'), (16, 15342, 4, '/tasks/huggingface-gpt-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4 --gradient_accumulation_steps 2'), (18, 28825, 4, '/tasks/huggingface-gpt-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8'), (11, 9751, 8, '/tasks/huggingface-bert-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --hidden_size 512 --num_hidden_layers 4 --num_attention_heads 8'), (15, 417, 8, '/tasks/huggingface-gpt-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8'), (22, 6523, 4, '/tasks/huggingface-gpt-wmt16.py --language_pair fi-en --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4 --gradient_accumulation_steps 2'), (13, 299, 8, '/tasks/huggingface-gpt-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4  --gradient_accumulation_steps 2'), (17, 11920, 8, '/tasks/huggingface-gpt-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4 --gradient_accumulation_steps 2'), (24, 8522, 4, '/tasks/huggingface-gpt-wmt16.py --language_pair fi-en --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8'), (26, 114, 1, '/tasks/pytorch-cifar10-efficientnet_v2_m.py --num_train_epochs 1'), (28, 98, 2, '/tasks/pytorch-cifar10-efficientnet_v2_m.py --num_train_epochs 1'), (27, 234, 1, '/tasks/pytorch-cifar10-efficientnet_v2_m.py --num_train_epochs 2'), (30, 84, 4, '/tasks/pytorch-cifar10-efficientnet_v2_m.py --num_train_epochs 1'), (19, 18116, 8, '/tasks/huggingface-gpt-wikitext.py --dataset wikitext-103 --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8'), (31, 137, 4, '/tasks/pytorch-cifar10-efficientnet_v2_m.py --num_train_epochs 2'), (29, 180, 2, '/tasks/pytorch-cifar10-efficientnet_v2_m.py --num_train_epochs 2'), (34, 67, 1, '/tasks/pytorch-cifar10-mobilenet_v3_small.py --num_train_epochs 1'), (36, 53, 2, '/tasks/pytorch-cifar10-mobilenet_v3_small.py --num_train_epochs 1'), (38, 48, 4, '/tasks/pytorch-cifar10-mobilenet_v3_small.py --num_train_epochs 1'), (23, 5554, 8, '/tasks/huggingface-gpt-wmt16.py --language_pair fi-en --per_device_train_batch_size 8 --n_embd 256 --n_layer 4 --n_head 4 --gradient_accumulation_steps 2'), (37, 90, 2, '/tasks/pytorch-cifar10-mobilenet_v3_small.py --num_train_epochs 2'), (35, 127, 1, '/tasks/pytorch-cifar10-mobilenet_v3_small.py --num_train_epochs 2'), (39, 76, 4, '/tasks/pytorch-cifar10-mobilenet_v3_small.py --num_train_epochs 2'), (25, 10889, 8, '/tasks/huggingface-gpt-wmt16.py --language_pair fi-en --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8'), (42, 89, 1, '/tasks/pytorch-cifar10-resnet101.py --num_train_epochs 1'), (44, 75, 2, '/tasks/pytorch-cifar10-resnet101.py --num_train_epochs 1'), (46, 64, 4, '/tasks/pytorch-cifar10-resnet101.py --num_train_epochs 1'), (32, 93, 8, '/tasks/pytorch-cifar10-efficientnet_v2_m.py --num_train_epochs 1'), (45, 129, 2, '/tasks/pytorch-cifar10-resnet101.py --num_train_epochs 2'), (43, 160, 1, '/tasks/pytorch-cifar10-resnet101.py --num_train_epochs 2'), (47, 102, 4, '/tasks/pytorch-cifar10-resnet101.py --num_train_epochs 2'), (33, 150, 8, '/tasks/pytorch-cifar10-efficientnet_v2_m.py --num_train_epochs 2'), (50, 72, 1, '/tasks/pytorch-cifar10-resnet50.py --num_train_epochs 1'), (40, 62, 8, '/tasks/pytorch-cifar10-mobilenet_v3_small.py --num_train_epochs 1'), (52, 62, 2, '/tasks/pytorch-cifar10-resnet50.py --num_train_epochs 1'), (54, 55, 4, '/tasks/pytorch-cifar10-resnet50.py --num_train_epochs 1'), (51, 133, 1, '/tasks/pytorch-cifar10-resnet50.py --num_train_epochs 2'), (55, 83, 4, '/tasks/pytorch-cifar10-resnet50.py --num_train_epochs 2'), (41, 88, 8, '/tasks/pytorch-cifar10-mobilenet_v3_small.py --num_train_epochs 2'), (53, 106, 2, '/tasks/pytorch-cifar10-resnet50.py --num_train_epochs 2'), (58, 76, 1, '/tasks/pytorch-cifar10-resnext50_32x4d.py --num_train_epochs 1'), (48, 73, 8, '/tasks/pytorch-cifar10-resnet101.py --num_train_epochs 1'), (60, 66, 2, '/tasks/pytorch-cifar10-resnext50_32x4d.py --num_train_epochs 1'), (62, 56, 4, '/tasks/pytorch-cifar10-resnext50_32x4d.py --num_train_epochs 1'), (59, 149, 1, '/tasks/pytorch-cifar10-resnext50_32x4d.py --num_train_epochs 2'), (63, 85, 4, '/tasks/pytorch-cifar10-resnext50_32x4d.py --num_train_epochs 2'), (61, 109, 2, '/tasks/pytorch-cifar10-resnext50_32x4d.py --num_train_epochs 2'), (49, 106, 8, '/tasks/pytorch-cifar10-resnet101.py --num_train_epochs 2'), (66, 72, 1, '/tasks/pytorch-cifar10-vgg11.py --num_train_epochs 1'), (56, 66, 8, '/tasks/pytorch-cifar10-resnet50.py --num_train_epochs 1'), (68, 55, 2, '/tasks/pytorch-cifar10-vgg11.py --num_train_epochs 1'), (67, 150, 1, '/tasks/pytorch-cifar10-vgg11.py --num_train_epochs 2'), (69, 93, 2, '/tasks/pytorch-cifar10-vgg11.py --num_train_epochs 2'), (57, 89, 8, '/tasks/pytorch-cifar10-resnet50.py --num_train_epochs 2'), (64, 63, 8, '/tasks/pytorch-cifar10-resnext50_32x4d.py --num_train_epochs 1'), (70, 79, 4, '/tasks/pytorch-cifar10-vgg11.py --num_train_epochs 1'), (65, 91, 8, '/tasks/pytorch-cifar10-resnext50_32x4d.py --num_train_epochs 2'), (71, 109, 4, '/tasks/pytorch-cifar10-vgg11.py --num_train_epochs 2'), (72, 73, 8, '/tasks/pytorch-cifar10-vgg11.py --num_train_epochs 1'), (73, 115, 8, '/tasks/pytorch-cifar10-vgg11.py --num_train_epochs 2')]

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
# PHILLY - 0.7 * 1 + 0.15 * 2 + 0.1 * 4 + 0.05 * 8 = 1.8
SWEEPS = {
	"48": { # Final Sweep -- OVERLOADED util 
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
	"47": { # Philly trace sweep - nowait, constant wait, compute wait, starburst
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
		    "policy": ['starburst', 'constant', 'constant_optimal'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [0.75] 
        }
    },
	"46": { # Sweep of every model and gpu combination
		"fixed_values": {
            "batch_time": 10 * 500,#120, 
	        "total_jobs": 500, #NOTE: This does not affected when running "collect_runtimes"
		    "time_constrained": False,
            "mean_duration": 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3,
		    "spill_to_cloud": False,
		    "onprem_only": True,
		    "job_type": "train",
			"image": 'gcr.io/sky-burst/skyburst:latest',
			"collect_runtimes": True,
        },
	    "varying_values": {	
		    "policy": ['onprem_only'],
            "train_names": [all_models],
            "arrival_rate": [1] 
        }
    },
	"45": { # Philly trace sweep - nowait, constant wait, compute wait, starburst
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
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
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
		    "policy": ['starburst', 'constant', 'constant_optimal'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [0.75] 
        }
    },
	"44": { # Sweep of every model and gpu combination
		"fixed_values": {
            "batch_time": 10 * 500,#120, 
	        "total_jobs": 500, #NOTE: This does not affected when running "collect_runtimes"
		    "time_constrained": False,
            "mean_duration": 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3,
		    "spill_to_cloud": False,
		    "onprem_only": True,
		    "job_type": "train",
			"image": 'gcr.io/sky-burst/skyburst:latest',
			"collect_runtimes": True,
			#"train_names": ["pytorch-cifar10-mobilenet_v3_small"],#["pytorch-cifar10-efficientnet_v2_m"],#["pytorch-mnist"], #["huggingface-bert-tiny-wikitext2-1epoch"],#["pytorch-mnist"],#["pytorch-cifar10-mobilenet_v3_small"], #["pytorch-cifar10-efficientnet_v2_m"],#["huggingface-bert-tiny-wikitext2-1epoch"],
			#"train_dist": [1],
        },
	    "varying_values": {	
		    "policy": ['onprem_only'], # Computes the optimal values
            "train_names": [["pytorch-cifar10-efficientnet_v2_m", "pytorch-cifar10-mobilenet_v3_small", "pytorch-cifar10-resnet101", "pytorch-cifar10-resnet50", "pytorch-cifar10-resnext50_32x4d"]],#[["huggingface-bert-tiny-wikitext2-1epoch", "pytorch-cifar10-efficientnet_v2_m"]],
            "arrival_rate": [1] 
        }
    },
	"43": { # Sleep no cloud
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 120, 
            "mean_duration": 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3,
		    "spill_to_cloud": False 
        },
	    "varying_values": {	
		    "policy": ['constant', 'starburst'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [1] 
        }
    },
	"42": { # Philly trace sweep - nowait, constant wait, compute wait, starburst # TODO: Get constant weight 
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 120, 
            "mean_duration": 1800,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": False, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3,
            "arrival_rate": 1/101, 
	        "time_constrained": False,
        },
	    "varying_values": {	
		    "policy": ['starburst', 'constant_optimal', 'constant'], # Perfomr high sys util + no wait, constant, starburst  
            "wait_time": [3],
            "arrival_rate": [1/101] 
        }
    },
	"41": { # Run real world job with short duration ``` no variance ``` exponential arrival rate
		"fixed_values": {
			"job_type": "train",
			"image": 'gcr.io/sky-burst/skyburst:latest',
			"train_names": ["pytorch-cifar10-mobilenet_v3_small"],#["pytorch-cifar10-efficientnet_v2_m"],#["pytorch-mnist"], #["huggingface-bert-tiny-wikitext2-1epoch"],#["pytorch-mnist"],#["pytorch-cifar10-mobilenet_v3_small"], #["pytorch-cifar10-efficientnet_v2_m"],#["huggingface-bert-tiny-wikitext2-1epoch"],
			"train_dist": [1],
			#"setup_script": "python /tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 32 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --num_train_epochs 1", 
            "batch_time": 120, 
            "mean_duration": 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3,
		    "spill_to_cloud": False 
        },
	    "varying_values": {	
		    "policy": ['starburst', 'fixed'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [1] 
        }
    },
	"40": { # Philly trace sweep - nowait, constant wait, compute wait, starburst
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 120, 
            "mean_duration": 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3
        },
	    "varying_values": {	
		    "policy": ['starburst', 'compute_optimal', 'constant_optimal', 'constant'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [1] 
        }
    },
	"39": { # Philly trace sweep - nowait, constant wait, compute wait, starburst
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 120, 
            "mean_duration": 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0, 1, 0, 0],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3
        },
	    "varying_values": {	
		    "policy": ['starburst', 'fixed'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [1] 
        }
    },
	"38": { # Philly trace sweep - nowait, constant wait, compute wait, starburst
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 120, 
            "mean_duration": 30,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": True, 
            "uniform_arrival": 2,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3
        },
	    "varying_values": {	
		    "policy": ['fixed', 'starburst'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [1] 
        }
    },
	"37": { # Philly trace sweep - nowait, constant wait, compute wait, starburst
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 120, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_dist":[0.25, 0.25, 0.25, 0.25],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
		    "gpu_dist": [0.7, 0.15, 0.1, 0.05],
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": True, 
            "uniform_arrival": 3,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1,
	        "wait_time": 3
        },
	    "varying_values": {	
		    "policy": ['fixed', 'constant_wait', 'compute_wait', 'starburst'], # Computes the optimal values
            "wait_time": [3],
            "arrival_rate": [1] 
        }
    },
	"36": { # Real world workload
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 60, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[88],
	        "cpu_dist": [1],
            "gpu_sizes": [8],
            "gpu_dist": [1],
            "uniform_submission": True, 
            "uniform_arrival": 3,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
		    "policy": ['fixed', 'constant_wait', 'runtime_wait', 'resource_wait','compute_wait', 'starburst'],
            #"arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [10],
            "arrival_rate": [1] 
        }
    },
	"35": { # Real world workload
		"fixed_values": {
			"image": "gcr.io/sky-burst/skyburst:latest",
            "batch_time": 60, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 3,
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
	"34": { # Testing small and large batches for onprem only and cloud spillover
		"fixed_values": {
            "batch_time": 120, 
            "mean_duration": 30,
            "waiting_policy": "fifo_wait",
            "gpu_dist": [1],
            "gpu_sizes": [8],
	        "cpu_dist":[1],
	        "cpu_sizes": [88],
            "uniform_submission": True, 
            "uniform_arrival": 3,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [2, 3, 5, 10],
            "arrival_rate": [1],
            #"setup_script": "/tasks/*.sh"
        }
    },
	"33": { # Testing small and large batches for onprem only and cloud spillover
		"fixed_values": {
            "batch_time": 120, 
            "mean_duration": 30,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 3,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [2, 3, 5, 10],
            "arrival_rate": [1],
            #"setup_script": "/tasks/*.sh"
        }
    },
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
            "batch_time": 120, 
            "mean_duration": 15,
            "waiting_policy": "fifo_wait",
            "cpu_sizes":[0.1, 0.1, 0.1, 0.1],
            "gpu_sizes": [1, 2, 4, 8],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],
	        "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "uniform_submission": True, 
            "uniform_arrival": 3,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
	        "gpus_per_node": 8,
            "sched_tick": 0.1
        },
	    "varying_values": {	
            "arrival_rate": [3], #TODO: Figure out the optimal values
            "wait_time": [0, 5, 10, 15],
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
    },

	"2a": { # High System Util - nowait, constant wait, compute wait, starburst
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
    "1a": { # High System Util - nowait, constant wait, compute wait, starburst
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
    "0a": { # Philly trace sweep - nowait, constant wait, compute wait, starburst
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


TRAINING_JOBS_BASH = {
	"huggingface-bert-tiny-wikitext2-1epoch": {
		"train_script": "huggingface-bert-tiny-wikitext2-1epoch.sh",
        "estimated_training_runtime": 300,
    },
    
	"huggingface-bert-tiny-wikitext2-1epoch": {
        "train_script": "python /tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 32 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --num_train_epochs 1", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            1: 180,
            2: 360, 
            3: 720,
            4: 1440
        } 
    },
    "pytorch-cifar10-efficientnet_v2_m": {
	    "train_script": "pytorch-cifar10-efficientnet_v2_m.sh", # TODO: support argparse 
	    "estimated_training_runtime": 600 #10 minutes
    },
    "pytorch-cifar10-mobilenet_v3_small": {
	    "train_script": "python /tasks/pytorch-cifar10-mobilenet_v3_small.py",
	    "estimated_training_runtime": 600 #10 minutes
    },
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

MISC = {
	# Language models
    "huggingface-bert-wikitext": {
        "train_script": "python /tasks/huggingface-bert-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 32 --hidden_size 128 --num_hidden_layers 2 --num_attention_heads 4 --num_train_epochs 1", 
        "estimated_training_runtime": 180, #2-4 minutes
        "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "args": {
            "--dataset": "wikitext-2",
            "--per_device_train_batch_size": "32",
	        "--hidden_size": "128",
	        "--num_hidden_layers": "2",
	        "--num_attention_heads": "4", 
	        "--num_train_epochs": "1"
        }
    },
    "huggingface-gpt-wikitext": {
	    "train_script": "python /tasks/huggingface-gpt-wikitext.py --dataset wikitext-2 --per_device_train_batch_size 8 --n_embd 512 --n_layer 8 --n_head 8 --num_train_epochs 1",
	    "gpu_runtimes": {
            4: 720,
            8: 1440
        },
        "args": {
            "--dataset": "wikitext-2",
            "--per_device_train_batch_size": "8",
	        "--hidden_size": "128",
	        "--n_embd": "512",
	        "--n_layer": "8",
	        "--n_head": "8",
	        "--num_train_epochs": "1"
        }
    },
}