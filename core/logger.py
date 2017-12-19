import os, logging
from logging.handlers import RotatingFileHandler
from utils.singleton import singleton
from utils.configuration import Kconfig

@singleton
class Klogger():
	def __init__(self):
		self.logger = None
		
		dirname = os.path.dirname(Kconfig().log_path)
		
		if not os.path.exists(dirname):
			os.mkdir(dirname)
			
	def init(self):
		# create logger
		logger_name = "loginfo"
		
		self.logger = logging.getLogger(logger_name)
		self.logger.setLevel(logging.DEBUG)
		
		# create file handler
		rfh = RotatingFileHandler(Kconfig().log_path, maxBytes = Kconfig().log_max_bytes, backupCount = Kconfig().log_backup_count)
		rfh.setLevel(logging.DEBUG)
		
		# create formatter
		fmt = "%(asctime)s [%(levelname)s] %(message)s"
		formatter = logging.Formatter(fmt)
		
		# add handler and formatter to logger
		rfh.setFormatter(formatter)
		self.logger.addHandler(rfh)
		
	def __getattr__(self, attr):
		
		'''NOT SUPPORT
		if attr in dir(self.logger):
			return self.logger[attr]
		'''
		obj = {
			"debug" : self.logger.debug,
			"info" : self.logger.info,
			"warn" : self.logger.warn,
			"error" : self.logger.error,
			"critical" : self.logger.critical
		}
		
		if attr in obj:
			return obj[attr]
			
		return None