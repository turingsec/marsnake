from utils.singleton import singleton
from utils import common
from core.configuration import Kconfig
from core.event.base_event import base_event
import os, base64, rsa

PADDING = b'{'
BLOCK_SIZE = 16

# one-liner to sufficiently pad the text to be encrypted
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

@singleton
class Ksecurity(base_event):
	def __init__(self):
		self.aes = None
		self.iv = None

	def on_initializing(self, *args, **kwargs):
		# random_generator = Random.new().read
		# rsa = RSA.generate(1024, random_generator)

		# private_pem = rsa.exportKey()

		# with open('master-private.pem', 'w') as f:
		#     f.write(private_pem)

		# public_pem = rsa.publickey().exportKey()
		# with open('master-public.pem', 'w') as f:
		#     f.write(public_pem)

		#self.client_publickey = Kconfig().client_publickey
		#self.client_privatekey = Kconfig().client_privatekey

		(self.pubkey, self.privkey) = rsa.newkeys(1024)
		self.server_pubkey = rsa.PublicKey.load_pkcs1(Kconfig().server_publickey)

		return True
		
	def rsa_long_encrypt(self, msg, length = 100):
		# msg = msg.encode("utf8")
		# pubobj = RSA.importKey(Kconfig().server_publickey)
		# pubobj = PKCS1_OAEP.new(pubobj)
		# res = []

		# for i in range(0, len(msg), length):
		# 	res.append(pubobj.encrypt(msg[i : i + length]))

		# return b"".join(res)

		msg = msg.encode("utf8")
		res = []

		for i in range(0, len(msg), length):
			res.append(rsa.encrypt(msg[i : i + length], self.server_pubkey))

		return b"".join(res)

	def rsa_long_decrypt(self, crypto, length = 128):
		# privobj = RSA.importKey(self.client_privatekey)
		# privobj = PKCS1_OAEP.new(privobj)
		# res = []

		# for i in range(0, len(crypto), length):
		# 	res.append(privobj.decrypt(crypto[i : i + length]))

		# return b"".join(res)

		res = []

		for i in range(0, len(crypto), length):
			res.append(rsa.decrypt(crypto[i : i + length], self.privkey))

		return b"".join(res)

	def get_pubkey(self):
		return self.pubkey.save_pkcs1().decode()

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
		count = 0
		encrypt = []

		if common.is_python2x():
			for i in data:
				encrypt.append(chr(ord(i) ^ ord(self.aes[count % len(self.aes)])))
				count += 1
			
			return b"".join(encrypt)
		else:
			for i in data:
				encrypt.append(i ^ self.aes[count % len(self.aes)])
				count += 1

			return bytes(encrypt)
				
		#aes_obj_enc = AES.new(self.aes, AES.MODE_CBC, self.iv)
		#return aes_obj_enc.encrypt(pad(data))
		
	def aes_decrypt(self, encrypt):
		return self.aes_encrypt(encrypt)
		#aes_obj_enc = AES.new(self.aes, AES.MODE_CBC, self.iv)
		#return aes_obj_enc.decrypt(encrypt).rstrip(PADDING)
