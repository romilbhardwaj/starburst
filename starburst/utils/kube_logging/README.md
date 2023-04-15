# Kube Logging
To support cluster state logging, follow the below steps to deploy yaml files to your cluster. 

## Prometheus 
- https://devopscube.com/setup-prometheus-monitoring-on-kubernetes/
	- https://github.com/techiescamp/kubernetes-prometheus 

### Steps
```
ACCOUNT=$(gcloud info --format='value(config.account)')
kubectl create clusterrolebinding owner-cluster-admin-binding \
    --clusterrole cluster-admin \
    --user $ACCOUNT

kubectl --context gke_sky-burst_us-central1-c_starburst-cloud create namespace monitoring
kubectl --context gke_sky-burst_us-central1-c_starburst-cloud create -f clusterRole.yaml
kubectl --context gke_sky-burst_us-central1-c_starburst-cloud create -f config-map.yaml
kubectl --context gke_sky-burst_us-central1-c_starburst-cloud create  -f prometheus-deployment.yaml 
kubectl --context gke_sky-burst_us-central1-c_starburst-cloud create -f prometheus-service.yaml --namespace=monitoring
```

### Common Errors
- Prometheus deployment pods are unschedulable
	- Solution: Increase total number of nodes to allow for pod to be scheduled

## Kube-state-metrics
- https://devopscube.com/setup-kube-state-metrics/
	- https://github.com/kubernetes/kube-state-metrics/tree/main/examples/standard

### Steps
```
kubectl --context gke_sky-burst_us-central1-c_starburst-cloud apply -f kube-state-metrics-configs/
```