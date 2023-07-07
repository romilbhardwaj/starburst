import logging
import re
from typing import Dict

from kubernetes import client, config
from kubernetes.client import models
import yaml

from starburst.cluster_managers.manager import Manager
from starburst.types.job import Job

client.rest.logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def parse_resource_cpu(resource_str):
    """ Parse CPU string to cpu count. """
    unit_map = {'m': 1e-3, 'K': 1e3}
    value = re.search(r'\d+', resource_str).group()
    unit = resource_str[len(value):]
    return float(value) * unit_map.get(unit, 1)


def parse_resource_memory(resource_str):
    """ Parse resource string to megabytes. """
    unit_map = {'Ki': 2**10, 'Mi': 2**20, 'Gi': 2**30, 'Ti': 2**40}
    value = re.search(r'\d+', resource_str).group()
    unit = resource_str[len(value):]
    return float(value) * unit_map.get(unit, 1) / (2**20
                                                   )  # Convert to megabytes


def _plan_pod_allocation(pod, available_resources):
    """
    Plan pod allocation.

    Args:
        pod: Pod object.
        available_resources: Available resources per node.
    """
    # Limited to single node pods for now.
    cpu_resources = parse_resource_cpu(
        pod.spec.containers[0].resources.requests.get("cpu", 0))
    gpu_resources = float(pod.spec.containers[0].resources.requests.get(
        "nvidia.com/gpu", 0))
    for node_name, node_resources in available_resources.items():
        if node_resources["cpu"] >= cpu_resources and node_resources[
                "gpu"] >= gpu_resources:
            return node_name
    return None


class KubernetesManager(Manager):
    """ Kubernetes manager.

    Provides helper methods to:
    1. Submit job YAMLs to Kubernetes
    2. Get job status
    3. Get cluster resources
    """

    def __init__(self, cluster_name: str, namespace: str = 'default'):
        super().__init__(cluster_name)
        self.namespace = namespace
        # Load kubernetes config for the given context
        config.load_kube_config(context=self.cluster_name)
        # Create kubernetes client
        self.core_v1 = client.CoreV1Api()
        self.batch_v1 = client.BatchV1Api()

        # Keep track of previous job.
        self.previous_job = None
        self.previous_job_status = None

    def get_cluster_resources(self):
        """ Gets total cluster resources for each node."""
        limit = None
        continue_token = ""
        nodes, _, _ = self.core_v1.list_node_with_http_info(
            limit=limit, _continue=continue_token)
        nodes = nodes.items

        # Initialize a dictionary to store available resources per node
        cluster_resources = {}
        for node in nodes:
            name = node.metadata.name
            node_cpu = parse_resource_cpu(node.status.capacity['cpu'])
            node_memory = parse_resource_memory(node.status.capacity['memory'])
            node_gpu = int(node.status.capacity.get('nvidia.com/gpu', 0))
            cluster_resources[name] = {
                'cpu': node_cpu,
                'memory': node_memory,  # MB
                'gpu': node_gpu
            }
        return cluster_resources

    def get_allocatable_resources(self) -> Dict[str, Dict[str, int]]:
        """ Get allocatable resources per node. """
        # Get the nodes and running pods
        limit = None
        continue_token = ""
        nodes, _, _ = self.core_v1.list_node_with_http_info(
            limit=limit, _continue=continue_token)
        nodes = nodes.items

        available_resources = {}
        for node in nodes:
            node_name = node.metadata.name
            node_cpu = parse_resource_cpu(node.status.allocatable['cpu'])
            node_memory = parse_resource_memory(
                node.status.allocatable['memory'])
            node_gpu = int(node.status.allocatable.get('nvidia.com/gpu', 0))
            available_resources[node_name] = {
                'cpu': node_cpu,
                'memory': node_memory,
                'gpu': node_gpu
            }
        pods, _, _ = self.core_v1.list_pod_for_all_namespaces_with_http_info(
            limit=limit, _continue=continue_token)
        pods = pods.items

        for pod in pods:
            if pod.status.phase in [
                    'Running', 'Pending'
            ] and pod.metadata.namespace == self.namespace:
                node_name = pod.spec.node_name
                if node_name is None:
                    # Hallucinate - Find node that can fit the pod
                    node_name = _plan_pod_allocation(pod, available_resources)
                    if node_name is None:
                        continue
                assert node_name in available_resources, (
                    f"Node {node_name} "
                    "not found in cluster resources.")
                for container in pod.spec.containers:
                    if container.resources.requests:
                        available_resources[node_name][
                            'cpu'] -= parse_resource_cpu(
                                container.resources.requests.get('cpu', '0m'))
                        available_resources[node_name][
                            'memory'] -= parse_resource_memory(
                                container.resources.requests.get(
                                    'memory', '0Mi'))
                        available_resources[node_name]['gpu'] -= int(
                            container.resources.requests.get(
                                'nvidia.com/gpu', 0))
        return available_resources

    def can_fit(self, job: Job) -> bool:
        """
        Check if a job can fit in the cluster.

        Args:
            job: Job object containing the YAML file.
        """
        if self.previous_job:
            self.previous_job_status = self._get_job_status(
                self.previous_job.name)
            if self.previous_job_status.active != 1:
                return False

        job_resources = job.resources
        available_cluster_resources = self.get_allocatable_resources()

        # Multinode jobs not supported.
        for _, node_resources in available_cluster_resources.items():
            if node_resources["cpu"] >= job_resources.get("cpu", 0) and \
              node_resources["memory"] >= job_resources.get("memory", 0) and \
              node_resources["gpu"] >= job_resources.get("gpu", 0):
                return True
        return False

    def submit_job(self, job: Job):
        """
        Submit a YAML which contains the Kubernetes Job declaration using the
        batch api.

        Args:
            job: Job object containing the YAML file.
        """
        # Parse the YAML file into a dictionary
        job_dict = job.job_yaml  #yaml.safe_load(job.job_yaml)
        # Create a Kubernetes job object from the dictionary
        k8s_job = models.V1Job()
        # Append random string to job name to avoid name collision
        k8s_job.metadata = models.V1ObjectMeta(
            name=str(job_dict['metadata']['name']))
        k8s_job.spec = models.V1JobSpec(template=job_dict['spec']['template'])
        self.batch_v1.create_namespaced_job(namespace=self.namespace,
                                            body=k8s_job)
        self.previous_job = job

    def _get_job_status(self, job_name):
        """ Get job status. """
        job = self.batch_v1.read_namespaced_job(job_name,
                                                namespace=self.namespace)
        return job.status