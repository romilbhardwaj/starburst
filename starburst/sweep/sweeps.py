DEFAULT_CONFIG = {
    #====================================================================================================#
    #                                            Sweep Parameters                                        #
    #====================================================================================================#
    # Sweep currently supports 3 types of jobs: CPU sleep jobs ('cpu_sleep'), GPU sleep jobs ('gpu_sleep'), and
    # real-life GPU training jobs ('gpu_train').
    'workload_type': 'cpu_sleep',
    # Total time (in seconds) where incoming jobs are submitted. After this time, no more jobs are submitted.
    'submit_time': 300,
    # Random seed for the job generator. This is used to generate the same set of jobs across different runs.
    'random_seed': 13,
    #====================================================================================================#
    #                                       Job Generation Parameters                                    #
    #====================================================================================================#
    # Job arrival distribution. Currently, we support two types of distributions: uniform and poisson.
    'arrival_dist': 'uniform',  # 'uniform', 'poisson'
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
    'cpu_sizes': [1, 2, 4, 8, 16, 32],
    # List of probabilities for each CPU size. The length of cpu_dist must be equal to the length of cpu_sizes.
    'cpu_dist': [0, 0.2, 0.2, 0.2, 0.2, 0.2],
    # Distribution of GPU resources requested by jobs. Applies for `workload_type: gpu_sleep, gpu_train`
    # List of GPU sizes that jobs can request. Multi-node jobs are not supported.
    'gpu_sizes': [1, 2, 4, 8],
    # List of probabilities for each GPU size. The length of gpu_dist must be equal to the length of gpu_sizes.
    # The default distribution follows the jobs in the Microsoft Philadelphia Deep Learning cluster.
    'gpu_dist': [0.7, 0.15, 0.1, 0.05],
    # Docker image for all jobs. Pods are launched with this docker image.
    'image': 'gcr.io/deeplearning-platform-release/pytorch-gpu.1-12',
    #====================================================================================================#
    #                                           Cluster Parameters                                       #
    #====================================================================================================#
    # GKE cluster name for on-prem cluster. This is used to submit jobs to the on-prem cluster.
    'onprem_cluster': 'gke_sky-burst_us-central1-c_starburst',
    # GKE cluster name for cloud cluster. This is used to submit jobs to the cloud cluster.
    'cloud_cluster': 'gke_sky-burst_us-central1-c_starburst-cloud',
    #====================================================================================================#
    #                                          Scheduler Parameters                                      #
    #====================================================================================================#
    # Scheduling tick, how often the scheduler is invoked (in seconds).
    'schedule_tick': 1,
    # How jobs should spill to cloud
    # Possible options: ['log', 'cluster', 'skypilot',]
    # 	- Log: Logs the jobs that spill to the cloud.
    # 	- Cluster: Uses `cloud_cluster` (GKE cluster) to submit jobs to the cloud.
    #   - Skypilot: Uses Skypilot to automatically provision a cloud cluster and submit jobs on the cluster.
    "spill_to_cloud": 'log',
    # Queueing policy which sets the order of the jobs in the queue
    # Possible options: ['fifo', 'sjf']
    'queue_policy': 'fifo',
    # Waiting policy which sets how long jobs wait in queue before timing out to the cloud.
    # Possible options: ['infinite', 'constant', 'runtime', 'resource', 'compute']
    'waiting_policy': 'constant',
    # Sets the hyperparameter for each waiting policy
    # 	- Infinite: Waiting coeff doesn't matter
    # 	- Constant: Jobs wait for waiting_coeff seconds.
    # 	- Runtime: Jobs wait for waiting_coeff * job's est. runtime.
    # 	- Resource: Jobs wait for waiting_coeff * job's resource request (GPUs or CPUs).
    # 	- Compute: Jobs wait for waiting_coeff * job's resource request (GPUs or CPUs) * job's est. runtime.
    'waiting_coeff': 15,
    # Estimates the waiting coeff based on the waiting budget. Overrides waiting_coeff if it is set to a non-negative value.
    # Example: If waiting_budget = 0.25, the total waiting budget is 25% of the total job runtime (sum from all generated jobs).
    # The waiting budget is allocated to all jobs based on the waiting policy and a job's characteristics.
    # The waiting coeff can thus be solved algebraically over all jobs.
    'waiting_budget': -1,
    # Minimum waiting waiting for jobs. Equivalent to Kubernetes cluster autoscaler 10 (s) waiting time.
    'min_waiting_time': 10,
    # Removes head of line blocking, allows scheduler to loop through all jobs in the queue.
    'loop': False,
}

FINAL_EXPERIMENTS = {
    "60": {  # True overloaded -- VERIFIED 
        "fixed_values": {
            "batch_time": 3 * 60 * 60,
            "mean_duration": 45 * 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist": [0.25, 0.25, 0.25, 0.25],
            "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],  #Philly Distribution
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": False,  #True, 
            "uniform_arrival": 4,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cluster_size": 1,
            "gpu_workload": True,
            "gpus_per_node": 8,
            "sched_tick": 0.1,
            "wait_time": 5,
            "spill_to_cloud": False,
            "arrival_rate":
            0.75,  # Maxes at 4k jobs bc 3 second interarrival rate
            "sample_real_workloads": True,
            "job_type": "train",
            "image": "gcr.io/sky-burst/skyburst:latest",
        },
        "varying_values": {
            "policy": ['constant', 'starburst',
                       'constant_optimal'],  # Computes the optimal values
            "wait_time": [15],
            "arrival_rate": [
                32 / (60 * 60)
            ]  # job/second ~ 45 minutes per job jobs per hour / 32 gpu cluster  -- system util 75 -- 32 jobs ~ 1.3 jobs * 32 jobs = 41jobs (1 gpu ~ 45min per job) -- 41 / 2 ~ 21 jobs per hour 
        }
    },
    "49": {  # Final Sweep -- OVERLOADED util 
        "fixed_values": {
            "batch_time": 5 * 60 * 60,
            "mean_duration": 45 * 60,
            "waiting_policy": "fifo_wait",
            "cpu_dist": [0.25, 0.25, 0.25, 0.25],
            "cpu_sizes": [i * 11 for i in [1, 2, 4, 8]],
            "gpu_dist": [0.7, 0.15, 0.1, 0.05],  #Philly Distribution
            "gpu_sizes": [1, 2, 4, 8],
            "uniform_submission": False,  #True, 
            "uniform_arrival": 4,
            "onprem_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu-cloud',
            "cloud_cluster": 'gke_sky-burst_us-central1-c_skyburst-gpu',
            "cluster_size": 1,
            "gpu_workload": True,
            "gpus_per_node": 8,
            "sched_tick": 0.1,
            "wait_time": 5,
            "spill_to_cloud": False,
            "arrival_rate":
            0.75,  # Maxes at 4k jobs bc 3 second interarrival rate
            "sample_real_workloads": True,
            "job_type": "train",
            "image": "gcr.io/sky-burst/skyburst:latest",
        },
        "varying_values": {
            "policy": ['constant', 'starburst',
                       'constant_optimal'],  # Computes the optimal values
            "wait_time":
            [15],  # TODO: Specify 10~15 seconds wait -- moved from 5 to 15 
            "arrival_rate": [
                32 / (60 * 60)
            ]  # Moved from 20 to 32 -- job/second ~ 45 minutes per job jobs per hour / 32 gpu cluster  -- system util 75 -- 32 jobs ~ 1.3 jobs * 32 jobs = 41jobs (1 gpu ~ 45min per job) -- 41 / 2 ~ 21 jobs per hour 
        }
    },
}