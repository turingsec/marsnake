from utils.singleton import singleton
from utils import common, net_op
from core.security import Ksecurity
from core.logger import Klogger
from core.configuration import Kconfig
import re

@singleton
class Khttp():
	def __init__(self):
		pass

	def get_connection(self, addr, userID):
		host = None
		port = None

		data = "{};{}".format(userID, Ksecurity().get_pubkey())
		encrypt = Ksecurity().rsa_long_encrypt(data)

		Klogger().info("Request to Web server {} userid:{}".format(addr, userID))
		status, data = net_op.create_http_request(addr, "POST", "/get_logic_conn", encrypt)
		Klogger().info("Get Response From Gateway server status({})".format(status))

		if status == 200:
			data = Ksecurity().rsa_long_decrypt(data)

			if b":" in data:
				host, port = data.split(b":", 1)

				if common.is_python2x() is False:
					host = host.decode("ascii")
					port = port.decode("ascii")

			Klogger().info("Logic Server Host:{} Port:{}".format(host, port))

		return host, port
