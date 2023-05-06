import matplotlib.pyplot as plt
import math 
import heapq 

class Job(object):
    def __init__(self, idx: int, arrival: float, runtime: float,
                 deadline: float, resources: dict, cost: float):
        self.idx = idx
        self.arrival = arrival
        self.runtime = runtime
        self.deadline = deadline
        self.resources = resources
        self.num_gpus = resources['GPUs']
        self.cost = cost

        # State of the Job
        self.state = None
        # Starting time of the job on the local cluster, if none, the job was ran on the cloud.
        self.start = None

        # Keeps track of which GPU(s) the job ran on.
        self.allocated_gpus = {}

        # For backfill scheduling
        self.block_job_idx = None

        # # This for preemption, to prevent chain pre-emptions
        # self.opp_cost = 0

    def __eq__(self, other):
        return self.idx == other.idx

    def __hash__(self):
        return hash(str(self.idx))

    def __repr__(self):
        return f'Job(idx={self.idx}, resources={self.resources}, arr={self.arrival}, run = {self.runtime}, deadline={self.deadline}, start={self.start})\n'

GPUS_PER_NODE = 128 #32 #16 #12#10#9 #32#16#8#128#1

def cpu_index_mapping(jobs):
    #TODO: Implemement greedy algorithm to plot cpu indices
    '''
    Add all jobs to queue, then greedily assign indicies 

    Have priority queue for each node with "Free indices" sorted by index number 

    Iterate over all start times 

    TODO: Verify allocated_notes
    TODO: Determine how parsing changes between http_info and default values 
    '''
    #allocated_nodes = jobs['allocated_gpus']#jobs['scheduled_nodes'].values()
    
    allocated_nodes = jobs['node_index']
    cpus = jobs['cpus']
    nodes = set(allocated_nodes)
    #for node_indices in allocated_nodes: 
    #    for index in node_indices: 
    #        nodes.add(index)
    #print("TOTAL NODES: ")
    #print(nodes)

    #print("")
    node_jobs ={}
    node_queues = {}
    for node in nodes:
        node_queues[node] = [i + 1 for i in range(GPUS_PER_NODE)]#8)]#128)]#8)] #heapq.heapify([i + 1 for i in range(8)]) #12-cpus -- 100 -- 256
        node_jobs[node] = []
        print(node_queues)
    print("ALL NODE QUEUES")
    print(node_queues)
    print("ALL JOBS")
    print(jobs)

    # TODO: Create a list of times that include all arrival times and completion times in the same list in numerical order 
    global_queue = []#heapq.heapify([])
    job_id_to_index = {}

    for i in range(len(jobs['arrival'])):
        # Remove values from queue
        job_id = jobs['idx'][i]
        job_id_to_index[job_id] = i
        job_node = jobs['node_index'][i]
        job_cpu_size = jobs['cpus'][i]
        job_arrival = jobs['arrival'][i]
        job_runtime = jobs['runtime'][i]
       
        print("JOB NODE")
        print(job_node)

        while global_queue and global_queue[0][0] <= job_arrival: 
            end_time, end_job_id = heapq.heappop(global_queue)
            released_index = job_id_to_index[end_job_id]
            #released_cpus = jobs['allocated_gpus'][released_index].keys()[0] #job_id_to_index[end_job_id]]#end_job_id]
            for released_node in jobs['allocated_gpus'][released_index]: 
                released_cpus = jobs['allocated_gpus'][released_index][released_node]
                #released_node = jobs['node_index'][released_index]
                released_node_queue = node_queues[released_node]
                node_jobs[released_node].remove(end_job_id)
                for cpu in released_cpus: 
                    heapq.heappush(released_node_queue, cpu)

        heapq.heappush(global_queue, (job_arrival + job_runtime, job_id))
        #print("GLOBAL QUEUE") # Queue sorted on end time -- earliest to latest end time
        #print(global_queue)
        #print("CPU_SIZE")
        #print(job_cpu_size)
        #print("NODE_QUEUE")
        #print(node_queue)

        job_allocated_cpus = []
        node_queue = node_queues[job_node]
        node_jobs[job_node].append(job_id)

        print("CPU_SIZE")
        print(job_cpu_size)
        print("NODE_QUEUE")
        print(node_queue)
        for j in range(job_cpu_size): 
            # TODO: Determine how to handle if jobs run more than total feasible cpus -- in a more robust manner than previously defined 
            #if node_queue: 
            #print("Job Queue")
            #print(node_queues)
            #print("Node Jobs")
            #print(node_jobs)
            #print("Current Node")
            #print(job_node)
            cpu_index = heapq.heappop(node_queue)
            job_allocated_cpus.append(cpu_index)
            
        jobs['allocated_gpus'][i] = {job_node: job_allocated_cpus}

    return jobs

