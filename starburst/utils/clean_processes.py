import psutil

# get a list of all processes
processes = psutil.process_iter()

# loop through all processes
for process in processes:
    try:
        # get process name and command line arguments
        name = process.name()
        cmdline = process.cmdline()

        # check if this is a Python process and if it matches the script name
        if name == 'python3' and 'sampled_jobs.py' in cmdline:
            # terminate the process
            process.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass