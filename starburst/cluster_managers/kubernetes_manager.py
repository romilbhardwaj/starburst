import logging
import time
from typing import Dict, Optional

import yaml
from kubernetes import client, config
from kubernetes.client import models

from starburst.types.job import Job

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

    def get_allocatable_resources_per_node(self) -> Dict[str, Dict[str, int]]:
        """ Get allocatable resources per node. """
        nodes = self.core_v1.list_node()
        node_res = {}
        for node in nodes.items:
            node_res[node.metadata.name] = {
                "cpu": int(node.status.allocatable["cpu"]),
                "memory": int(node.status.allocatable["memory"][:-2]),
                "gpu": int(node.status.allocatable.get("nvidia.com/gpu", 0)),
            }
        return node_res

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
        job.job_submit_time = time.time()
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