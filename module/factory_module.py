from utils.singleton import singleton
from concurrent.futures import ThreadPoolExecutor
from utils import common, import_helper
from config import constant
import sys, os, imp, traceback

def load_mod(mod_path):
	mod_path = mod_path.replace("/", ".").rsplit(".", 1)[0]
	mod = None

	try:
		mod = import_helper.import_module(mod_path)
	except Exception as e:
		print("{} error:{}".format(mod_path, str(e)))
		traceback.print_exc()
		
	return mod

def run_mod(mod_run, payload, socket):
	try:
		mod_run(payload, socket)
	except Exception as e:
		traceback.print_exc()

@singleton
class Kmodules():
	def __init__(self):
		pass

	def init(self):
		'''
		self.modules = {
			"1000" : load_mod("module/basic/get_info.py"),
			"1001" : load_mod("module/filesystem/open_dir.py"),
			"1002" : load_mod("module/filesystem/download_files.py"),
			"1003" : load_mod("module/filesystem/mkdir.py"),
			"1004" : load_mod("module/filesystem/delete_file_or_folder.py"),
			"1005" : load_mod("module/filesystem/upload.py"),
			"1006" : load_mod("module/filesystem/rename.py"),
			"1007" : load_mod("module/status/network_status.py"),
			"1008" : load_mod("module/basic/overview.py"),
			"10081" : load_mod("module/basic/overview_win.py"),
			"1009" : load_mod("module/basic/system_status.py"),
			"1010" : load_mod("module/status/cpu_status.py"),
			"1011" : load_mod("module/status/ram_status.py"),
			"1012" : load_mod("module/status/disk_status.py"),
			"1013" : load_mod("module/status/user_status.py"),
			"1015" : load_mod("module/hardening/web_scan.py"),
			"1016" : load_mod("module/hardening/vulscan.py"),
			"1017" : load_mod("module/runshell.py"),
			"1018" : load_mod("module/filesystem/list_directory.py"),
			"1019" : load_mod("module/filesystem/paste.py"),
			"1020" : load_mod("module/filesystem/chmod.py"),
			"1021" : load_mod("module/filesystem/sync.py"),
			"1022" : load_mod("module/hardening/boot_services.py"),
			"1023" : load_mod("module/hardening/kernel.py"),
			"1025" : load_mod("module/hardening/authentication.py"),
			"1026" : load_mod("module/hardening/network_audit.py"),
			"1027" : load_mod("module/status/service_status.py"),
			"1028" : load_mod("module/hardening/weakpwd_scan.py"),
			"1029" : load_mod("module/filesystem/execute.py"),
			"1030" : load_mod("module/status/process_detail.py"),
			"1031" : load_mod("module/filesystem/compress.py"),
			"1032" : load_mod("module/filesystem/decompress.py")
		}
		'''
		self.maps = {}
		self.executor = ThreadPoolExecutor(max_workers = 10)

	def unpacker(self, data):
		import cpacker
		cpacker.do_unpack(data, self.maps)

	def create(self, socket, payload):
		cmd_id = payload["cmd_id"]
		
		#You can disable the features you don't prefer to apply at config/constant.py
		#By default, All features are enabled
		if cmd_id in constant.ALLOW_MODULE_ID:
			if constant.ALLOW_MODULE_ID[cmd_id]["enabled"]:
				if not self.maps.has_key(cmd_id):
					print("{} not found".format(cmd_id))
					return
				else:
					self.executor.submit(run_mod, self.maps[cmd_id], payload, socket)
					
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