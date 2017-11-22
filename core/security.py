import os, base64
from utils.singleton import singleton
from utils import common
from utils.configuration import Kconfig
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES

PADDING = '{'
BLOCK_SIZE = 16

# one-liner to sufficiently pad the text to be encrypted
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

@singleton
class Ksecurity():
	def __init__(self):
		self.aes = None
		self.iv = None

	def init(self):
		self.client_publickey = Kconfig().client_publickey
		self.client_privatekey = Kconfig().client_privatekey

	def rsa_long_encrypt(self, msg, length = 100):
		msg = msg.encode("utf8")
		pubobj = RSA.importKey(Kconfig().server_publickey)
		pubobj = PKCS1_OAEP.new(pubobj)
		res = []

		for i in range(0, len(msg), length):
			res.append(pubobj.encrypt(msg[i : i + length]))

		return "".join(res)

	def rsa_long_decrypt(self, msg, length = 128):
		privobj = RSA.importKey(self.client_privatekey)
		privobj = PKCS1_OAEP.new(privobj)
		res = []

		for i in range(0, len(msg), length):
			res.append(privobj.decrypt(msg[i : i + length]))

		return "".join(res)

	def get_pubkey(self):
		return self.client_publickey

	def swap_publickey_with_server(self, socket):
		response = {
			"cmd_id" : "10000",
			"key" : self.get_pubkey()
		}

		socket.response(response)
		
	def set_aes_iv(self, aes, iv):
		if aes and iv:
			self.aes = aes
			self.iv = iv
	
	def can_aes_encrypt(self):
		return self.aes and self.iv

	def reset_aes(self):
		self.aes = None
		self.iv = None

	def aes_encrypt(self, data):
		aes_obj_enc = AES.new(self.aes, AES.MODE_CBC, self.iv)
		return aes_obj_enc.encrypt(pad(data))
		
	def aes_decrypt(self, encrypt):
		aes_obj_enc = AES.new(self.aes, AES.MODE_CBC, self.iv)
		return aes_obj_enc.decrypt(encrypt).rstrip(PADDING)