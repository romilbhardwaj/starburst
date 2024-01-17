export PYTHONPATH=/home/gcpuser/starburst/

cd /home/gcpuser/starburst/starburst/utils

current_time=$(date +%s)

#directory="../logs/logs/"
#directory="../logs/archive/"
directory=$(printf "../logs/archive/%d" $current_time)

if [ ! -d "$directory" ]; then
  mkdir -p "$directory"
  echo "Log directory '$directory' created."
fi

python3 clean_processes.py
python3 clean_processes.py
python3 clean_processes.py

#python3 submit_jobs.py run $1 $current_time 
nohup python3 submit_jobs.py run $1 $current_time > ../logs/archive/$current_time/starburst.log 2>&1 &