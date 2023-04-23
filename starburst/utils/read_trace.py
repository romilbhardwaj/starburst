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

GPUS_PER_NODE = 8#32#16#8#128#1

def cpu_index_mapping(jobs):
    #TODO: Implemement greedy algorithm to plot cpu indices
    '''
    Add all jobs to queue, then greedily assign indicies 

    Have priority queue for each node with "Free indices" sorted by index number 

    iterate over all start times 
    '''
    #allocated_nodes = jobs['allocated_gpus']#jobs['scheduled_nodes'].values()
    allocated_nodes = jobs['node_index']
    cpus = jobs['cpus']
    nodes = set(allocated_nodes)
    #for node_indices in allocated_nodes: 
    #    for index in node_indices: 
    #        nodes.add(index)
    print("TOTAL NODES: ")
    print(nodes)

    node_jobs ={}
    node_queues = {}
    for node in nodes:
        node_queues[node] = [i + 1 for i in range(8)]#128)]#8)] #heapq.heapify([i + 1 for i in range(8)]) #12-cpus -- 100 -- 256
        node_jobs[node] = []

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
        print("GLOBAL QUEUE") # Queue sorted on end time -- earliest to latest end time
        print(global_queue)
        
        job_allocated_cpus = []
        node_queue = node_queues[job_node]
        node_jobs[job_node].append(job_id)
        for j in range(job_cpu_size): 
            # TODO: Determine how to handle if jobs run more than total feasible cpus
            #if node_queue: 
            print("Job Queue")
            print(node_queues)
            print("Node Jobs")
            print(node_jobs)
            print("Current Node")
            print(job_node)
            cpu_index = heapq.heappop(node_queue)
            job_allocated_cpus.append(cpu_index)
            
        jobs['allocated_gpus'][i] = {job_node: job_allocated_cpus}

    return jobs

def plot_trace_spacetime_and_spillover(jobs, num_nodes, save=False, path=None, subplt=None, plt_index=None, tag=None):
    # TODO: Modify function to plot CPU jobs --> number of jobs concurrently running may exceed cpu count
    '''
    Create "threads index" that track CPU jobs running together
    '''
    print("NUM NODES")
    print(num_nodes)
    jobs = cpu_index_mapping(jobs)
    print("DISPLAYED JOBS")
    print(jobs)
    jobs = jobs.copy()
    #TODO: Plot color based on job start time and not job index
    #NUM_COLORS = max(jobs['arrival']) + 1
    NUM_COLORS = len(jobs['idx']) + 1
    print(NUM_COLORS)
    cm = plt.get_cmap('gist_rainbow')
    colors = [cm(1. * i / NUM_COLORS) for i in range(NUM_COLORS)]
    fig, ax = plt.subplots(figsize=(100, 50))
    total_gpus = num_nodes * GPUS_PER_NODE #GPUs equivalent to CPUs
    segment_height_list = {}
    for j_idx in range(len(jobs['idx'])):
        allocated_gpus = jobs['allocated_gpus'][j_idx]
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
                            #color=colors[jobs['arrival'][j_idx]],
                            color=colors[jobs['idx'][j_idx]],
                            alpha = 0.5)
                else: 
                    ax.barh(gpu_idx,
                            width=jobs['runtime'][j_idx],
                            edgecolor='black',
                            height=1.0,
                            left=segment[0],#jobs['start'][j_idx],
                            align='edge',
                            #color=colors[jobs['arrival'][j_idx]],
                            color=colors[jobs['idx'][j_idx]],
                            alpha = 0.5)
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
    for i in range(total_gpus + 1):
        multiplier = math.ceil(num_nodes / 32)
        if (i + 1) % GPUS_PER_NODE == 1:
            plt.axhline(y=i + 1, linewidth=8 / multiplier, color='brown')
        else:
            pass

    max_arrival = max(jobs['arrival'])
    if subplt is not None:
        if plt_index is not None: 
            subplt[plt_index].set_ylim(bottom=-128, top=10)  #, #top=total_gpus + 1) #(-4, 10) (-16, 10)
            subplt[plt_index].set_xlim(left=-50, right=800)#2* max_arrival)
            #subplt[plt_index].set_axvline(x=max_arrival, color='black', linewidth=5)
            #plt.tight_layout()
            subplt[plt_index].set_xlabel('Time')
            subplt[plt_index].set_ylabel('Nodes' + str(tag))
            return subplt
    else: 
        plt.ylim(bottom=-4, top=10)  #, #top=total_gpus + 1)
        plt.xlim(left=-50, right=800)#2* max_arrival)
        plt.axvline(x=max_arrival, color='black', linewidth=5)
        #plt.tight_layout()
        plt.xlabel('Time')
        plt.ylabel('Nodes')

    if save:
        if path: 
            plt.savefig(path)
            plt.close()
    else: 
        if not subplt: 
            plt.show()
    