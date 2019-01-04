from core.db import Kdatabase
from utils.singleton import singleton
from utils.randomize import Krandom
from utils import common, time_op
import psutil

@singleton
class Kfingerprint():
	def __init__(self):
		pass

	def record_account(self):
		fingerprint = Kdatabase().get_obj("fingerprint")

		if common.is_linux():
			import pwd
			pwall_users = pwd.getpwall()

	def record_listening_port(self):
		listening = []
		fingerprint = Kdatabase().get_obj("fingerprint")
		now = time_op.now()

		for proc in psutil.process_iter():
			try:
				connections = proc.connections(kind = "inet4")
			except Exception as e:
				connections = []

			if connections:
				for conn in connections:
					if conn.laddr:
						local_port = conn.laddr[1]
						local_ip = conn.laddr[0]

						if conn.status == "LISTEN":
							try:
								create_time = int(proc.create_time())
								user = proc.username()
								cmdline = proc.cmdline()
								exe = common.decode2utf8(proc.exe())
							except Exception as e:
								exe = "Unknown"

							protocol = "Unknown"

							if conn.type == 1:
								protocol = "TCP"
							elif conn.type == 2:
								protocol = "UDP"

							listening.append({
								"port": local_port,
								"ip": local_ip,
								"create_time": create_time,
								"user": user,
								"cmdline": cmdline,
								"exe": exe,
								"protocol": protocol
							})

		old_list = fingerprint["port"]["current"]
		change = fingerprint["port"]["change"]

		#检查新增端口
		for info_1 in listening:
			exists = False

			for info_2 in old_list:
				if info_1["port"] == info_2["port"]:
					exists = True
					break

			if not exists:
				change[Krandom().purely(8)] = {
					"port": info_1["port"],
					"ts": now,
					"flag": 0	#新增
				}

		#检查减少端口
		for info_1 in old_list:
			exists = False

			for info_2 in listening:
				if info_1["port"] == info_2["port"]:
					exists = True
					break

			if not exists:
				change[Krandom().purely(8)] = {
					"port": info_1["port"],
					"ts": now,
					"flag": 1	#减少
				}

		fingerprint["port"]["current"] = listening
		fingerprint["port"]["change"] = change
		fingerprint["port"]["lasttime"] = now

		Kdatabase().dump("fingerprint")
