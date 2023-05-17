from kubernetes.client import V1PodTemplateSpec
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1PodSpec
from kubernetes.client import V1Container

from kubeflow.training.utils import utils
from kubeflow.training.models import V1ReplicaSpec
from kubeflow.training.models import KubeflowOrgV1TFJob
from kubeflow.training.models import KubeflowOrgV1TFJobSpec
from kubeflow.training.models import V1RunPolicy
from kubeflow.training import TrainingClient

# TODO: Resolve kubeflow logs from overriding starburst logs initialized in main_driver.py

#import logging
#logging.getLogger('kubeflow.training').setLevel(logging.DEBUG)

def submit_tf_job():
	"""
	https://github.com/kubeflow/training-operator/blob/master/sdk/python/examples/kubeflow-tfjob-sdk.ipynb 
	"""

	# TODO: Debug integration with starburst once logging error resolved
	
	kubeflow_client = TrainingClient()
	namespace = utils.get_default_target_namespace()

	container = V1Container(
		name="tensorflow",
		image="gcr.io/kubeflow-ci/tf-mnist-with-summaries:1.0",
		command=[
			"python",
			"/var/tf_mnist/mnist_with_summaries.py",
			"--log_dir=/train/logs", "--learning_rate=0.01",
			"--batch_size=150"
			]
	)

	worker = V1ReplicaSpec(
		replicas=2,
		restart_policy="Never",
		template=V1PodTemplateSpec(
			spec=V1PodSpec(
				containers=[container]
			)
		)
	)

	chief = V1ReplicaSpec(
		replicas=1,
		restart_policy="Never",
		template=V1PodTemplateSpec(
			spec=V1PodSpec(
				containers=[container]
			)
		)
	)

	ps = V1ReplicaSpec(
		replicas=1,
		restart_policy="Never",
		template=V1PodTemplateSpec(
			spec=V1PodSpec(
				containers=[container]
			)
		)
	)

	tfjob = KubeflowOrgV1TFJob(
		api_version="kubeflow.org/v1",
		kind="TFJob",
		metadata=V1ObjectMeta(name="mnist",namespace=namespace),
		spec=KubeflowOrgV1TFJobSpec(
			run_policy=V1RunPolicy(clean_pod_policy="None"),
			tf_replica_specs={"Worker": worker,
							"Chief": chief,
							"PS": ps}
		)
	)

	kubeflow_tfjob = kubeflow_client.create_tfjob(tfjob, namespace=namespace)