from utils import common
from utils.singleton import singleton
from config import constant
import os

try:
	import cPickle as pickle
except ImportError:
	import pickle

class Kpickle():
	def __init__(self, path):
		db_location = os.path.join(common.get_data_location(), constant.DB_DIR)

		if not os.path.exists(db_location):
			os.mkdir(db_location)

		self.path = os.path.join(db_location, path)

	def dump(self, obj):
		with open(self.path, 'wb') as f:
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def load(self):
		with open(self.path, 'rb') as f:
			return pickle.load(f)

@singleton
class Kdatabase():
	def __init__(self):
		pass
		
	def on_initializing(self, *args, **kwargs):
		self.reset_monitor_second()
		
		self.db_objs = {}
		self.db_maps = {
			"audit": Kpickle(constant.DB_AUDIT),
			"baseline": Kpickle(constant.DB_BASELINE),
			"basic" : Kpickle(constant.DB_BASIC),
			"fingerprint" : Kpickle(constant.DB_FINGERPRINT),
			"monitor" : Kpickle(constant.DB_MONITOR),
			"setting": Kpickle(constant.DB_SETTING),
			"ueba" : Kpickle(constant.DB_UEBA),
			"virus": Kpickle(constant.DB_VIRUS),
			"virus_whitelist" : Kpickle(constant.DB_VIRUS_WHITELIST),
			"vuls" : Kpickle(constant.DB_VULS)
		}
		
		db_objs = {
			"audit" : {
				"feature": [],
				"authentication": [],
				"kernel": [],
				"statistic": {
					"critical": 0,
					"warning": 0
				},
				"lasttime" : 0
			},
			"baseline" : {
				"risks": {},
				"lasttime" : 0
			},
			"basic" : {
				"startup_counts" : 0,
				"uuid" : None,
				"version" : ""
			},
			"fingerprint" : {
				"port": {
					"current": [],
					"change": {},
					"lasttime": 0
				},
				"account": {
					"current": [],
					"change": {},
					"lasttime": 0
				}
			},
			"monitor" : {
				"cpu" : [],
				"memory" : [],
				"net_io" : {
					"tx" : [],
					"rx" : []
				},
				"disk_io" : {
					"read" : [],
					"write" : []
				},
				"procs" : [],
				"times" : [],
				"minutes" : 0,
				"warnings" : {
					"cpu" : [],
					"memory" : [],
					"net_io" : [],
					"disk_io" : []
				}
			},
			"setting" : {
				"username": "",
				"credential": ""
			},
			"ueba" : {
				"storys" : {},
				"lasttime" : 0
			},
			"virus" : {
				"handledList": {},
				"isolateList": {},
				"untrustList": {},
				"allHistory": [],
				'lastScanedPath':'',
				'finished': 0,
				"lasttime" : 0,
				'searchedCount' : 0
			},
			"virus_whitelist" : {},
			"vuls" : {
				"items" : {},
				"repaired_packages" : [],
				"record" : [],
				"lasttime" : 0
			}
		}
		
		for key in self.db_maps.keys():
			try:
				self.db_objs[key] = self.db_maps[key].load()
			except Exception as e:
				self.db_objs[key] = db_objs[key]
				self.dump(key)
				
		#self.startup_update()
		self.manual_struct_update()
		
		if len(args) == 0:
			if not self.get_obj("setting")["username"] or not self.get_obj("setting")["credential"]:
				from core.logger import Klogger
				Klogger().critical("Please use login.py to login Marsnake server first")
				return False

		return True

	def manual_struct_update(self):
		"""This function only for updating TypeError struct"""
		pass

	def recursive_update(self, default, custom):
		"""
		default:
			the old struct needs to be changed
		custom:
			the standard struct to change default.

		when done,custom is the new struct with default's data.
		"""
		if not isinstance(default, dict) or not isinstance(custom, dict):
			raise TypeError('Params of recursive_update should be dicts')

		for key in custom:
			if key in default:
				if type(custom[key]) != type(default[key]):
					raise TypeError('Type error')
				elif isinstance(custom[key], dict) and isinstance(default.get(key), dict):
					self.recursive_update(default[key], custom[key])
				elif isinstance(custom[key], list) and isinstance(default.get(key), list):
					custom[key].extend(default[key])
				else:
					custom[key] = default[key]

	def startup_update(self):
		basic = self.get_obj("basic")
		basic["startup_counts"] += 1

		if basic["startup_counts"] == 1:
			basic["uuid"] = common.create_uuid()

			self.dump("basic")

	def reset_monitor_second(self):
		self.monitor_second = {
			"cpu" : [],
			"memory" : [],
			"net_io" : {
				"tx" : [],
				"rx" : []
			},
			"disk_io" : {
				"read" : [],
				"write" : []
			},
			"procs" : {}
		}

	def get_monitor_second(self):
		return self.monitor_second

	def get_obj(self, key):
		if key in self.db_objs:
			return self.db_objs[key]

	def dump(self, key):
		if key in self.db_objs:
			self.db_maps[key].dump(self.db_objs[key])
