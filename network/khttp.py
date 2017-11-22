from utils.singleton import singleton
from utils import common
from core.security import Ksecurity
import base64, re

@singleton
class Khttp():
	def __init__(self):
		pass
		
	def get_connection(self, addr, userID):
		host = None
		port = None
		
		gate_host, gate_port = addr.rsplit(":", 1)
		
		if common.is_python2x():
			import httplib
			conn = httplib.HTTPConnection(gate_host, gate_port)
		else:
			from http.client import HTTPConnection
			conn = HTTPConnection(gate_host, gate_port)
			
		data = "{};{}".format(userID, Ksecurity().get_pubkey())
		encrypt = Ksecurity().rsa_long_encrypt(data, 200)
		
		conn.request("POST", 
					"/xxx", 
					encrypt, 
					{"Content-type": "application/octet-stream", "Accept": "text/plain"})
					
		res = conn.getresponse()
		
		if res.status == 200:
			
			data = res.read()
			data = Ksecurity().rsa_long_decrypt(data, 256)
			
			if ":" in data:
				host, port, en_mods = data.split(":", 2)
				pattern = re.compile(r"<data>(.*)</data>", re.S)
				match = re.search(pattern, en_mods)

				if match and len(match.groups()):
					en_mods = match.groups()[0]

		conn.close()
		
		return host, port, en_mods