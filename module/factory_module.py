from utils.singleton import singleton
from concurrent.futures import ThreadPoolExecutor
from utils import common, import_helper
from core.logger import Klogger
from core.threads import Kthreads
import sys, imp
import threading

def load_mod(mod_path):
	mod_path = mod_path.replace("/", ".").rsplit(".", 1)[0]
	mod = None

	try:
		mod = import_helper.import_module(mod_path)
	except Exception as e:
		Klogger().exception()

	return mod

def run_mod(mod_run, payload, socket):
	try:
		#Kthreads().set_name("module-{}".format(mod_run.__module__))
		mod_run.run(payload, socket)
	except Exception as e:
		Klogger().exception()

@singleton
class Kmodules():
	def __init__(self):
		pass

	def on_initializing(self, *args, **kwargs):
		self.modules = {
			"0" : load_mod("module/basic/heartbeat.py"),
			#"1" : load_mod("module/basic/remote_verification.py"),
			"2" : load_mod("module/basic/set_security_strategy.py"),
			"999" : load_mod("module/basic/set_language.py"),
			"1000" : load_mod("module/basic/get_info.py"),
			"1009" : load_mod("module/basic/system_status.py"),
			"1014" : load_mod("module/status/resource.py"),
			"1015" : load_mod("module/status/fingerprint.py"),
			"1016" : load_mod("module/hardening/vulscan.py"),
			"1022" : load_mod("module/hardening/boot_services.py"),
			"1033" : load_mod("module/terminal/new_pty.py"),
			"1034" : load_mod("module/terminal/write_pty.py"),
			"1035" : load_mod("module/terminal/resize_pty.py"),
			"1036" : load_mod("module/terminal/kill_pty.py"),
			"1037" : load_mod("module/vnc/init_vnc.py"),
			"1038" : load_mod("module/hardening/enable_service.py"),
			"1039" : load_mod("module/status/usage.py"),
			"1040" : load_mod("module/status/usage_proc.py"),
			"1041" : load_mod("module/status/user_status.py"),
			"1042" : load_mod("module/hardening/check_garbage.py"),
			"1043" : load_mod("module/hardening/clean_garbage.py"),
			#"1044" : load_mod("module/hardening/remove_garbage.py"),
			"1045" : load_mod("module/status/network_status.py"),
			"1046" : load_mod("module/status/cpu_status.py"),
			"1047" : load_mod("module/status/disk_status.py"),
			#"1048" : load_mod("module/hardening/cleaner.py"),
			"1049" : load_mod("module/hardening/security_audit.py"),
			"1050" : load_mod("module/hardening/check_vuls.py"),
			"1051" : load_mod("module/hardening/repair_vuls.py"),
			#"1052" : load_mod("module/hardening/repair_vuls.py"),
			# "1060" : load_mod("module/filetransfer/sender_init.py"),
			# "1061" : load_mod("module/filetransfer/udp_setup_server.py"),
			# "1062" : load_mod("module/filetransfer/udp_setup_client.py"),
			# "1064" : load_mod("module/filetransfer/udp_punch.py"),
			# "1065" : load_mod("module/filetransfer/udp_punch_server.py"),
			# "1066" : load_mod("module/filetransfer/udp_punch_client.py"),
			# "1067" : load_mod(""
			# "1068" : load_mod("module/filetransfer/upload.py"),
			# "1069" : load_mod("module/filetransfer/download.py"),
			"1070" : load_mod("module/ueba/ueba_overview.py"),
			"1071" : load_mod("module/ueba/ueba_list.py"),
			"1072" : load_mod("module/ueba/ueba_detail.py"),
			#"1073" : load_mod("module/hardening/security_audit_scaner.py"),
			"1074" : load_mod("module/ueba/ueba_resolve.py"),
			"1075" : load_mod("module/ueba/ueba_delete_resolved.py"),

			#"1080" : load_mod("module/filetransfer/list_files.py"),
			#"1081" : load_mod("sync process"),
			#"1082" : load_mod("module/filetransfer/downloading.py"),

			"1090" : load_mod("module/status/get_resource_warnings.py"),
			"1091" : load_mod("module/status/clear_resource_warnings.py"),
			"1092" : load_mod("module/status/get_ports.py"),
			"1093" : load_mod("module/status/get_accounts.py"),
			"1094" : load_mod("module/status/fresh_ports.py"),
			"1095" : load_mod("module/status/fresh_accounts.py"),
			"1096" : load_mod("module/status/remove_port_change.py"),
			"1097" : load_mod("module/status/remove_account_change.py"),

			"1100" : load_mod("module/hardening/virusScannerQueryUnhandled.py"),
			"1101" : load_mod("module/hardening/virusScannerQueryHandled.py"),
			"1102" : load_mod("module/hardening/virusScannerQueryWhitelist.py"),
			"1103" : load_mod("module/hardening/virusScannerTrust.py"),
			"1104" : load_mod("module/hardening/virusScannerDelete.py"),
			"1105" : load_mod("module/hardening/virusScannerAddWhiteList.py"),
			"1106" : load_mod("module/hardening/virusScannerDelWhiteList.py"),
			"1107" : load_mod("module/hardening/virusScannerMoveTo.py"),
			"1108" : load_mod("module/hardening/virusScannerClearHistory.py"),

			"1119" : load_mod("module/baseline/get_baseline.py"),
			"1120" : load_mod("module/baseline/verify.py"),
			"1121" : load_mod("module/baseline/ignore.py")
		}

		if common.is_linux():
			self.modules["1008"] = load_mod("module/basic/overview.py")

		if common.is_windows():
			self.modules["10081"] = load_mod("module/basic/overview_win.py")

		if common.is_darwin():
			self.modules["10082"] = load_mod("module/basic/overview_mac.py")

		self.executor = ThreadPoolExecutor(max_workers = 6)
		self.unacked = False

		return True

	def on_unpack(self, *args, **kwargs):
		#data = args[0]
		#import cpacker
		#cpacker.do_unpack(data, self.modules)

		#if self.modules:
		#	Klogger().info("unpack success {} modules".format(len(self.modules)))
		#else:
		#	Klogger().error("unpack failed {} modules".format(len(self.modules)))

		if not self.unacked:
			self.executor.submit(run_mod, self.modules["1014"], None, None)
			self.executor.submit(run_mod, self.modules["1015"], None, None)
			self.executor.submit(run_mod, self.modules["1016"], None, None)
			#self.executor.submit(run_mod, self.modules["1048"], None, None)
			#self.executor.submit(run_mod, self.modules["1073"], None, None)

			self.unacked = True

	def create(self, socket, payload):
		cmd_id = payload["cmd_id"]

		#You can disable the features you don't prefer to apply at config/constant.py
		#By default, All features are enabled
		#if cmd_id in constant.ALLOW_MODULE_ID:
		#	if constant.ALLOW_MODULE_ID[cmd_id]["enabled"]:
		if not cmd_id in self.modules:
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
