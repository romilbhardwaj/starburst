"""
Submits jobs to the on-prem cluster and cloud cluster.

Description:
This module contains the job submission service, which is responsible for
submitting jobs to the on-prem cluster and cloud cluster via the
`submission_loop` method. Jobs are submitted to cluster based on their arrival
times. When all jobs have completed, the service exits.
"""
import logging
import os
import re
import subprocess
import time
import tempfile
import traceback
from typing import Any, Dict

from kubernetes import client, config
import yaml

from starburst.sweep import utils, submit_sweep
from starburst.utils import LogManager

JOB_SUBMISSION_TICK = 0.05
JOB_COMPLETION_TICK = 1

logger = logging.getLogger(__name__)


class JobStateTracker(object):
    """
    Tracks the job submission and completion over the cloud & on-prem cluster.
    """

    def __init__(self, num_jobs):
        self.submit_state = {idx: False for idx in range(num_jobs)}
        self.finish_state = {idx: False for idx in range(num_jobs)}

    def update_submit_idx(self, idx: int, state: Any):
        """
        Updates the submission state of the job with the given index.
        """
        self.submit_state[idx] = state

    def update_submit_file_state(self, idx: int, file_path: str):
        """
        Updates the submission state of the job with the given index to a file.
        """
        file_path = os.path.abspath(file_path)
        job_data = utils.load_yaml_file(file_path)
        job_data[idx]["scheduler_submit_time"] = self.submit_state[idx]
        utils.save_yaml_object(job_data, file_path)

    def check_if_jobs_submitted(self) -> bool:
        """
        Check if all jobs have been submitted.
        """
        return all(self.submit_state.values())

    def update_finished_jobs(self, onprem_cluster: Dict[str, Any],
                             cloud_cluster: Dict[str, Any]):
        """
        Updates the finished state of the jobs.        
        For the on-premise cluster,it polls Kubernetes for the job status.
        For the cloud-cluster, depending on the spillover configuration,
        it either polls the cloud cluster or parses the log file.

        Args:
            onprem_cluster (Dict[str, Any]): On-prem cluster configuration.
            cloud_cluster (Dict[str, Any]): Cloud cluster configuration.
        """

        spill_to_cloud = cloud_cluster["spill_to_cloud"] == 'log'
        configs = [onprem_cluster, cloud_cluster]
        for idx, cluster_config in enumerate(configs):
            if idx == 1 and spill_to_cloud:
                cloud_log_path = cloud_cluster["cloud_cluster_path"]
                cloud_jobs = parse_spillover_jobs(file_path=cloud_log_path)
                for job_idx in cloud_jobs:
                    self.finish_state[job_idx] = True
                continue
            config.load_kube_config(context=cluster_config["name"])
            api = client.BatchV1Api()
            job_list, _, _ = api.list_namespaced_job_with_http_info(
                namespace="default", limit=None, _continue="")
            for job_idx, job_state in self.finish_state.items():
                try:
                    if not job_state:
                        curr_job = find_job_with_substring(
                            job_list.items, "job-" + str(job_idx))
                        if curr_job.status.succeeded == 1:
                            self.finish_state[job_idx] = True
                except Exception:
                    pass

    def check_if_jobs_finished(self) -> bool:
        return all(self.finish_state.values())


def find_job_with_substring(jobs_http: dict, substring: str):
    for job in jobs_http:
        if substring in job.metadata.name:
            return job
    return None


def parse_spillover_jobs(file_path: str):
    """
    Parses the log file to find jobs that were spilled over to the cloud.

    Args:
            file_path (str): Path to the log file.
    """
    with open(file_path, "r") as f:
        cloud_log_list = f.read().split("\n")
    log_jobs = []
    for log in cloud_log_list[1:-1]:
        # Regex to find the job id and the expected job duration.
        match = re.search(r"Cloud Job \|\| job name job-(\S+) \| (\S+)", log)
        #match = match.groups()
        if match:
            match = match.groups()
            # Convert the job id to an int.
            job_id = int(match[0])
            log_jobs.append(job_id)
    return log_jobs


