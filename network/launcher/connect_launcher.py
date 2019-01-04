from network.launcher.base_launcher import base_launcher
from network.ksocket import Ksocket
from network.khttp import Khttp
from core.profile_reader import KProfile
from core.logger import Klogger
from core.event import Kevent
import time

class connect_launcher(base_launcher):
	def __init__(self):
		self.socket = None

	def start(self):
		while True:
			try:
				server_setting = KProfile().read_key("server")
				marsnake_server = "{}:{}".format(server_setting["host"], server_setting["port"])

				host, port = Khttp().get_connection(marsnake_server, KProfile().read_key("username"))

				if host and port:
					Kevent().do_unpack()

					self.socket = Ksocket(host, port, KProfile().read_key("username"))
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
