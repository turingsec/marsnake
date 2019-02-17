from utils.singleton import singleton
from utils import common
from utils.randomize import Krandom
from config import constant
import os, json

@singleton
class KProfile():
	def __init__(self):
		self.strategy_detail = None

		if not self.read_info():
			self.create_info()

		self.manual_struct_update()

	def create_info(self):
		self.info = {
			"username": "",
			"fullname": "",
			"password": "",
			"server": {
				"host": constant.SERVER_HOST,
				"port": constant.SERVER_PORT
			},
			"settings": {
				"remote_support": {
					"allow_terminal": True,
					"allow_vnc": True,
					"code": Krandom().digits(6)
				}
			}
		}

		self.write_info()

	def set_web_strategy(self, detail):
		if detail:
			self.strategy_detail = detail

	def get_web_strategy(self):
		return self.strategy_detail

	def manual_struct_update(self):
		pass

	def read_key(self, key):
		if key in self.info:
			return self.info[key]

		return None

	def read_info(self):
		info_path = os.path.join(common.get_data_location(), constant.SETTINGS_INFO)

		try:
			with open(info_path, "r") as f:
				self.info = json.load(f)
				return True

		except Exception as e:
			print("read_info error:", e)
			pass

		return False

	def write_info(self):
		info_path = os.path.join(common.get_data_location(), constant.SETTINGS_INFO)

		try:
			with open(info_path, "w") as f:
				f.write(json.dumps(self.info))

		except Exception as e:
			print("write_info error:", e)
			print(self.info)
			pass
		
	def write_username_fullname(self, username, fullname):
		self.info["username"] = username
		self.info["fullname"] = fullname
		
		self.write_info()

	def write_password(self, password):
		self.info["password"] = password
		
		self.write_info()

	def write_server_conn(self, host, port):
		self.info["server"] = {
			"host": host,
			"port": port
		}

		self.write_info()

	def write_settings(self, vuls_int, cleaner_int, virus_int, allow_terminal, allow_vnc, code):
		self.info["settings"] = {
			"remote_support": {
				"allow_terminal": allow_terminal,
				"allow_vnc": allow_vnc,
				"code": code
			}
		}

		self.write_info()
