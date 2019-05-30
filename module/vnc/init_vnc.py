from ctypes import *
from struct import pack, unpack
from time import time, sleep
from threading import Thread, Lock, currentThread
from utils import common
from core.logger import Klogger
import os, socket, json, psutil

vnc_running = False

class PIXEL_FORMAT(Structure):
	_fields_ = [("bits_per_pixel", c_uint8),
				("depth", c_uint8),
				("big_endian_flag", c_uint8),
				("true_colour_flag", c_uint8),
				("red_max", c_uint16),
				("green_max", c_uint16),
				("blue_max", c_uint16),
				("red_shift", c_uint8),
				("green_shift", c_uint8),
				("blue_shift", c_uint8)]

class FRAMEBUFFER_UPDATE_REQUEST(Structure):
	_fields_ = [("x_position", c_uint16),
				("y_position", c_uint16),
				("width", c_uint16),
				("height", c_uint16)]

class Connection:
	client = None

	def __init__(self, ip, port, key):
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		try:
			self.client.connect((ip, port))
			self.send(json.dumps({"key": key}).encode("ascii"))
		except Exception as e:
			print("VNC connection error:", e)
			self.client.close()
			self.client = None

	def send(self, msg):
		return self.client.sendall(msg)

	def recv(self, msglen):
		assert msglen >= 0

		if msglen == 0:
			return b''

		data = self.client.recv(msglen)

		if data == b'':
			raise Exception("ConnectionClosed")

		while len(data) < msglen:
			data += self.client.recv(msglen - len(data))

		return data

	def gethostname(self):
		return socket.gethostname()

class MiscLibrary:
	def __init__(self):
		if common.is_linux():
			envret = setenv()
			if envret == False:
				raise Exception("Can not set important environment!Maybe use XWayland.")
			if common.is_x86_64():
				misc_path = "lib/linux/x64/misc.so"
			else:
				misc_path = "lib/linux/x86/misc.so"

			self._lib = CDLL(os.path.join(common.get_work_dir(), misc_path))

		elif common.is_windows():
			self._lib = CDLL(os.path.join(
				common.get_work_dir(), "lib/windows/misc.dll"))
		else:
			raise Exception("Not support on macos")

		ret = self._lib.GlobalInit()

		if ret != 0:
			raise Exception("MiscGlobalInitFailed")

		self._buffer = create_string_buffer(4194304)

	def ServerInitMessage(self):
		framebuffer_width = c_uint16()
		framebuffer_height = c_uint16()
		server_pixel_format = PIXEL_FORMAT()

		ret = self._lib.ServerInitMessage(byref(framebuffer_width), byref(
			framebuffer_height), byref(server_pixel_format))
		if ret != 0:
			raise Exception("Misc_ServerInitMessage failed")

		return (framebuffer_width.value, framebuffer_height.value, server_pixel_format)

	def FrameBufferUpdate(self, pixel_format, framebuffer_update_request, jpeg_quality):
		data_len = c_uint32()

		if framebuffer_update_request is None:
			ret = self._lib.FrameBufferUpdate(byref(data_len), self._buffer, byref(
				pixel_format), None, c_uint32(jpeg_quality))
		else:
			ret = self._lib.FrameBufferUpdate(byref(data_len), self._buffer, byref(
				pixel_format), byref(framebuffer_update_request), c_uint32(jpeg_quality))

		if ret != 0:
			raise Exception("Misc_FrameBufferUpdate failed")

		return (data_len.value, memoryview(self._buffer))

	def SetKey(self, down_flag, key):
		self._lib.SetKey(c_uint8(down_flag), c_uint32(key))

	def SetPointer(self, button_mask, x_position, y_position):
		self._lib.SetPointer(c_uint8(button_mask), c_uint16(
			x_position), c_uint16(y_position))

	def SetClipBoard(self, text_len, text):
		self._lib.SetClipBoard(c_uint32(text_len), c_char_p(text))

