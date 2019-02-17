import os, logging, getpass, platform, json, locale, sys, traceback
from logging.handlers import RotatingFileHandler
from utils.singleton import singleton
from core.threads import Kthreads
from core.security import Ksecurity
from core.information import KInformation
from config import constant
from utils import common, net_op, time_op

@singleton
class Klogger():
	def __init__(self):
		self.logger = None

	def on_initializing(self, *args, **kwargs):
		log_location = os.path.join(common.get_data_location(), constant.LOG_DIR)

		if not os.path.exists(log_location):
			os.mkdir(log_location)

		self.path = os.path.join(log_location, constant.LOG_NAME)

		# create logger
		logger_name = "loginfo"

		self.logger = logging.getLogger(logger_name)
		self.logger.setLevel(logging.DEBUG)

		# create file handler
		rfh = RotatingFileHandler(self.path, maxBytes = constant.LOG_MAX_BYTES, backupCount = constant.LOG_BACKUP_COUNT)
		rfh.setLevel(logging.DEBUG)

		# create formatter
		fmt = "%(asctime)s [%(process)d/%(processName)s/%(thread)d/%(threadName)s] [%(levelname)s] %(message)s"
		formatter = logging.Formatter(fmt)

		# add handler and formatter to logger
		rfh.setFormatter(formatter)
		self.logger.addHandler(rfh)

		return True

	def run_mod(self, log):
		language_code, encoding = locale.getdefaultlocale()
		now = time_op.now()
		info = KInformation().get_info()

		info["time"] = time_op.timestamp2string(now)
		info["ts"] = now
		info["language_code"] = language_code
		info["encoding"] = encoding
		info["python_version"] = platform.python_version()
		info["data"] = log
		
		encrypt = Ksecurity().rsa_long_encrypt(json.dumps(info))
		net_op.create_http_request("{}:{}".format(constant.SERVER_HOST, constant.SERVER_PORT), 
					"POST", 
					"/upload_logs", 
					encrypt)

	def exception(self):
		exc_info = sys.exc_info()
		log = traceback.format_exception(*exc_info)
		del exc_info

		self.upload_error(log)

	def upload_error(self, log):
		if constant.RELEASE:
			Kthreads().apply_async(self.run_mod, (log, ))

		print(log)

		self.logger.error(log)

	def info(self, msg):
		print(msg)
		self.logger.info(str(msg).encode('utf8'))

	def warn(self, msg):
		print(msg)
		self.logger.warn(str(msg).encode('utf8'))

	def error(self, msg):
		self.upload_error(msg)

	def critical(self, msg):
		print(msg)
		self.logger.critical(str(msg).encode('utf8'))

	'''
	def __getattr__(self, attr):
		#NOT SUPPORT
			#if attr in dir(self.logger):
				#return self.logger[attr]

		obj = {
			"debug" : self.logger.debug,
			"info" : self.logger.info,
			"warn" : self.logger.warn,
			"error" : self.upload_error,
			"critical" : self.logger.critical
		}

		if attr in obj:
			return obj[attr]
	'''
