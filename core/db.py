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
			
class Kresource():
	def __init__(self, minute = False):
		self.cpu = []
		self.memory = []
		self.net_io = {
			"tx" : [],
			"rx" : []
		}
		
		self.disk_io = {
			"read" : [],
			"write" : []
		}
		
		if minute:
			self.procs = []
			self.times = []
			self.minutes = 0
		else:
			self.procs = {}
			self.seconds = 0
			
@singleton
class Kdatabase():
	def __init__(self):
		pass
		
	def init(self):
		self.db_objs = {}
		self.db_maps = {
			"basic" : Kpickle(Kconfig().db_basic),
			"monitor" : Kpickle(Kconfig().db_monitor)
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
				"status_second" : Kresource(),
				"status_minute" : Kresource(True)
			}

	def get_obj(self, key):
		if self.db_objs.has_key(key):
			return self.db_objs[key]
			
	def dump(self, key):
		if self.db_objs.has_key(key):
			self.db_maps[key].dump(self.db_objs[key])