def get_job_submission_log_path(name: str):
    """
    Retrives the path to the job submission log file.
    """
    path = (f"{submit_sweep.LOG_DIRECTORY.format(name=name)}"
            "/debug/job_submission_thread.log")
    return os.path.abspath(path)


def get_event_submission_log_path(name: str, idx: int):
    """
    Retrives the path to the event submission log file.
    """
    path = (f"{submit_sweep.LOG_DIRECTORY.format(name=name)}"
            f"/events/{idx}.log")
    return os.path.abspath(path)


def submit_job_to_scheduler(job_yaml: dict):
    with tempfile.NamedTemporaryFile(mode="w") as f:
        temp_file_path = f.name
        yaml.safe_dump(job_yaml, f)
        logger.debug(
            f"****** Job Sent to submit_job.py at Time {time.time()} ******")
        subprocess.run([
            "python3",
            "-m",
            "starburst.drivers.submit_job",
            "--job-yaml",
            temp_file_path,
        ])


def submission_loop(
    jobs: Dict[Any, Any],
    clusters: Dict[str, str],
    sweep_name: str,
    run_index: int,
    file_logger: LogManager,
):
    """
    Logic for submitting jobs to the scheduler. Only returns when all jobs
    have been submitted and completed running on the cluster.
    """
    total_jobs = len(jobs)
    job_tracker = JobStateTracker(total_jobs)
    onprem_cluster = {
        "name": clusters["onprem"],
    }
    cloud_cluster = {
        "name": clusters["cloud"],
        "spill_to_cloud": jobs[0]["spill_to_cloud"],
        "cloud_cluster_path":
        get_event_submission_log_path(sweep_name, run_index),
    }

    # Primary loop for submitting jobs to the scheduler.
    # Will submit jobs until all jobs have been submitted.
    file_logger.append(f"Submitting {total_jobs} jobs...")
    submission_offset = time.time()
    job_index = 0
    while True:
        # Offset a job's submit time by the Unix epoch time.
        if time.time() > jobs[job_index]["submit_time"] + submission_offset:
            job = jobs[job_index]
            submit_job_to_scheduler(job["kube_yaml"])
            submit_time = time.time()
            job_tracker.update_submit_idx(job_index, submit_time)
            job_tracker.update_submit_file_state(
                job_index,
                f"{submit_sweep.LOG_DIRECTORY.format(name=str(sweep_name))}"
                f"/jobs/{run_index}.yaml",
            )
            file_logger.append(f"Submitting Job {job_index}: {str(job)} "
                               f"during time {submit_time}.")
            job_index += 1
        if job_index >= total_jobs:
            break
        time.sleep(JOB_SUBMISSION_TICK)
    assert (job_tracker.check_if_jobs_submitted()
            ), "Not all jobs were submitted to the scheduler."

    # Once all jobs have been submitted, continually check the status of the
    # jobs until all jobs have completed.
    file_logger.append(f"Waiting for {total_jobs} jobs to complete...")
    while True:
        if job_tracker.check_if_jobs_finished():
            break
        job_tracker.update_finished_jobs(onprem_cluster, cloud_cluster)
        file_logger.append("Finished Jobs State: " +
                           str(job_tracker.finish_state))
        time.sleep(JOB_COMPLETION_TICK)


def job_submission_service(jobs: Dict[Any, Any], clusters: Dict[str, str],
                           sweep_name: str, run_index: int):
    """
    Calls loop that submit jobs to the scheduler. 
    If an error occurs during the submission loop, the error is logged.
    """
    submission_file_logger = LogManager(
        "job_submission_service", get_job_submission_log_path(sweep_name))
    try:
        submission_loop(
            jobs=jobs,
            clusters=clusters,
            sweep_name=sweep_name,
            run_index=run_index,
            file_logger=submission_file_logger,
        )
    except Exception:
        # If an error occrus during job submission loop, log the error
        # and move onto the next run in the sweep.
        submission_file_logger.append(traceback.format_exc() + "\n")
        pass
    submission_file_logger.close()