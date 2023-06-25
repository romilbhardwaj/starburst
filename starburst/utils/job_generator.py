import math
import numpy as np
from typing import List, Dict

import training_dataset

ESIMATED_TIMES = training_dataset.ESTIMATED_TIMES
JOB_GEN_ARRAY = ['arrival_dist', 'arrival_param', 'min_arrival_time', 'mean_duration', 'min_duration', 'max_duration', 'image', 'cpu_dist', 'cpu_sizes', 'gpu_dist', 'gpu_sizes']

class JobGenerator(object):
    def __init__(self, config) -> None:
        self.config = config

    def get_resources(self) -> Dict[str, int]:
        return {'cpu': 1, 'gpu': 0}
    
    def get_interarrival(self):
        arrival_dist = self.config['arrival_dist']
        arrival_param = self.config['arrival_param']
        job_submit_time = 0
        if arrival_dist == 'uniform':
            job_submit_time = arrival_param
        elif arrival_dist == 'poisson':
            job_submit_time = np.random.exponential(scale=1/arrival_param)
        else:
            raise ValueError(f'Unknown arrival distribution {arrival_dist}, must be uniform or poisson.')
        return max(self.config['min_arrival_time'], job_submit_time)

    def get_duration(self):
        mean_duration = self.config['mean_duration']
        min_duration = self.config['min_duration']
        max_duration = self.config['max_duration']
        job_duration = np.random.exponential(scale=mean_duration)
        job_duration = float(np.clip(job_duration, min_duration, max_duration))
        return job_duration

    def get_jinja_template(self):
         return NotImplementedError

    def get_jinja_dict(self, job:dict):
         return NotImplementedError
    
    @property
    def image(self):
        return self.config['image']
    
    @property
    def script(self):
         return NotImplementedError


class CPUSleepJobGenerator(JobGenerator):

    def get_resources(self) -> Dict[str, int]:
        cpus = int(np.random.choice(self.config['cpu_sizes'], p=self.config['cpu_dist']))
        return {'cpu': cpus, 'gpu': 0}
    
    def get_jinja_template(self):
         return 'sleep_job.yaml.jinja'

    def get_jinja_dict(self, job:dict):
        resources = job['resources']
        return {'job': str(job['job_id']), 'script': self.script.format(time=job['job_duration']), 'cpu': resources['cpu'], 'gpu': resources['gpu'], 'image': self.image}
    
    @property
    def script(self):
         return 'echo \"||\" && sleep {time}'


class GPUSleepJobGenerator(JobGenerator):

    def get_resources(self) -> Dict[str, int]:
        gpus = int(np.random.choice(self.config['gpu_sizes'], p=self.config['gpu_dist']))
        return {'cpu': 11 * gpus, 'gpu': gpus}
    
    def get_jinja_template(self):
         return 'sleep_job.yaml.jinja'
    
    def get_jinja_dict(self, job:dict):
        resources = job['resources']
        return {'job': str(job['job_id']), 'script': self.script.format(time=job['job_duration']), 'cpu': resources['cpu'], 'gpu': resources['gpu'], 'image': self.image}

    @property
    def script(self):
         return 'nvidia-smi --query-gpu=uuid --format=csv,noheader && echo \"||\" && sleep {time}'


# Stateful job generator, keeps track of previous gpu and script.
class GPUTrainJobGenerator(JobGenerator):

    def __init__(self, config) -> None:
        super().__init__(config)
        self.cached_values = {'gpus': 0, 'script': None}

    def get_resources(self) -> Dict[str, int]:
        gpus = int(np.random.choice(self.config['gpu_sizes'], p=self.config['gpu_dist']))
        self.cached_values['gpu'] = gpus
        return {'cpu': 11 * gpus, 'gpu': gpus}
    
    def get_duration(self):
        generated_duration = super().get_duration()
        estimated_duration, script = sample_gpu_train_job(self.cached_values['gpu'], generated_duration)
        self.cached_values['script'] = script
        return estimated_duration

    def get_jinja_template(self):
        return 'train_job.yaml.jinja'
    
    def get_jinja_dict(self, job:dict):
        resources = job['resources']
        return {'job': str(job['job_id']), 'script': self.script, 'cpu': resources['cpu'], 'gpu': resources['gpu'], 'image': self.image}

    @property
    def script(self):
         return self.cached_values['script']

    @property
    def image(self):
        return 'gcr.io/deeplearning-platform-release/pytorch-gpu.1-12'


def sample_gpu_train_job(gpu, runtime):
	"return script the closest fils gpu runtime pair"
	jobs = [(j[1], j[3]) for j in training_dataset.ESTIMATED_TIMES if j[2] == gpu]
	#id = 0
	min_delta = math.inf
	min_id = 0  
	for i in range(len(jobs)):
		job = jobs[i]
		delta = abs(jobs[i][0] - runtime)
		if delta <= min_delta: 
			min_delta = delta
			min_id = i
	return jobs[min_id]