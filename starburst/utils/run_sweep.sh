export PYTHONPATH=/home/suryaven/test/starburst

cd /home/suryaven/test/starburst/starburst/utils

directory="../logs/logs/"

if [ ! -d "$directory" ]; then
  mkdir -p "$directory"
  echo "Log directory '$directory' created."
fi

python3 clean_processes.py

nohup python3 sampled_jobs.py > ../logs/logs/output_$1.log 2>&1 &