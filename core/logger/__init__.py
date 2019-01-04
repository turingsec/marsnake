import os, logging, getpass, platform, json, locale, sys, traceback
from logging.handlers import RotatingFileHandler
from utils.singleton import singleton
from core.configuration import Kconfig
from core.profile_reader import KProfile
from core.threads import Kthreads
from core.security import Ksecurity
from core.event.base_event import base_event
from core.information import KInformation
from utils import common, net_op, time_op

@singleton
class Klogger(base_event):
	def __init__(self):
		self.logger = None

	def on_initializing(self, *args, **kwargs):
		log_location = os.path.join(common.get_data_location(), Kconfig().log_dir)

		if not os.path.exists(log_location):
			os.mkdir(log_location)

		self.path = os.path.join(log_location, Kconfig().log_name)

		# create logger
		logger_name = "loginfo"

		self.logger = logging.getLogger(logger_name)
		self.logger.setLevel(logging.DEBUG)

		# create file handler
		rfh = RotatingFileHandler(self.path, maxBytes = Kconfig().log_max_bytes, backupCount = Kconfig().log_backup_count)
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

		server_setting = KProfile().read_key("server")
		marsnake_server = "{}:{}".format(server_setting["host"], server_setting["port"])

		encrypt = Ksecurity().rsa_long_encrypt(json.dumps(info))
		net_op.create_http_request(marsnake_server, "POST", "/upload_logs", encrypt)

	def exception(self):
		exc_info = sys.exc_info()
		log = traceback.format_exception(*exc_info)
		del exc_info

		self.upload_error(log)

	def upload_error(self, log):
		if Kconfig().release:
			Kthreads().apply_async(self.run_mod, (log, ))

		print(log)

		self.logger.error(log)

	def info(self, msg):
		self.logger.info(str(msg).encode('utf8'))

	def warn(self, msg):
		self.logger.warn(str(msg).encode('utf8'))

	def error(self, msg):
		self.upload_error(msg)

	def critical(self, msg):
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
