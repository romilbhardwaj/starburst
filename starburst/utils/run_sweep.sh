export PYTHONPATH=/home/suryaven/test/starburst

cd /home/suryaven/test/starburst/starburst/utils

directory="../logs/logs/"

if [ ! -d "$directory" ]; then
  mkdir -p "$directory"
  echo "Log directory '$directory' created."
fi

python3 clean_processes.py
python3 clean_processes.py
python3 clean_processes.py

nohup python3 submit_jobs.py run $1 > ../logs/logs/output_$2.log 2>&1 &