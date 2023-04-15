import matplotlib.pyplot as plt
import math 

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

GPUS_PER_NODE = 1

def plot_trace_spacetime_and_spillover(jobs, num_nodes):
    jobs = jobs.copy()
    NUM_COLORS = len(jobs['idx'])
    cm = plt.get_cmap('gist_rainbow')
    colors = [cm(1. * i / NUM_COLORS) for i in range(NUM_COLORS)]
    fig, ax = plt.subplots(figsize=(100, 50))
    total_gpus = num_nodes * GPUS_PER_NODE
    segment_height_list = {}
    for j_idx in range(len(jobs['idx'])):
        allocated_gpus = jobs['allocated_gpus'][j_idx]
        if not allocated_gpus:
            height = 0
            segment = (jobs['arrival'][j_idx],
                       jobs['arrival'][j_idx] + jobs['runtime'][j_idx], j_idx)
            for k, v in segment_height_list.items():
                if segment[0] > k[0] and segment[0] < k[1]:
                    height += v
            segment_height_list[segment] = jobs['num_gpus'][j_idx]
            ax.barh(total_gpus + height,
                    width=segment[1] - segment[0],
                    edgecolor='black',
                    height=jobs['num_gpus'][j_idx],
                    left=segment[0],
                    align='edge',
                    color=colors[jobs['idx'][j_idx]])
        else:
            for node_idx in allocated_gpus.keys():
                for node_gpu_idx in allocated_gpus[node_idx]:
                    gpu_idx = total_gpus - (GPUS_PER_NODE * node_idx +
                                            node_gpu_idx)
                    #                 print(job.idx)
                    #                 print(len(colors))
                    ax.barh(gpu_idx,
                            width=jobs['runtime'][j_idx],
                            edgecolor='black',
                            height=1.0,
                            left=jobs['start'][j_idx],
                            align='edge',
                            color=colors[jobs['idx'][j_idx]])
    for i in range(total_gpus + 1):
        multiplier = math.ceil(num_nodes / 32)
        if (i + 1) % GPUS_PER_NODE == 1:
            plt.axhline(y=i + 1, linewidth=8 / multiplier, color='brown')
        else:
            pass
    max_arrival = max(jobs['arrival'])
    plt.ylim(bottom=1)  #, #top=total_gpus + 1)
    plt.xlim(right=1.1 * max_arrival)
    plt.axvline(x=max_arrival, color='black', linewidth=5)
    plt.tight_layout()
    plt.show()