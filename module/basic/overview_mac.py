from utils import lib, common, file_op, time_op
from utils.randomize import Krandom
from datetime import datetime
from core.logger import Klogger
from core.db import Kdatabase
from core.language import Klanguage

import platform, psutil, os, sys, pwd, getpass, json, time, locale

def get_system_info(response):
	system_info = response["system_info"]
	home, shell = home_shell()

	system_info.append({Klanguage().to_ts(1020) : home})
	system_info.append({Klanguage().to_ts(1021) : shell})

	system_info.append({Klanguage().to_ts(1023) : platform.python_version()})

	system_info.append({Klanguage().to_ts(1024) : "{}/{}".format(platform.system(), platform.machine())})
	system_info.append({Klanguage().to_ts(1025) : "{}".format(common.get_distribution())})
	system_info.append({Klanguage().to_ts(1026) : platform.release()})

	system_info.append({Klanguage().to_ts(1027) : time_op.timestamp2string(psutil.boot_time())})
	system_info.append({Klanguage().to_ts(1028) : time_op.timestamp2string(time.time())})

def home_shell():
	user_shell = "unknown"
	user_home = "unknown"
	users = pwd.getpwall()

	for user in users:
		if user[0] == getpass.getuser():
			user_home = user[5]
			user_shell = user[6]
			break

	return user_home, user_shell

def get_mem_disk_info(response):
	#name	STATS   USED	MOUNT   FILESYSTEM
	for item in psutil.disk_partitions():
		device, mountpoint, fstype, opts = item

		try:
			total, used, free, percent = psutil.disk_usage(mountpoint)

			response["disk"][device] = percent
		except Exception:
			pass

	mem = psutil.virtual_memory()
	response["ram"]["total"] = common.size_human_readable(mem[0])
	response["ram"]["used"] = common.size_human_readable(mem[3])

def get_garbage(response):
	cleaner = Kdatabase().get_obj("cleaner")

	for kind, info in cleaner["kinds"].items():
		size = info["size"]

		if size > 0:
			response["garbage"].append({
				"name" : Klanguage().to_ts(info["name"]),
				"size" :  info["size"]
			})

def run(payload, socket):
	response = {
		"cmd_id" : "1008",
		"session_id" : payload["args"]["session_id"],
		"system_info" : [],
		"usage" : {
			"cpu" : [],
			"memory" : 0,
			"disk" : {
				"read" : [],
				"write" : []
			},
			"network" : {
				"tx" : [],
				"rx" : []
			}
		},
		"disk" : {},
		"ram" : {
			"total" : 0,
			"used" : 0
		},
		"garbage" : [],
		"error" : ""
	}

	get_system_info(response)
	get_mem_disk_info(response)
	get_garbage(response)

	monitor_second = Kdatabase().get_monitor_second()

	response["usage"]["cpu"] = common.extend_at_front(monitor_second["cpu"], 71, 0)
	try:
		response["usage"]["memory"] = monitor_second["memory"][-1]
	except:
		response["usage"]["memory"] = 0.0
	response["usage"]["disk"]["read"] = common.extend_at_front(monitor_second["disk_io"]["read"], 71, 0)
	response["usage"]["disk"]["write"] = common.extend_at_front(monitor_second["disk_io"]["write"], 71, 0)
	response["usage"]["network"]["tx"] = common.extend_at_front(monitor_second["net_io"]["tx"], 71, 0)
	response["usage"]["network"]["rx"] = common.extend_at_front(monitor_second["net_io"]["rx"], 71, 0)

	socket.response(response)
