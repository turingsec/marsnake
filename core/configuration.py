from utils.singleton import singleton
from utils import common, file_op
from config import constant
import os

@singleton
class Kconfig():
	def __init__(self):
		pass
		
	def init(self):
		self.release = constant.RELEASE
		self.server = constant.SERVER_URL
		
		self.server_publickey = self.read_server_publickey()
		self.client_publickey = self.read_client_publickey()
		self.client_privatekey = self.read_client_privatekey()
		self.credential = self.read_credential().strip()
		
		self.log_path = constant.LOG_PATH
		self.log_max_bytes = constant.LOG_MAX_BYTES
		self.log_backup_count = constant.LOG_BACKUP_COUNT
		
		self.db_monitor = constant.DB_MONITOR
		self.db_basic = constant.DB_BASIC
		self.db_cleaner = constant.DB_CLEANER
		self.db_vuls = constant.DB_VULS
		
		if not self.server_publickey:
			print("No server publickey file exists")
			return False
			
		if not self.client_publickey:
			print("No client public key exists")
			return False
			
		if not self.client_privatekey:
			print("No client private key exists")
			return False
			
		if not self.credential:
			print("No credential file exists")
			return False
			
		return True
		
	def read_server_publickey(self):
		return file_op.cat(os.path.join(common.get_work_dir(), constant.SERVER_PUBLIC_KEY), "r")
		
	def read_client_publickey(self):
		return file_op.cat(os.path.join(common.get_work_dir(), constant.RSA_PUBLIC_KEY), "r")
		
	def read_client_privatekey(self):
		return file_op.cat(os.path.join(common.get_work_dir(), constant.RSA_PRIVATE_KEY), "r")
		
	def read_credential(self):
		return file_op.cat(os.path.join(common.get_work_dir(), constant.CREDENTIAL), "r")