# RFB 3.8 Magic String
ProtocolVersion = b"\x52\x46\x42\x20\x30\x30\x33\x2e\x30\x30\x38\x0a"
ProtocolFailedReasonString = b"Protocol not supported."
SecurityFailedReasonString = b"Invalid security type."
# Security type Magic Number
SEC_Invalid = b'\x00'
SEC_None = b'\x01'
SEC_VNCAuth = b'\x02'
# ClientToServerMessage
MSG_SetPixelFormat = b'\x00'
MSG_SetEncodings = b'\x02'
MSG_FrameBufferUpdateRequest = b'\x03'
MSG_KeyEvent = b'\x04'
MSG_PointerEvent = b'\x05'
MSG_ClientCutText = b'\x06'
# Encodings
ENCODE_RAW = b'\x00\x00\x00\x00'
ENCODE_TIGHT = b'\x00\x00\x00\x07'

class RFBServer():

	def __init__(self, ip_addr, ip_port, key):
		self._misc = MiscLibrary()
		self._conn = Connection(ip_addr, ip_port, key)

		# variables
		self._state = 0
		self._fps = 7.0
		self._supportedSecurityType = [SEC_None]
		self._selectedSecurityType = None
		self._encodings = None
		self._jpegQuality = 50
		self._jpegQualityTopLimit = 60
		self._jpegQualityBottomLimit = 10

		# global variable requires lock
		self._pixelFormat = PIXEL_FORMAT()
		self._pixelFormatLock = Lock()
		self._frameBufferUpdateRequest = None
		self._frameBufferUpdateRequestLock = Lock()

		# threads
		self._t_ClientMessageHandlerThread = None
		self._t_FrameBufferUpdateThread = None

		sleep(1)

	def _handshakeVersion(self):
		# step1: server send a message indicates the highest supported protocol version
		# step2: client choose a protocol version
		self._conn.send(ProtocolVersion)

		if self._conn.recv(12) != ProtocolVersion:
			self._conn.send(pack(">B", 0))
			self._conn.send(
				pack(">I", len(ProtocolFailedReasonString)) + ProtocolFailedReasonString)

			raise Exception("ProtocolVersionNotSupported")
		else:
			self._state = 1

	def _handshakeSecurity(self):
		assert self._state == 1
		# step1: server send a message indicates security types supported
		# step2: client choose a security type
		self._conn.send(pack(">B", len(self._supportedSecurityType)) +
						b''.join(self._supportedSecurityType))
		self._selectedSecurityType = self._conn.recv(1)

		if not self._selectedSecurityType in self._supportedSecurityType:
			self._conn.send(pack(">I", 1))
			self._conn.send(
				pack(">I", len(SecurityFailedReasonString)) + SecurityFailedReasonString)

			raise Exception("InvalidSecurityTypeClientSelected")
		else:
			self._conn.send(pack(">I", 0))
			self._state = 2

	def _initialisationClientInit(self):
		assert self._state == 2
		# recv a clientinit message which includes a shared-flag, just ignore
		self._conn.recv(1)
		self._state = 3

	def _initialisationServerInit(self):
		assert self._state == 3
		# send a serverinit message
		name_string = self._conn.gethostname()
		framebuffer_width, framebuffer_height, self._pixel_format = self._misc.ServerInitMessage()

		self._conn.send(b''.join((pack(">H", framebuffer_width),
								 pack(">H", framebuffer_height),
								 pack(">B", self._pixel_format.bits_per_pixel),
								 pack(">B", self._pixel_format.depth),
								 pack(">B", self._pixel_format.big_endian_flag),
								 pack(">B", self._pixel_format.true_colour_flag),
								 pack(">H", self._pixel_format.red_max),
								 pack(">H", self._pixel_format.green_max),
								 pack(">H", self._pixel_format.blue_max),
								 pack(">B", self._pixel_format.red_shift),
								 pack(">B", self._pixel_format.green_shift),
								 pack(">B", self._pixel_format.blue_shift),
								 b"\x00\x00\x00",
								 pack(">I", len(name_string)), name_string.encode(common.os_encoding))))
		self._state = 4

	def HandShake(self):
		# handshake stage
		self._handshakeVersion()
		self._handshakeSecurity()

		assert self._state == 2

	def Initialisation(self):
		self._initialisationClientInit()
		self._initialisationServerInit()
		assert self._state == 4

	def FrameBufferUpdateThread(self):
		global vnc_running

		jpegquality_up_counter = 0
		jpegquality_down_counter = 0

		Klogger().info("FrameBufferUpdateThread started")

		# start client message handler thread
		t  = Thread(target=self.ClientMessageHandlerThread, args=(currentThread(), ))
		t.daemon = True
		t.start()

		self._t_ClientMessageHandlerThread = t

		while True:
			if self._t_ClientMessageHandlerThread.isAlive() == False:
				Klogger().info("FrameBufferUpdateThread end")
				vnc_running = False
				break

			start_time = time()

			self._pixelFormatLock.acquire()
			self._frameBufferUpdateRequestLock.acquire()

			data_len, data = self._misc.FrameBufferUpdate(
				self._pixel_format, self._frameBufferUpdateRequest, self._jpegQuality)

			self._frameBufferUpdateRequest = None
			self._pixelFormatLock.release()
			self._frameBufferUpdateRequestLock.release()

			start_send_time = time()

			try:
				self._conn.send(data[:data_len])
			except:
				Klogger().info("FrameBufferUpdateThread end")
				break

			send_interval = time() - start_send_time
			interval = time() - start_time

			# congest control
			if (send_interval > ((1.0 / self._fps) - 0.06)):
				jpegquality_down_counter += 1
				jpegquality_up_counter = 0
			elif (send_interval < ((1.0 / self._fps) - 0.09)):
				jpegquality_up_counter += 1
				jpegquality_down_counter = 0
			else:
				jpegquality_down_counter = 0
				jpegquality_up_counter = 0

			if jpegquality_up_counter > 4 * self._fps:
				jpegquality_up_counter = 0
				self._jpegQuality = (self._jpegQuality + 10) if (
					self._jpegQuality < self._jpegQualityTopLimit) else self._jpegQualityTopLimit

			if jpegquality_down_counter > 1 * self._fps:
				jpegquality_down_counter = 0
				self._jpegQuality = (self._jpegQuality - 10) if (self._jpegQuality >
																 self._jpegQualityBottomLimit) else self._jpegQualityBottomLimit

			if interval < (1.0 / self._fps):
				sleep((1.0 / self._fps) - interval)

	def ClientMessageHandlerThread(self, parent_thread):
		global vnc_running

		# enter an infinite loop to handle client's request
		while True:
			if parent_thread.isAlive() == False:
				Klogger().info("ClientMessageHandlerThread end")
				vnc_running = False
				break

			try:
				request = self._conn.recv(1)
			except:
				Klogger().info("ClientMessageHandlerThread end")
				break

			if request == MSG_SetPixelFormat:
				pixel_format_inbyte = self._conn.recv(19)
				pixel_format_inbyte = pixel_format_inbyte[3:]
				self._pixelFormatLock.acquire()
				(self._pixelFormat.bits_per_pixel, ) = unpack(
					">B", pixel_format_inbyte[0:1])
				(self._pixelFormat.depth, ) = unpack(
					">B", pixel_format_inbyte[1:2])
				(self._pixelFormat.big_endian_flag, ) = unpack(
					">B", pixel_format_inbyte[2:3])
				(self._pixelFormat.true_colour_flag, ) = unpack(
					">B", pixel_format_inbyte[3:4])
				(self._pixelFormat.red_max, ) = unpack(
					">H", pixel_format_inbyte[4:6])
				(self._pixelFormat.green_max, ) = unpack(
					">H", pixel_format_inbyte[6:8])
				(self._pixelFormat.blue_max, ) = unpack(
					">H", pixel_format_inbyte[8:10])
				(self._pixelFormat.red_shift, ) = unpack(
					">B", pixel_format_inbyte[10:11])
				(self._pixelFormat.green_shift, ) = unpack(
					">B", pixel_format_inbyte[11:12])
				(self._pixelFormat.blue_shift, ) = unpack(
					">B", pixel_format_inbyte[12:13])
				self._pixelFormatLock.release()
			elif request == MSG_SetEncodings:
				number_of_encodings = self._conn.recv(3)
				(number_of_encodings, ) = unpack(">H", number_of_encodings[1:])
				encodings_inbyte = self._conn.recv(number_of_encodings * 4)

				self._encodings = [encodings_inbyte[x: x + 4]
								   for x in range(0, number_of_encodings * 4, 4)]

				if not ENCODE_TIGHT in self._encodings:
					raise Exception("TightEncodingNotSupported")
			elif request == MSG_FrameBufferUpdateRequest:
				interested_area = self._conn.recv(9)

				if interested_area[0] != b'\x00':
					continue

				(x_position, ) = unpack(">H", interested_area[1:3])
				(y_position, ) = unpack(">H", interested_area[3:5])
				(width, ) = unpack(">H", interested_area[5:7])
				(height, ) = unpack(">H", interested_area[7:9])
				self._frameBufferUpdateRequestLock.acquire()
				self._frameBufferUpdateRequest = FRAMEBUFFER_UPDATE_REQUEST(
					x_position, y_position, width, height)
				self._frameBufferUpdateRequestLock.release()

			elif request == MSG_KeyEvent:
				key_event = self._conn.recv(7)
				(down_flag, ) = unpack(">B", key_event[0:1])
				(key, ) = unpack(">I", key_event[3:7])

				self._misc.SetKey(down_flag, key)
			elif request == MSG_PointerEvent:
				pointer_event = self._conn.recv(5)
				(button_mask, ) = unpack(">B", pointer_event[0:1])
				(x_position, ) = unpack(">H", pointer_event[1:3])
				(y_position, ) = unpack(">H", pointer_event[3:5])

				self._misc.SetPointer(button_mask, x_position, y_position)
			elif request == MSG_ClientCutText:
				text_len = self._conn.recv(7)
				(text_len, ) = unpack(">I", text_len[3:7])
				text = self._conn.recv(text_len)

				self._misc.SetClipBoard(text_len, text)
			else:
				raise Exception("UnknownClientMessage")

	def VNCServerLoopStart(self):
		assert self._state == 4

		self._t_FrameBufferUpdateThread = Thread(target=self.FrameBufferUpdateThread, args=())
		self._t_FrameBufferUpdateThread.start()

