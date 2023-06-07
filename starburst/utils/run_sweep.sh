export PYTHONPATH=$HOME/starburst/

cd $HOME/starburst/starburst/utils

current_time=$(date +%s)

directory=$(printf "../sweep_logs/archive/%d" $current_time)

if [ ! -d "$directory" ]; then
  mkdir -p "$directory"
  echo "Log directory '$directory' created."
fi

python3 clean_processes.py
sleep 3

nohup python3 submit_jobs.py run $1 $current_time > ../sweep_logs/archive/$current_time/starburst.log 2>&1 &