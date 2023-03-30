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
3. You can now submit k8s jobs to starburst. We have an example job in `examples/example_job.yaml`. Use the provided script to submit the job to starburst.
   ```console
   python -m starburst.drivers.submit_job --job-yaml examples/example_job.yaml
   ``` 
4. If you have chosen the `fifo_onprem_only` policy, your job should now be running on the onprem cluster! 🥳

# Architecture
* Starburst uses an async architecture. `Events` are at the heart of Starburst. We use asyncio to run an event loop to process events in the queue. 
* Every event must come from an `EventSource`.
  *  `SchedTickEventSource` generates `SchedTick` events for the scheduler.
  *  `GRPCEventSource` generates events from the GRPC Job Submission Server. I.e., whenever a job is submitted, a `JobAddEvent` is added to the event queue.
* Policies are defined in `starburst/policies`.
  * To define a custom policy, you must implement the `process_queue` method from `BasePolicy`. This method is called every time a `SchedTick` event is processed.
  * The policy can access the cluster state information and queue state to make waiting/scheduling decisions.