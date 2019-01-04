from core.configuration import Kconfig
from utils import common, time_op
from utils.singleton import singleton
from core.event.base_event import base_event
import os

try:
	import cPickle as pickle
except ImportError:
	import pickle

class Kpickle():
	def __init__(self, path):
		db_location = os.path.join(common.get_data_location(), Kconfig().db_dir)

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
class Kdatabase(base_event):
	def __init__(self):
		pass

	def on_initializing(self, *args, **kwargs):
		self.reset_monitor_second()

		self.db_objs = {}
		self.db_maps = {
			"audit": Kpickle(Kconfig().db_audit),
			"baseline": Kpickle(Kconfig().db_baseline),
			"basic" : Kpickle(Kconfig().db_basic),
			"cleaner" : Kpickle(Kconfig().db_cleaner),
			"fingerprint" : Kpickle(Kconfig().db_fingerprint),
			"monitor" : Kpickle(Kconfig().db_monitor),
			"ueba" : Kpickle(Kconfig().db_ueba),
			"virus": Kpickle(Kconfig().db_virus),
			"virus_whitelist" : Kpickle(Kconfig().db_virus_whitelist),
			"vuls" : Kpickle(Kconfig().db_vuls)
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
			"cleaner" : {
				"kinds" : {},
				"record" : [],
				"lasttime" : 0
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
		#self.recursive_update(self.db_objs, db_objs)
		#self.db_objs = db_objs

		return True

	def manual_struct_update(self):
		"""This function only for updating TypeError struct"""

		# modify at 2018/6/16 14:41 by zhangqian
		if 'statistic' not in self.db_objs["audit"]:
			self.db_objs["audit"]["statistic"] = {
				"critical": 0,
				"warning": 0
			}
			self.dump("audit")

		if not self.db_objs["basic"]["uuid"]:
			self.db_objs["basic"]["uuid"] = common.create_uuid()
			self.dump("basic")

		if not "warnings" in self.db_objs["monitor"]:
			self.db_objs["monitor"]["warnings"] = {
				"cpu": [],
				"memory": [],
				"net_io": [],
				"disk_io": []
			}
			self.dump("monitor")

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
