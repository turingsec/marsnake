from utils.singleton import singleton
from utils import common, net_op
from core.security import Ksecurity
from core.logger import Klogger
import re, json, base64

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
			data = json.loads(data)
			
			if data["code"] == 0:
				destination = Ksecurity().rsa_long_decrypt(base64.b64decode(data["data"]))

				if b":" in destination:
					host, port = destination.split(b":", 1)
					host = host.decode("ascii")
					port = port.decode("ascii")

				Klogger().info("Logic Server Host:{} Port:{}".format(host, port))
			else:
				Klogger().info("Connect to Web server failed:{}".format(data["msg"]))

		return host, port