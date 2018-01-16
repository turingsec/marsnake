from utils.configuration import Kconfig
from utils import common
from utils.singleton import singleton
import cPickle, os

class Kpickle():
	def __init__(self, path):
		dirname = os.path.dirname(path)
		
		if not os.path.exists(dirname):
			os.mkdir(dirname)
			
		self.path = os.path.join(common.get_work_dir(), path)
		
	def dump(self, obj):
		with open(self.path, 'wb') as f:
			cPickle.dump(obj, f, cPickle.HIGHEST_PROTOCOL)
			
	def load(self):
		with open(self.path, 'rb') as f:
			return cPickle.load(f)
			
@singleton
class Kdatabase():
	def __init__(self):
		pass
		
	def init(self):
		self.db_objs = {}
		self.db_maps = {
			"basic" : Kpickle(Kconfig().db_basic),
			"monitor" : Kpickle(Kconfig().db_monitor),
			"cleaner" : Kpickle(Kconfig().db_cleaner),
			"vuls" : Kpickle(Kconfig().db_vuls)
		}
		
		try:
			self.db_objs["basic"] = self.db_maps["basic"].load()
		except Exception as e:
			self.db_objs["basic"] = {
				"remark" : ""
			}
			
		try:
			self.db_objs["monitor"] = self.db_maps["monitor"].load()
		except Exception as e:
			self.db_objs["monitor"] = {
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
				"minutes" : 0
			}
			
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
				"procs" : {},
				"seconds" : 0
			}
			
		try:
			self.db_objs["cleaner"] = self.db_maps["cleaner"].load()
		except Exception as e:
			self.db_objs["cleaner"] = {
				"items" : {},
				"kinds" : {},
				"record" : {},
				"lasttime" : 0
			}
			
		try:
			self.db_objs["vuls"] = self.db_maps["vuls"].load()
		except Exception as e:
			self.db_objs["vuls"] = {
				"items" : {},
				"record" : {},
				"lasttime" : 0
			}

	def get_monitor_second(self):
		return self.monitor_second

	def get_obj(self, key):
		if self.db_objs.has_key(key):
			return self.db_objs[key]
			
	def dump(self, key):
		if self.db_objs.has_key(key):
			self.db_maps[key].dump(self.db_objs[key])

	def dump_minute(self):
		self.db_maps["monitor"].dump(self.db_objs["monitor"])