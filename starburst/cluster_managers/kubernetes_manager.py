import logging
import re
import time
from typing import Dict, Optional

import yaml
from kubernetes import client, config
from kubernetes.client import models

from starburst.types.job import Job

client.rest.logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class KubernetesManager(object):
    """ Kubernetes manager.

    Provides helper methods to:
    1. Submit job YAMLs to Kubernetes
    2. Get job status
    3. Get cluster resources
    """

    def __init__(self, kube_context=None):
        # Load kubernetes config for the given context
        config.load_kube_config(context=kube_context)
        # Create kubernetes client
        self.core_v1 = client.CoreV1Api()
        self.batch_v1 = client.BatchV1Api()


    def get_total_cluster_resources(self):
        """ Get cluster resources. """
        nodes = self.core_v1.list_node()
        total_res = {
            "cpu": 0,
            "memory": 0,
            "gpu": 0,
        }
        for node in nodes.items:
            total_res["cpu"] += int(node.status.capacity["cpu"])
            total_res["memory"] += int(node.status.capacity["memory"][:-2])
            total_res["gpu"] += int(node.status.capacity.get("nvidia.com/gpu", 0))
        return total_res

    def get_total_cluster_resource_usage(self):
        """ Get cluster resources usage """
        nodes = self.core_v1.list_node()
        total_res = {
            "cpu": 0,
            "memory": 0,
            "gpu": 0,
        }
        for node in nodes.items:
            total_res["cpu"] += int(node.status.allocatable["cpu"])
            total_res["memory"] += int(node.status.allocatable["memory"][:-2])
            total_res["gpu"] += int(node.status.allocatable.get("nvidia.com/gpu", 0))
        return total_res

    @staticmethod
    def parse_resource_cpu(resource_str):
        """ Parse CPU string to cpu count. """
        unit_map = {'m': 1e-3, 'K': 1e3}
        value = re.search(r'\d+', resource_str).group()
        unit = resource_str[len(value):]
        return float(value) * unit_map.get(unit, 1)

    @staticmethod
    def parse_resource_memory(resource_str):
        """ Parse resource string to megabytes. """
        unit_map = {'Ki': 2 ** 10, 'Mi': 2 ** 20, 'Gi': 2 ** 30, 'Ti': 2 ** 40}
        value = re.search(r'\d+', resource_str).group()
        unit = resource_str[len(value):]
        return float(value) * unit_map.get(unit, 1) / (
                    2 ** 20)  # Convert to megabytes

    def get_allocatable_resources_per_node(self) -> Dict[str, Dict[str, int]]:
        # Get the nodes and running pods
        nodes = self.core_v1.list_node().items
        pods = self.core_v1.list_pod_for_all_namespaces(watch=False).items

        # Initialize a dictionary to store available resources per node
        available_resources = {}

        for node in nodes:
            name = node.metadata.name
            total_cpu = self.parse_resource_cpu(node.status.allocatable['cpu'])
            total_memory = self.parse_resource_memory(
                node.status.allocatable['memory'])
            total_gpu = int(node.status.allocatable.get('nvidia.com/gpu', 0))

            used_cpu = 0
            used_memory = 0
            used_gpu = 0

            for pod in pods:
                if pod.spec.node_name == name and pod.status.phase in ['Running', 'Pending']:
                    for container in pod.spec.containers:
                        if container.resources.requests:
                            used_cpu += self.parse_resource_cpu(
                                container.resources.requests.get('cpu', '0m'))
                            used_memory += self.parse_resource_memory(
                                container.resources.requests.get('memory',
                                                                 '0Mi'))
                            used_gpu += int(container.resources.requests.get(
                                'nvidia.com/gpu', 0))

            available_cpu = total_cpu - used_cpu
            available_memory = total_memory - used_memory
            available_gpu = total_gpu - used_gpu

            available_resources[name] = {
                'cpu': available_cpu,
                'memory': available_memory, # MB
                'gpu': available_gpu
            }

        return available_resources


    def can_fit(self, job: Job) -> Optional[str]:
        """ Check if a job can fit in the cluster. """
        job_resources = job.resources
        cluster_resources = self.get_allocatable_resources_per_node()
        for node_name, node_resources in cluster_resources.items():
            if node_resources["cpu"] >= job_resources.get("cpu", 0) and \
                    node_resources["memory"] >= job_resources.get("memory", 0) and \
                    node_resources["gpu"] >= job_resources.get("gpu", 0):
                return node_name
        return None

    def submit_job(self, job: Job):
        """ Submit a YAML which contains the Kubernetes Job declaration using the batch api"""
        # Parse the YAML file into a dictionary
        job_dict = yaml.safe_load(job.job_yaml)

        # Create a Kubernetes job object from the dictionary
        k8s_job = models.V1Job()
        # Append random string to job name to avoid name collision
        k8s_job.metadata = models.V1ObjectMeta(name=job_dict['metadata']['name'] + '-' + job.job_id)
        k8s_job.spec = models.V1JobSpec(template=job_dict['spec']['template'])

        self.batch_v1.create_namespaced_job(namespace="default", body=k8s_job)


    def get_job_status(self, job_name):
        """ Get job status. """
        job = self.batch_v1.read_namespaced_job_status(job_name, namespace="default")
        return job.status