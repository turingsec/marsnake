from utils import file_op, common
from datetime import datetime
from core.language import Klanguage
import psutil, sys, os

def cpu_cache():
	path = "/sys/devices/system/cpu/cpu0/cache"
	cache = {
		"L1Cache" : 0,
		"L2Cache" : 0,
		"L3Cache" : 0
	}

	if os.path.exists(path):
		for i in range(4):
			index_dir = os.path.join(path, "index{}".format(i))
			size = file_op.cat(os.path.join(index_dir, "size"), "r")
			level = file_op.cat(os.path.join(index_dir, "level"), "r")

			if size and level:
				key = "L{}Cache".format(level.strip("\n"))

				if key in cache:
					cache[key] = size.strip("\n")

	return cache

def cpu_status(response):
	virtualization = "None"
	cpu_mhz = 0
	num_threads = 0
	num_process = 0
	num_fds = 0

	if os.path.exists("/proc/cpuinfo"):
		with open("/proc/cpuinfo") as f:
			data = f.readlines()

			for line in data:
				_tmp = line.split(":")
				if len(_tmp) != 2:
					continue

				item, value = (_tmp[0].strip(), _tmp[1].strip())

				if item == "cpu MHz":
					try:
						cpu_mhz = int(float(value))
					except:
						pass

				elif item == "flags":
					if "vmx" in value:
						virtualization = "Intel VT-x"
					if "svm" in value:
						virtualization = "AMD-V"

	for proc in psutil.process_iter():

		try:
			num_threads += proc.num_threads()
			if common.is_linux():
				num_fds += proc.num_fds()
			elif common.is_windows():
				num_fds += proc.num_handles()
		except Exception as e:
			pass

		num_process += 1

	#cache = cpu_cache()
	freq = psutil.cpu_freq()
	freq = [cpu_mhz, 0, cpu_mhz] if (not freq or len(freq) < 3) else freq
	
	response["cpu"].append([Klanguage().to_ts(1505), "{}%".format(psutil.cpu_percent(interval = 0.2))])
	response["cpu"].append([Klanguage().to_ts(1511), num_process])
	response["cpu"].append([Klanguage().to_ts(1508), psutil.cpu_count(logical = False)])
	response["cpu"].append([Klanguage().to_ts(1514), "{} Mhz".format(freq[0])])

	response["cpu"].append([Klanguage().to_ts(1506), virtualization])
	response["cpu"].append([Klanguage().to_ts(1509), num_threads])
	response["cpu"].append([Klanguage().to_ts(1512), psutil.cpu_count(logical = True)])
	response["cpu"].append([Klanguage().to_ts(1515), "{} Mhz".format(freq[1])])

	response["cpu"].append([Klanguage().to_ts(1507), sys.byteorder])
	response["cpu"].append([Klanguage().to_ts(1510), num_fds])
	response["cpu"].append([Klanguage().to_ts(1513), str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())).split(".")[0]])
	response["cpu"].append([Klanguage().to_ts(1516), "{} Mhz".format(freq[2])])

def run(payload, socket):

	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"cpu" : [],
		"error" : ""
	}

	cpu_status(response)

	socket.response(response)
