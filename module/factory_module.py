from utils.singleton import singleton
from concurrent.futures import ThreadPoolExecutor
from utils import common, import_helper
from config import constant
from core.logger import Klogger
import sys, os, imp, traceback

def load_mod(mod_path):
	mod_path = mod_path.replace("/", ".").rsplit(".", 1)[0]
	mod = None
	
	try:
		mod = import_helper.import_module(mod_path)
	except Exception as e:
		Klogger().error(str(e))
		traceback.print_exc()
		
	return mod
	
def run_mod(mod_run, payload, socket):
	try:
		mod_run(payload, socket)
	except Exception as e:
		Klogger().error(str(e))
		traceback.print_exc()
		
@singleton
class Kmodules():
	def __init__(self):
		pass
		
	def init(self):
		self.modules = {}
		self.executor = ThreadPoolExecutor(max_workers = 10)
		
	def unpacker(self, data):
		import cpacker
		cpacker.do_unpack(data, self.modules)
		
		if self.modules:
			Klogger().info("unpack success {} modules".format(len(self.modules)))
		else:
			Klogger().error("unpack failed {} modules".format(len(self.modules)))
			
		self.executor.submit(run_mod, self.modules["1014"], None, None)
		
	def create(self, socket, payload):
		cmd_id = payload["cmd_id"]
		
		#You can disable the features you don't prefer to apply at config/constant.py
		#By default, All features are enabled
		if cmd_id in constant.ALLOW_MODULE_ID:
			if constant.ALLOW_MODULE_ID[cmd_id]["enabled"]:
				if not self.modules.has_key(cmd_id):
					Klogger().error("module {} not found".format(cmd_id))
					return
				else:
					self.executor.submit(run_mod, self.modules[cmd_id], payload, socket)
					
	def load_compiled(self, name, filename, code, ispackage = False):
		#if data[:4] != imp.get_magic():
		#	raise ImportError('Bad magic number in %s' % filename)
		# Ignore timestamp in data[4:8]
		#code = marshal.loads(data[8:])
		imp.acquire_lock() # Required in threaded applications
		
		try:
			mod = imp.new_module(name)
			sys.modules[name] = mod 	# To handle circular and submodule imports 
										# it should come before exec.
			try:
				mod.__file__ = filename # Is not so important.
				# For package you have to set mod.__path__ here. 
				# Here I handle simple cases only.
				if ispackage:
					mod.__path__ = [name.replace('.', '/')]
				exec(code in mod.__dict__)
			except:
				del sys.modules[name]
				raise
		finally:
			imp.release_lock()
			
		return mod