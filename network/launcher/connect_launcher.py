from network.launcher.base_launcher import base_launcher
from network.ksocket import Ksocket
from network.khttp import Khttp
from config import constant
from core.logger import Klogger
from core.event import Kevent
from core.db import Kdatabase
import time

class connect_launcher(base_launcher):
	def __init__(self):
		self.socket = None

	def start(self):
		while True:
			try:
				username = Kdatabase().get_obj("setting")["username"]
				
				host, port = Khttp().get_connection(constant.SERVER_URL, username)
				
				if host and port:
					Kevent().do_unpack()

					self.socket = Ksocket(host, port, username)
					self.socket.start()
					self.socket.loop()
				else:
					Klogger().info("Reconnect to {} after 5s".format(marsnake_server))
					time.sleep(5)
					continue

			except Exception as e:
				Klogger().exception()

			if self.socket:
				self.socket.close()
				self.socket = None

			time.sleep(10)