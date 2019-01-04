from utils.singleton import singleton
from utils.randomize import Krandom
from utils import common, time_op, file_op
from core.event.base_event import base_event
from config import constant
from io import BytesIO
import os, zipfile, base64
import socket
import sys
import stun
import json
import shutil

@singleton
class Kicloud(base_event):
	def __init__(self):
		self.sock = None
		self.download_cache = {}
		self.upload_cache = {}

	def on_initializing(self, *args, **kwargs):
		return True

	def init(self, pair_id, device_id, server_ip, server_port):
		nat_type, external_ip, external_port = stun.get_ip_info()

		# Create a UDP/IP socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		response = {
			"nat_type" : nat_type,
			"pair_id" : pair_id,
			"device_id" : device_id
		}

		self.sock.sendto(json.dumps(response).encode("ascii"), (server_ip, server_port))

	def punch_as_client(self, pair_id, target_ip, target_port, random_code):
		self.sock.sendto(random_code, (target_ip, target_port))

	def punch_as_server(self, pair_id, target_ip, target_port, random_code, tcp_socket):
		self.random_code = random_code
		self.sock.sendto(Krandom().purely(8), (target_ip, target_port))

		i = 0

		while(i < 10):
			data, addr = self.sock.recvfrom(1024)

			if data == self.random_code:
				response = {
					"cmd_id" : "1067",
					"pair_id" : pair_id,
					"error" : ""
				}

				tcp_socket.response(response)

			i += 1

	def download_check(self, path, items):
		for i in items:
			item = os.path.join(path, i)

			if not os.path.exists(item):
				return "{} NOTEXIST".format(item)

			if not os.path.isabs(item):
				return "{} NOTABSOLUTEPATH".format(item)

			readable, unread_item = file_op.check_abspath_readable(item, True)

			if not readable:
				return "{} CANNOTBEREAD".format(unread_item)

		return ""

	def download_prepare(self, identity, path, items):
		filename = None
		content = None
		is_ok = False

		if len(items) == 1:
			file_path = os.path.join(path, items[0])

			if os.path.isfile(file_path):
				content = file_op.cat(file_path)
				filename = items[0]
				is_ok = True

		if not is_ok:
			filename = "{}.zip".format(time_op.localtime2string())
			f = BytesIO()
			zf = zipfile.ZipFile(f, mode = 'w', compression = zipfile.ZIP_DEFLATED)

			for i in items:
				i = common.path_translate(i)
				item = os.path.join(path, i)
				filelist = []

				file_op.enum_file_path(item, filelist)

				for file in filelist:
					try:
						zipname = file[len(path) + 1:]
						zipname = zipname.replace('\\', '/')

						zf.write(file, zipname)
					except:
						pass

			zf.close()
			content = f.getvalue()
			f.close()

		encoded = base64.b64encode(content).decode("ascii")

		self.download_cache[identity] = {
			"begin_time" : time_op.now(),
			"last_time" : time_op.now(),
			"content" : encoded,
			"total" : len(encoded),
			"sent_bytes" : 0,
			"filename" : filename,
		}

		print(self.download_cache[identity])

	def download(self, payload, socket):
		identity = payload["args"]["identity"]

		if not identity or identity in self.download_cache:
			return

		path = payload["args"]["path"]
		items = payload["args"]["items"]
		session_id = payload["args"]["session_id"]
		error = self.download_check(path, items)

		if error:
			socket.response({
				"cmd_id" : payload["cmd_id"],
				"session_id" : session_id,
				"error" : error
			})
			return

		self.download_prepare(identity, path, items)

		socket.response({
			"cmd_id" : payload["cmd_id"],
			"session_id" : session_id,
			"identity" : identity,
			"error" : ""
		})

	def downloading(self, identity, socket, session_id):
		if identity not in self.download_cache:
			return

		cache = self.download_cache[identity]

		sent_bytes = cache["sent_bytes"]
		content = cache["content"]
		total = cache["total"]
		filename = cache["filename"]

		if sent_bytes < total:
			left = total - sent_bytes
			send = constant.FILE_TRANSFER_SIZE_PER_TIME if left > constant.FILE_TRANSFER_SIZE_PER_TIME else left
			block = content[sent_bytes:sent_bytes + send]
			sent_bytes += send

			cache["sent_bytes"] += send
			cache["last_time"] = time_op.now()

			self.sync_download_progress(socket, session_id, identity, sent_bytes, total, filename, block)

	def uploading(self, args, socket):
		datalen = args["data_len"]
		filename = args["filename"]
		identity = args["identity"]
		error = ""

		if identity not in self.upload_cache:
			self.upload_cache[identity] = {
				"begin_time" : time_op.now(),
				"last_time" : time_op.now(),
				"path" : args["path"],
				"filename" : filename,
				"total" : datalen,
				"received" : 0,
				"content" : bytearray()
			}

		cache = self.upload_cache[identity]
		cache["content"].extend(bytearray(args["data"]))
		cache["received"] += len(args["data"])

		if cache["received"] == cache["total"]:
			item_new_path = os.path.join(cache["path"], cache["filename"])

			if os.path.exists(item_new_path):
				item_new_path = "{}-{}".format(item_new_path, time_op.localtime2string())

			try:
				with open(item_new_path, "ab") as f:
					f.write(cache["content"])
			except Exception as e:
				error = str(e)
				print(error)
			finally:
				del self.upload_cache[identity]

			socket.response({
				"cmd_id" : "1068",
				"session_id" : args["session_id"],
				"identity" : identity,
				"error" : ""
			})

		self.sync_upload_progress(socket, args["session_id"], identity, cache["received"], datalen, filename, error)

	def sync_download_progress(self, socket, session_id, identity, received, total, filename, data):
		socket.response({
			"cmd_id" : "1082",
			"session_id" : session_id,
			"percent" : round(received / total, 4),
			"received" : received,
			"total" : total,
			"filename" : filename,
			"identity" : identity,
			"data" : data
		})

	def sync_upload_progress(self, socket, session_id, identity, received, total, filename, error):
		socket.response({
			"cmd_id" : "1081",
			"session_id" : session_id,
			"percent" : round(received / total, 4),
			"received" : received,
			"total" : total,
			"filename" : filename,
			"identity" : identity,
			"error" : error
		})
