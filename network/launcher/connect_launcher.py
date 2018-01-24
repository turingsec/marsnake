from network.launcher.base_launcher import base_launcher
from network.ksocket import Ksocket
from network.khttp import Khttp
from core.configuration import Kconfig
from module.factory_module import Kmodules
from core.logger import Klogger
from core.event import Kevent
import argparse, time, traceback

class connect_launcher(base_launcher):
	"connect_launcher"
	def __init__(self):
		self.socket = None
		
	def start(self):
		while True:
			try:
				host, port, en_mods = Khttp().get_connection(Kconfig().server, Kconfig().credential)
				Kmodules().unpacker(en_mods)
				
				self.socket = Ksocket(host, port, Kconfig().credential)
				
				self.socket.start()
				self.socket.loop()
				
			except Exception as e:
				Klogger().error(str(e))
				traceback.print_exc()
				
			Kevent().do_disconnected()
			
			if self.socket:
				self.socket.close()
				self.socket = None
				
			time.sleep(10)