def plot_trace_spacetime_and_spillover(jobs, num_nodes, save=False, path=None, subplt=None, plt_index=None, tag=None, scale=1, plot_sweep=False, dim=(-100, 100, 0, 100)):
    # TODO: Modify function to plot CPU jobs --> number of jobs concurrently running may exceed cpu count
    '''
    Create "threads index" that track CPU jobs running together
    '''
    #print("NUM NODES")
    #print(num_nodes)
    jobs = cpu_index_mapping(jobs)
    #print("DISPLAYED JOBS")
    #print(jobs)
    jobs = jobs.copy()
    #TODO: Plot color based on job start time and not job index
    #NUM_COLORS = max(jobs['arrival']) + 1
    NUM_COLORS = len(jobs['idx']) + 5#1
    #print(NUM_COLORS)
    cm = plt.get_cmap('gist_rainbow')
    colors = [cm(1. * i / NUM_COLORS) for i in range(NUM_COLORS)]
    
    '''
    if not plot_sweep:
        fig, subplt = plt.subplots(figsize=(100 * scale, 50 * scale))
    '''
    
    total_gpus = num_nodes * GPUS_PER_NODE #GPUs equivalent to CPUs
    segment_height_list = {}
    try: 
        for j_idx in range(len(jobs['idx'])):
            allocated_gpus = jobs['allocated_gpus'][j_idx]
            segment = (jobs['arrival'][j_idx],
                        jobs['arrival'][j_idx] + jobs['runtime'][j_idx], j_idx)
            for node_idx in allocated_gpus.keys():
                for node_gpu_idx in allocated_gpus[node_idx]:
                    #print("NODE_IDX")
                    #print(node_idx)
                    #print("NODE_GPU_IDX")
                    #print(node_gpu_idx)
                    gpu_idx = total_gpus - (GPUS_PER_NODE * node_idx +
                                            node_gpu_idx)
                    #                 print(job.idx)
                    #                 print(len(colors))
                    #if plot_sweep: 
                    if subplt is not None:
                        if plt_index is not None: 
                            subplt[plt_index].barh(gpu_idx,
                                width=jobs['runtime'][j_idx],
                                edgecolor='black',
                                height=1.0,
                                left=segment[0],#jobs['start'][j_idx],
                                align='edge',
                                #color=colors[jobs['arrival'][j_idx]],
                                #color=colors[jobs['idx'][j_idx]],
                                color=colors[jobs['idx'][j_idx]] if jobs['idx'][j_idx] < len(colors) else None,
                                alpha = 0.5)
                    '''
                    else:
                        subplt.barh(gpu_idx,
                                    width=jobs['runtime'][j_idx],
                                    edgecolor='black',
                                    height=1.0,
                                    left=segment[0],#jobs['start'][j_idx],
                                    align='edge',
                                    #color=colors[jobs['arrival'][j_idx]],
                                    #color=colors[jobs['idx'][j_idx]],
                                    color=colors[jobs['idx'][j_idx]] if jobs['idx'][j_idx] < len(colors) else None,
                                    alpha = 0.5)
                    '''

                    '''
                    else: 
                        ax.barh(gpu_idx,
                                width=jobs['runtime'][j_idx],
                                edgecolor='black',
                                height=1.0,
                                left=segment[0],#jobs['start'][j_idx],
                                align='edge',
                                #color=colors[jobs['arrival'][j_idx]],
                                #color=colors[jobs['idx'][j_idx]],
                                color=colors[jobs['idx'][j_idx]] if jobs['idx'][j_idx] < len(colors) else None,
                                alpha = 0.5)
                    '''
            '''
            if not allocated_gpus:
                print("NOT ALLOCATED")
                height = 0
                segment = (jobs['arrival'][j_idx],
                        jobs['arrival'][j_idx] + jobs['runtime'][j_idx], j_idx)
                for k, v in segment_height_list.items():
                    if segment[0] > k[0] and segment[0] < k[1]:
                        height += v
                segment_height_list[segment] = jobs['num_gpus'][j_idx]
                if subplt is not None:
                    if plt_index is not None: 
                        subplt[plt_index].barh(total_gpus + height,
                        width=segment[1] - segment[0],
                        edgecolor='black',
                        height=jobs['num_gpus'][j_idx],
                        left=segment[0],
                        align='edge',
                        color=colors[jobs['idx'][j_idx]],
                        alpha = 0.5)
                else: 
                    ax.barh(total_gpus + height,
                            width=segment[1] - segment[0],
                            edgecolor='black',
                            height=jobs['num_gpus'][j_idx],
                            left=segment[0],
                            align='edge',
                            color=colors[jobs['idx'][j_idx]],
                            alpha = 0.5)
            else:
                segment = (jobs['arrival'][j_idx],
                        jobs['arrival'][j_idx] + jobs['runtime'][j_idx], j_idx)
                for node_idx in allocated_gpus.keys():
                    for node_gpu_idx in allocated_gpus[node_idx]:
                        gpu_idx = total_gpus - (GPUS_PER_NODE * node_idx +
                                                node_gpu_idx)
                        #                 print(job.idx)
                        #                 print(len(colors))
                        if subplt is not None:
                            if plt_index is not None: 
                                subplt[plt_index].barh(gpu_idx,
                                    width=jobs['runtime'][j_idx],
                                    edgecolor='black',
                                    height=1.0,
                                    left=segment[0],#jobs['start'][j_idx],
                                    align='edge',
                                    color=colors[jobs['idx'][j_idx]],
                                    alpha = 0.5)
                        else: 
                            ax.barh(gpu_idx,
                                    width=jobs['runtime'][j_idx],
                                    edgecolor='black',
                                    height=1.0,
                                    left=segment[0],#jobs['start'][j_idx],
                                    align='edge',
                                    color=colors[jobs['idx'][j_idx]],
                                    alpha = 0.5)
            '''
    except Exception as e: 
        '''
        allocated_gpus = jobs['allocated_gpus'][j_idx]
        print(allocated_gpus)
        segment = (jobs['arrival'][j_idx],
                    jobs['arrival'][j_idx] + jobs['runtime'][j_idx], j_idx)
        for node_idx in allocated_gpus.keys():
            for node_gpu_idx in allocated_gpus[node_idx]:
                #print("NODE_IDX")
                #print(node_idx)
                #print("NODE_GPU_IDX")
                #print(node_gpu_idx)
        '''
        print(e)
        #return e
    for i in range(total_gpus + 1):
        multiplier = math.ceil(num_nodes / 32)
        if (i + 1) % GPUS_PER_NODE == 1:
            #if plot_sweep: 
            subplt[plt_index].axhline(y=i + 1, linewidth=0.75 / multiplier, color='black')
            #else: 
            #    subplt.axhline(y=i + 1, linewidth=0.75 / multiplier, color='black')
            #plt.axhline(y=i + 1, linewidth=8 / multiplier, color='brown')
        else:
            pass

    max_arrival = max(jobs['arrival'])
    completions = [jobs['arrival'][i] + jobs['runtime'][i] for i in range(len(jobs['arrival']))]
    max_completion = max(completions)

    x_lim_max = max_completion


    if subplt is not None:
        if plt_index is not None: 
            #dim = (-30, 60, 0, 650)
            bottom, top, left, right = dim
            subplt[plt_index].set_ylim(bottom=bottom, top=top)  #, #top=total_gpus + 1) #(-4, 10) (-16, 10)
            #subplt[plt_index].set_xlim(left=-50, right=800)#2* max_arrival)
            subplt[plt_index].set_xlim(left=left, right=right)#x_lim_max) 
            #subplt[plt_index].axvline(x=max_arrival, color='black', linewidth=5)
            subplt[plt_index].axvline(x=max_completion, color='brown', linewidth=0.75)
            #subplt[plt_index].set_axvline(x=max_arrival, color='black', linewidth=5)
            #plt.tight_layout()
            subplt[plt_index].set_xlabel('Time')
            subplt[plt_index].set_ylabel('Nodes ' + str(tag) +  )
            return subplt
    
    if save:
        if path: 
            plt.savefig(path)
            plt.close()
    else:
        print("Plotted") 
        plt.show()
        #if not subplt: 
            #plt.show()
    #return subplt
    '''
    else: 
        plt.ylim(bottom=-4, top=10)  #, #top=total_gpus + 1)
        plt.xlim(left=-50, right=800)#2* max_arrival)
        #plt.axvline(x=max_arrival, color='black', linewidth=5)
        #plt.tight_layout()
        plt.xlabel('Time')
        plt.ylabel('Nodes')
    '''
    
    
