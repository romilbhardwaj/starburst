from starburst.cluster_managers.kubernetes_manager import KubernetesManager

asdf = KubernetesManager('mluo-cloud')

lol = asdf.get_allocatable_resources()

print(lol)
