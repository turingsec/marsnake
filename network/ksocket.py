from module.factory_module import Kmodules
from utils.randomize import Krandom
from config import constant
from ctypes import create_string_buffer
from core.security import Ksecurity
from core.logger import Klogger
import socket, json, struct, threading

class stream():
	def __init__(self, size):
		self.buffer = create_string_buffer(size)
		self.size = size
		self.index = 0
		
	def write(self, data):
		if self.index + len(data) > self.size:
			Klogger().error("index:{} len(data):{} size:{}".format(self.index, len(data), self.size))
			raise
			
		for i in range(len(data)):
			self.buffer[self.index] = data[i]
			self.index += 1
			
	def get_len(self):
		return self.index
		
	def get_data(self, start, wanted):
		if self.index < start + wanted :
			return None
			
		return self.buffer[start:start + wanted]
		
	def clear(self, total):
		diff = self.index - total
		
		if diff == 0:
			self.index = 0
			return
		elif diff > 0:
			for i in range(diff):
				self.buffer[i] = self.buffer[total + i]
				
			self.index = diff
		else:
			raise "diff({}) < 0".format(diff)
			
class Ksocket():
	def __init__(self, host, port, userid, nodelay = False, keepalive = True):
		self.host = host
		self.port = port
		self.userid = userid
		
		self.family = socket.AF_INET
		self.type = socket.SOCK_STREAM
		
		self.nodelay = nodelay
		self.keepalive = keepalive
		
		self.input = stream(constant.SOCKET_BUFFER_SIZE)
		self.output = stream(constant.SOCKET_BUFFER_SIZE)
		
		self.lock = threading.Lock()
		
	def start(self):
		family, socktype, proto, _, sockaddr = socket.getaddrinfo(self.host, self.port, self.family, self.type)[0]
		
		sock = socket.socket(family, socktype)
		sock.connect(sockaddr)
		
		if self.nodelay:
			sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
			
		if self.keepalive:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
			
		if hasattr(socket, "TCP_KEEPIDLE") and hasattr(socket, "TCP_KEEPINTVL") and hasattr(socket, "TCP_KEEPCNT"):
			sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1 * 60)
			sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)
			sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
		elif hasattr(socket, "SIO_KEEPALIVE_VALS"):
			sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 1 * 60 * 1000, 5 * 60 * 1000))
			
		self.sock = sock
		self.recv_count = 0

		Ksecurity().reset_aes()

	def loop(self):
		while True:
			request = self.sock.recv(constant.SOCKET_RECV_SIZE)
			
			if not len(request):
				Klogger().info("server closed!")
				break;
				
			self.input.write(request)
			#self.print2hex(self.input.get_data(0, self.input.get_len()))
				
			while self.handle_package():
				pass

	def handle_package(self):
		recv_len = self.input.get_len()
		
		if recv_len < 36:
			return False
			
		plen = self.input.get_data(32, 4)
		plen = struct.unpack('>I', plen)[0]
		
		total = 32 + 4 + plen + 16
		
		if recv_len < total:
			return False
		
		payload = self.input.get_data(36, plen)
		self.input.clear(total)
		
		self.handle_package_2(payload)
		
		return True
		
	def handle_package_2(self, payload):
		if self.recv_count == 0:
			payload = json.loads(payload)
			Klogger().info("recv:{}".format(payload))
			if payload["cmd_id"] == "10000":
				Ksecurity().swap_publickey_with_server(self)		
				
		elif self.recv_count == 1:
			payload = json.loads(payload)
			Klogger().info("recv:{}".format(payload))
			if payload["cmd_id"] == "1000":
				payload["user_id"] = self.userid
				Kmodules().create(self, payload)
		else:
			payload = Ksecurity().aes_decrypt(payload)
			payload = json.loads(payload)

			if payload["cmd_id"] in ["1000", "1008", "1017", "10081"]:
				Klogger().info("recv:{}".format(payload))

			if payload["args"]["user_id"] == self.userid:
				Kmodules().create(self, payload)
				
		self.recv_count += 1
		
	def response(self, payload):
		try:
			'''
			if payload["cmd_id"] in constant.MSG_ID:
				print("cmd_id:{} sended".format(payload["cmd_id"]))
				print(payload)
				print("")
			'''
			with self.lock:
				if payload["cmd_id"] in ["1000", "1008", "1017", "10081"]:
					Klogger().info(payload)
				
				prefix = struct.pack("32s", Krandom().purely(32))
				suffix = struct.pack("16s", Krandom().purely(16))
				payload = json.dumps(payload)
				
				if Ksecurity().can_aes_encrypt():
					payload = Ksecurity().aes_encrypt(payload)
					
				payload_len = struct.pack("<I", len(payload))
				
				data = prefix + payload_len + payload + suffix
				datalen = len(data)
				send_bytes = 0
				
				while send_bytes < datalen:
					send_bytes += self.sock.send(data[send_bytes:])
					
		except Exception as e:
			Klogger().error(str(e))
			
	def close(self):
		if hasattr(self, "sock"):
			self.sock.close()