import copy
import csv
import cvxpy
import datetime
import json
import math
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.pyplot as plt
import multiprocessing
from multiprocessing import Pool
import numpy as np
import os
import pandas as pd
import pickle
import random
import seaborn as sns
from typing import List, Dict
import sys
import warnings
warnings.filterwarnings("ignore", category=FutureWarning) 
sys.path.append('../')


def set_plotting_setting(ax):
    plt.rcParams.update({'font.size': 15})
    ax.grid(True, which='both')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(True)
    ax.spines['bottom'].set_visible(True)
    ax.tick_params(bottom=False, left=False)
    ax.set_axisbelow(True)
    ax.set_xlim(right=2.25)

label_dict = {
    'avg_jct': 'Avg. JCT (hr)',
    'cost_mult': '% Cost Savings\nover No Wait',
    'cost_diff': 'Cost Savings\nover No Wait',
    'cluster_size': 'Cluster Size (# Nodes)',
    'norm_system_utilization': 'System Utilization',
    'system_utilization': 'System Utilization',
    'cluster_utilization': 'Cluster Utilization',
    'total_cloud_cost': 'Cloud Cost',
    'arrival_rate': 'Arrival Rate',
}

def simulator_plotting_fn(df, 
                          x_axis: str,
                          y_axis: list = ['cost_mult', 'avg_jct'],
                          df_filter: dict = {},
                          baseline_filter: dict={'waiting_policy': 'zero',},
                          groupby_values=['waiting_policy', 'waiting_factor'],
                          normalize_x_axis=False):
    if isinstance(y_axis, str):
        y_axis = [y_axis]
    fig, axs = plt.subplots(nrows=1, ncols=len(y_axis), figsize=(5*len(y_axis), 3.5))
    
    for k,v in df_filter.items():
        df = df[df[k]==v]
       
    baseline_df = df
    for k,v in baseline_filter.items():
        assert isinstance(v, str)
        baseline_df = baseline_df[baseline_df[k]==v]
        #df = df[df[k]!=v]
    diff_df = pd.merge(df, baseline_df, left_on=x_axis,right_on=x_axis)
    
    if normalize_x_axis:
        if x_axis == 'cluster_size':
            # Hardcoded in Philly trace, precomputed ahead of time
            total_job_volume = 1155998.77277777
            job_makespan = 2559.3205555555555
            diff_df['norm_system_utilization'] = total_job_volume/(job_makespan*diff_df['cluster_size']*sim_df['gpus_per_node'].iloc[0])
            x_axis = 'norm_system_utilization'
        elif x_axis == 'arrival_rate':
            avg_job_volume_rate = diff_df['arrival_rate'] * np.mean(df['num_gpus'].iloc[0]* df['runtime'].iloc[0])
            diff_df['norm_system_utilization'] = avg_job_volume_rate/(df['cluster_size'].iloc[0]*df['gpus_per_node'].iloc[0])
            x_axis = 'norm_system_utilization'
    
    def cost_multiplier(row):
        baseline_cost = row['total_cloud_cost_y']
        cost = row['total_cloud_cost_x']
        if baseline_cost == 0 and cost==0:
            return 0
        elif baseline_cost <=10000:
            # Small cloud cost for No wait
            # Savings over small cloud cost is negligible for organizations.
            return 0
        elif baseline_cost == 0 and cost>0:
            return 100
        return 100* (1 - (cost/baseline_cost))

    def cost_difference(row):
        baseline_cost = row['total_cloud_cost_y']
        cost = row['total_cloud_cost_x']
        return baseline_cost - cost
    
    diff_df['cost_mult'] = diff_df.apply(cost_multiplier, axis=1)
    diff_df['cost_diff'] = diff_df.apply(cost_difference, axis=1)
    groupby_values = [f'{g}_x' for g in groupby_values]
    mod_y_axis = [f'{y}_x' if y!='cost_mult' and y!='cost_diff' else y for y in y_axis]
    
    import itertools
    markers = itertools.cycle(('v', '^','.', 'o', '*',',', '+',)) 
    for idx, (label, grp) in enumerate(diff_df.groupby(groupby_values)):
        marker = next(markers)
        for ax_idx, ax in enumerate(axs):           
            grp.plot(x = x_axis, y = mod_y_axis[ax_idx],ylabel=label_dict[y_axis[ax_idx]], \
                     xlabel=label_dict[x_axis], marker=marker, ax = ax, label = label, legend=None)
    
    for ax in axs:
        set_plotting_setting(ax)
    #axs[1].set_xlim(right=36, left=20)
    lines, labels = ax.get_legend_handles_labels()
    fig.legend(lines, labels, ncol=len(labels), \
               bbox_to_anchor=(0, 0.92, 1, 0.2),loc='upper center')
    plt.tight_layout()
    plt.show()  

'''
simulator_plotting_fn(sim_df, x_axis='cluster_size', y_axis=['cost_mult','cost_diff','avg_jct','cluster_utilization'], normalize_x_axis=True)

arrival_df = utils.load_logs_as_dataframe('/home/gcpuser/sim_logs/gen_gpu/vary_waiting_5.log')

simulator_plotting_fn(arrival_df, x_axis='arrival_rate', y_axis=['avg_jct','cost_mult', 'cost_diff', 'cluster_utilization'], \
                      groupby_values=['waiting_policy', 'waiting_factor'], normalize_x_axis=True)
'''