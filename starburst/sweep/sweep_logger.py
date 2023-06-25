import logging
import os
import time

LOG_DIRECTORY = '../sweep_logs/{name}/'

def create_log_directory(sweep_name: str=None) -> str:
	"""
	Creates a log directory for the entire sweep.

	Args:
		name (str): Name of the log directory for the current sweep.
	"""
	if not sweep_name:
		sweep_name  = str(int(time.time()))
	log_directory_path = LOG_DIRECTORY.format(name=sweep_name)
	base_log_path = os.path.abspath(log_directory_path)
	os.makedirs(base_log_path, exist_ok=True)
	# Generate sub log directories.
	sub_logs = ['jobs/', 'debug/', 'events/']
	for s_log in sub_logs:
		temp_path =f'{base_log_path}/{s_log}'
		os.makedirs(temp_path, exist_ok=True)
	return sweep_name

class LogFileManager(object):
	"""
	LogFileManager is a class that manages logging to a log file.
	"""
	def __init__(self, log_name: str, log_file_path: str):
		self.logger = logging.getLogger(log_name)
		self.logger.setLevel(logging.DEBUG)
		# Remove the default stdout handler from the logger
		self.logger.handlers = []
		self.file_handler = logging.FileHandler(log_file_path)
		self.file_handler.setLevel(logging.DEBUG)
		self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
		self.file_handler.setFormatter(self.formatter)
		self.logger.addHandler(self.file_handler)
		# Prevent the logger from propagating to the root logger.
		self.logger.propagate = False

	def append(self, message):
		self.logger.debug(message)

	def close(self):
		for handler in self.logger.handlers:
			handler.close()
			self.logger.removeHandler(handler)