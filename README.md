# Starburst 🌟

A hybrid cloud scheduler that enables you to run your k8s workloads on-prem and in the cloud.

# Quickstart
0. `pip install -e . && pip install -r requirements.txt`
1. Setup your k8s clusters. These can be either GKE clusters or setup locally for quick debug. Here I'll setup two k8s clusters locally on my laptop. 
   ```console
   # This creates two clusters on your laptop
   kind create cluster --name onprem
   kind create cluster --name cloud
   ```
   After you have done this, make sure they show up in `kubectl config get-contexts`.
2. Once you have your two k8s clusters ready, run Starburst:
   ```console
   python -m starburst.drivers.main_driver --policy fifo_onprem_only
   ```
3. You can now submit k8s jobs to starburst. We have an example job in `examples/example_job.yaml`. In a new terminal, submit the job to starburst.
   ```console
   python -m starburst.drivers.submit_job --job-yaml examples/example_job.yaml
   ```
4. If you have chosen the `fifo_onprem_only` policy, your job should now be running on the onprem cluster! 🥳 You should see an output like:
    ```console
   (base) ➜  drivers git:(main) ✗ python -m starburst.drivers.main_driver --policy fifo_onprem_only
    03-30 15:38:04 | DEBUG  | asyncio                                  || Using selector: KqueueSelector
    03-30 15:38:04 | DEBUG  | grpc._cython.cygrpc                      || Using AsyncIOEngine.POLLER as I/O engine
    03-30 15:38:04 | DEBUG  | starburst.scheduler.starburst_scheduler  || Waiting for event.
    03-30 15:38:04 | DEBUG  | starburst.scheduler.starburst_scheduler  || Sched Tick, type:EventTypes.SCHED_TICK
    03-30 15:38:04 | INFO   | starburst.policies.queue_policies        || Job queue is empty.
    03-30 15:38:04 | DEBUG  | starburst.scheduler.starburst_scheduler  || Waiting for event.
    03-30 15:38:05 | DEBUG  | starburst.scheduler.starburst_scheduler  || Sched Tick, type:EventTypes.SCHED_TICK
    03-30 15:38:05 | INFO   | starburst.policies.queue_policies        || Job queue is empty.
    03-30 15:38:05 | DEBUG  | starburst.scheduler.starburst_scheduler  || Waiting for event.
    03-30 15:38:05 | DEBUG  | starburst.scheduler.starburst_scheduler  || JobAddEvent: Job, name: MyJob, submit: 1680215885.589775, start: 0, end: 0, yaml: apiVersion: batch/v1
    kind: Job
    metadata:
      name: pi
    spec:
      template:
        spec:
          containers:
          - name: pi
            image: perl:5.34.0
            command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
          restartPolicy: Never
      backoffLimit: 4, resources: {'cpu': 1}
    03-30 15:38:05 | DEBUG  | starburst.scheduler.starburst_scheduler  || Waiting for event.
    03-30 15:38:06 | DEBUG  | starburst.scheduler.starburst_scheduler  || Sched Tick, type:EventTypes.SCHED_TICK
    03-30 15:38:06 | DEBUG  | kubernetes.client.rest                   || response body: {"kind":"NodeList","apiVersion":"v1","metadata":{"resourceVersion":"5353"},"items":[{"metadata":{"name":"onprem-control-plane","uid":"d9c2edc6-d34e-437f-96ff-24cff807df21","resourceVersion":"5081","creationTimestamp":"2023-03-30T21:30:05Z","labels":{"beta.kubernetes.io/arch":"arm64","beta.kubernetes.io/os":"linux","kubernetes.io/arch":"arm64","kubernetes.io/hostname":"onprem-control-plane","kubernetes.io/os":"linux","node-role.kubernetes.io/control-plane":"","node.kubernetes.io/exclude-from-external-load-balancers":""},"annotations":{"kubeadm.alpha.kubernetes.io/cri-socket":"unix:///run/containerd/containerd.sock","node.alpha.kubernetes.io/ttl":"0","volumes.kubernetes.io/controller-managed-attach-detach":"true"},"managedFields":[{"manager":"kubelet","operation":"Update","apiVersion":"v1","time":"2023-03-30T21:30:05Z","fieldsType":"FieldsV1","fieldsV1":{"f:metadata":{"f:annotations":{".":{},"f:volumes.kubernetes.io/controller-managed-attach-detach":{}},"f:labels":{".":{},"f:beta.kubernetes.io/arch":{},"f:beta.kubernetes.io/os":{},"f:kubernetes.io/arch":{},"f:kubernetes.io/hostname":{},"f:kubernetes.io/os":{}}},"f:spec":{"f:providerID":{}}}},{"manager":"kubeadm","operation":"Update","apiVersion":"v1","time":"2023-03-30T21:30:07Z","fieldsType":"FieldsV1","fieldsV1":{"f:metadata":{"f:annotations":{"f:kubeadm.alpha.kubernetes.io/cri-socket":{}},"f:labels":{"f:node-role.kubernetes.io/control-plane":{},"f:node.kubernetes.io/exclude-from-external-load-balancers":{}}}}},{"manager":"kube-controller-manager","operation":"Update","apiVersion":"v1","time":"2023-03-30T21:30:28Z","fieldsType":"FieldsV1","fieldsV1":{"f:metadata":{"f:annotations":{"f:node.alpha.kubernetes.io/ttl":{}}},"f:spec":{"f:podCIDR":{},"f:podCIDRs":{".":{},"v:\"10.244.0.0/24\"":{}}}}},{"manager":"kubelet","operation":"Update","apiVersion":"v1","time":"2023-03-30T22:34:36Z","fieldsType":"FieldsV1","fieldsV1":{"f:status":{"f:conditions":{"k:{\"type\":\"DiskPressure\"}":{"f:lastHeartbeatTime":{}},"k:{\"type\":\"MemoryPressure\"}":{"f:lastHeartbeatTime":{}},"k:{\"type\":\"PIDPressure\"}":{"f:lastHeartbeatTime":{}},"k:{\"type\":\"Ready\"}":{"f:lastHeartbeatTime":{},"f:lastTransitionTime":{},"f:message":{},"f:reason":{},"f:status":{}}},"f:images":{}}},"subresource":"status"}]},"spec":{"podCIDR":"10.244.0.0/24","podCIDRs":["10.244.0.0/24"],"providerID":"kind://docker/onprem/onprem-control-plane"},"status":{"capacity":{"cpu":"6","ephemeral-storage":"61202244Ki","hugepages-1Gi":"0","hugepages-2Mi":"0","hugepages-32Mi":"0","hugepages-64Ki":"0","memory":"8039820Ki","pods":"110"},"allocatable":{"cpu":"6","ephemeral-storage":"61202244Ki","hugepages-1Gi":"0","hugepages-2Mi":"0","hugepages-32Mi":"0","hugepages-64Ki":"0","memory":"8039820Ki","pods":"110"},"conditions":[{"type":"MemoryPressure","status":"False","lastHeartbeatTime":"2023-03-30T22:34:36Z","lastTransitionTime":"2023-03-30T21:30:03Z","reason":"KubeletHasSufficientMemory","message":"kubelet has sufficient memory available"},{"type":"DiskPressure","status":"False","lastHeartbeatTime":"2023-03-30T22:34:36Z","lastTransitionTime":"2023-03-30T21:30:03Z","reason":"KubeletHasNoDiskPressure","message":"kubelet has no disk pressure"},{"type":"PIDPressure","status":"False","lastHeartbeatTime":"2023-03-30T22:34:36Z","lastTransitionTime":"2023-03-30T21:30:03Z","reason":"KubeletHasSufficientPID","message":"kubelet has sufficient PID available"},{"type":"Ready","status":"True","lastHeartbeatTime":"2023-03-30T22:34:36Z","lastTransitionTime":"2023-03-30T21:30:28Z","reason":"KubeletReady","message":"kubelet is posting ready status"}],"addresses":[{"type":"InternalIP","address":"172.18.0.2"},{"type":"Hostname","address":"onprem-control-plane"}],"daemonEndpoints":{"kubeletEndpoint":{"Port":10250}},"nodeInfo":{"machineID":"a38b913a7769497f97b9b76ac75aba12","systemUUID":"a38b913a7769497f97b9b76ac75aba12","bootID":"affd12b5-dd4e-4981-b46b-bcb322754471","kernelVersion":"5.15.49-linuxkit","osImage":"Ubuntu 22.04.1 LTS","containerRuntimeVersion":"containerd://1.6.9","kubeletVersion":"v1.25.3","kubeProxyVersion":"v1.25.3","operatingSystem":"linux","architecture":"arm64"},"images":[{"names":["docker.io/library/perl@sha256:2584f46a92d1042b25320131219e5832c5b3e75086dfaaff33e4fda7a9f47d99","docker.io/library/perl:5.34.0"],"sizeBytes":327591300},{"names":["registry.k8s.io/etcd:3.5.4-0"],"sizeBytes":81120118},{"names":["docker.io/library/import-2022-10-25@sha256:c666c2ddbc056f8aba649a2647a26d3f6224bce857613b91be6075c88ca963a1","registry.k8s.io/kube-apiserver:v1.25.3"],"sizeBytes":74211819},{"names":["docker.io/library/import-2022-10-25@sha256:8584d5d11885180c547784653a575ab8f6a983b6557bc77ddf577a4a0b4b6dec","registry.k8s.io/kube-controller-manager:v1.25.3"],"sizeBytes":62283900},{"names":["docker.io/library/import-2022-10-25@sha256:2f5536b3e12d9862d10103b10756684ac451b11eda25b62b9ceff71fdc3fd657","registry.k8s.io/kube-proxy:v1.25.3"],"sizeBytes":59581437},{"names":["docker.io/library/import-2022-10-25@sha256:f935a2ebcacd3788ccd8e8e800fbdf1fc5b80892db99d037797cddf4089273ed","registry.k8s.io/kube-scheduler:v1.25.3"],"sizeBytes":50618490},{"names":["docker.io/kindest/kindnetd:v20221004-44d545d1"],"sizeBytes":23673212},{"names":["docker.io/kindest/local-path-provisioner:v0.0.22-kind.0"],"sizeBytes":15578330},{"names":["registry.k8s.io/coredns/coredns:v1.9.3"],"sizeBytes":13423150},{"names":["docker.io/kindest/local-path-helper:v20220607-9a4d8d2a"],"sizeBytes":2749880},{"names":["registry.k8s.io/pause:3.7"],"sizeBytes":268400}]}}]}
    
    {'apiVersion': 'batch/v1', 'kind': 'Job', 'metadata': {'name': 'pi'}, 'spec': {'template': {'spec': {'containers': [{'name': 'pi', 'image': 'perl:5.34.0', 'command': ['perl', '-Mbignum=bpi', '-wle', 'print bpi(2000)']}], 'restartPolicy': 'Never'}}, 'backoffLimit': 4}}
    03-30 15:38:06 | DEBUG  | kubernetes.client.rest                   || response body: {"kind":"Job","apiVersion":"batch/v1","metadata":{"name":"pi-933950","namespace":"default","uid":"57824752-fdad-478e-b626-5cb5caccef77","resourceVersion":"5354","generation":1,"creationTimestamp":"2023-03-30T22:38:06Z","labels":{"controller-uid":"57824752-fdad-478e-b626-5cb5caccef77","job-name":"pi-933950"},"annotations":{"batch.kubernetes.io/job-tracking":""},"managedFields":[{"manager":"OpenAPI-Generator","operation":"Update","apiVersion":"batch/v1","time":"2023-03-30T22:38:06Z","fieldsType":"FieldsV1","fieldsV1":{"f:spec":{"f:backoffLimit":{},"f:completionMode":{},"f:completions":{},"f:parallelism":{},"f:suspend":{},"f:template":{"f:spec":{"f:containers":{"k:{\"name\":\"pi\"}":{".":{},"f:command":{},"f:image":{},"f:imagePullPolicy":{},"f:name":{},"f:resources":{},"f:terminationMessagePath":{},"f:terminationMessagePolicy":{}}},"f:dnsPolicy":{},"f:restartPolicy":{},"f:schedulerName":{},"f:securityContext":{},"f:terminationGracePeriodSeconds":{}}}}}}]},"spec":{"parallelism":1,"completions":1,"backoffLimit":6,"selector":{"matchLabels":{"controller-uid":"57824752-fdad-478e-b626-5cb5caccef77"}},"template":{"metadata":{"creationTimestamp":null,"labels":{"controller-uid":"57824752-fdad-478e-b626-5cb5caccef77","job-name":"pi-933950"}},"spec":{"containers":[{"name":"pi","image":"perl:5.34.0","command":["perl","-Mbignum=bpi","-wle","print bpi(2000)"],"resources":{},"terminationMessagePath":"/dev/termination-log","terminationMessagePolicy":"File","imagePullPolicy":"IfNotPresent"}],"restartPolicy":"Never","terminationGracePeriodSeconds":30,"dnsPolicy":"ClusterFirst","securityContext":{},"schedulerName":"default-scheduler"}},"completionMode":"NonIndexed","suspend":false},"status":{}}
    
    03-30 15:38:06 | INFO   | starburst.policies.queue_policies        || Onprem cluster can fit the Job, name: MyJob, submit: 1680215886.5699992, start: 0, end: 0
    03-30 15:38:06 | DEBUG  | starburst.scheduler.starburst_scheduler  || Waiting for event.
    03-30 15:38:07 | DEBUG  | starburst.scheduler.starburst_scheduler  || Sched Tick, type:EventTypes.SCHED_TICK
    03-30 15:38:07 | INFO   | starburst.policies.queue_policies        || Job queue is empty.
    ```

# Architecture
* Starburst uses an async architecture. `Events` are at the heart of Starburst. We use asyncio to run an event loop to process events in the queue. 
* Every event must come from an `EventSource`.
  *  `SchedTickEventSource` generates `SchedTick` events for the scheduler.
  *  `GRPCEventSource` generates events from the GRPC Job Submission Server. I.e., whenever a job is submitted, a `JobAddEvent` is added to the event queue.
* Policies are defined in `starburst/policies`.
  * To define a custom policy, you must implement the `process_queue` method from `BasePolicy`. This method is called every time a `SchedTick` event is processed.
  * The policy can access the cluster state information and queue state to make waiting/scheduling decisions.