def run(payload, socket):
	global vnc_running

	host = payload["args"]["host"]
	port = payload["args"]["port"]
	key = payload["args"]["key"]

	response = {
		'cmd_id' : payload['cmd_id'],
		'session_id' : payload["args"]["session_id"],
		'key' : key,
		'error' : ""
	}

	if vnc_running == True:
		response['error'] = "VNC is already running"
		socket.response(response)

	else:
		socket.response(response)

		try:
			vnc_running = True

			r = RFBServer(host, port, key)

			r.HandShake()
			r.Initialisation()
			r.VNCServerLoopStart()

		except Exception as e:
			vnc_running = False
			Klogger().error("VNC handshake %s" % (str(e), ))

def setenv():
	ENV_DIS = ""
	ENV_XAUTH = ""

	if 'DISPLAY' in os.environ and 'XAUTHORITY' in os.environ:
		return True

	for process in psutil.process_iter():
		try:
			envir = process.environ()
		except:
			continue

		if 'DISPLAY' in envir:
			ENV_DIS = envir['DISPLAY']

		if 'XAUTHORITY' in envir:
			ENV_XAUTH = envir['XAUTHORITY']

		if ENV_DIS and ENV_XAUTH:
			break

	if ENV_DIS and ENV_XAUTH:
		os.environ['DISPLAY'] = ENV_DIS
		os.environ['XAUTHORITY'] = ENV_XAUTH
		return True
	else:
		return False
