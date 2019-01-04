from utils.singleton import singleton
from utils import common, file_op
from config import constant
from core.event.base_event import base_event
import os, json

@singleton
class Kconfig(base_event):
	def __init__(self):
		pass

	def on_initializing(self, *args, **kwargs):
		self.release = constant.RELEASE
		self.cybertek_server = constant.CYBERTEK_URL

		self.server_publickey = self.read_server_publickey()

		self.log_dir = constant.LOG_DIR
		self.log_name = constant.LOG_NAME
		self.log_max_bytes = constant.LOG_MAX_BYTES
		self.log_backup_count = constant.LOG_BACKUP_COUNT

		self.db_dir = constant.DB_DIR
		self.db_monitor = constant.DB_MONITOR
		self.db_baseline = constant.DB_BASELINE
		self.db_basic = constant.DB_BASIC
		self.db_cleaner = constant.DB_CLEANER
		self.db_fingerprint = constant.DB_FINGERPRINT
		self.db_vuls = constant.DB_VULS
		self.db_ueba = constant.DB_UEBA
		self.db_audit = constant.DB_AUDIT
		self.db_virus = constant.DB_VIRUS
		self.db_virus_whitelist = constant.DB_VIRUS_WHITELIST

		self.cybertak_size_limit = constant.MALWARE_FILE_MAX_SIZE

		if not self.server_publickey:
			print("No server publickey file exists")
			return False

		return True

	def read_server_publickey(self):
		return file_op.cat(os.path.join(common.get_work_dir(), constant.SERVER_PUBLIC_KEY), "r")

	def read_version(self):
		version = ""

		with open(os.path.join(common.get_work_dir(), constant.VERSION_CONF), "r") as f:
			version = f.read().strip('\n')

		return version
