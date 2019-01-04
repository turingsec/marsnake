from utils import common, time_op
from datetime import timedelta
from datetime import datetime
from core.db import Kdatabase
from core.logger import Klogger
from core.event import Kevent
import psutil, time

RECORD_INTERVAL = 60

CPU_WARNING_THRESHOLD = 80.0
MEM_WARNING_THRESHOLD = 80.0
WARNING_START_THRESHOLD = 5	# * RECORD_INTERVAL
WARNING_STOP_THRESHOLD = 3	# * RECORD_INTERVAL

def upgrade_warnings_info(monitor, monitor_warnings):
	now_time = monitor["times"][-1]

	if monitor["cpu"][-1] >= CPU_WARNING_THRESHOLD:
		if now_time - monitor_warnings["cpu"]["end_time"] > WARNING_STOP_THRESHOLD * RECORD_INTERVAL:
			monitor_warnings["cpu"]["start_time"] = now_time
			monitor_warnings["cpu"]["end_time"] = now_time
			monitor_warnings["cpu"]["percent"] = monitor["cpu"][-1]
			monitor_warnings["cpu"]["percent_count"] = 1
			monitor_warnings["cpu"]["db"] = None

		else:
			cpu = monitor_warnings["cpu"]["percent"] * monitor_warnings["cpu"]["percent_count"] + monitor["cpu"][-1]
			monitor_warnings["cpu"]["end_time"] = now_time
			monitor_warnings["cpu"]["percent"] = round(cpu / (monitor_warnings["cpu"]["percent_count"] + 1), 2)
			monitor_warnings["cpu"]["percent_count"] += 1

			if monitor_warnings["cpu"]["end_time"] - monitor_warnings["cpu"]["start_time"] >= WARNING_START_THRESHOLD * RECORD_INTERVAL:
				if monitor_warnings["cpu"]["db"] == None:
					monitor_warnings["cpu"]["db"] = {
						"start_time": monitor_warnings["cpu"]["start_time"],
						"end_time": monitor_warnings["cpu"]["end_time"],
						"percent": monitor_warnings["cpu"]["percent"]
					}
					monitor["warnings"]["cpu"].append(monitor_warnings["cpu"]["db"])

				else:
					# modify monitor_warnings implicitly
					monitor_warnings["cpu"]["db"]["end_time"] = monitor_warnings["cpu"]["end_time"]
					monitor_warnings["cpu"]["db"]["percent"] = monitor_warnings["cpu"]["percent"]


	if monitor["memory"][-1] >= MEM_WARNING_THRESHOLD:
		if now_time - monitor_warnings["memory"]["end_time"] > WARNING_STOP_THRESHOLD * RECORD_INTERVAL:
			monitor_warnings["memory"]["start_time"] = now_time
			monitor_warnings["memory"]["end_time"] = now_time
			monitor_warnings["memory"]["percent"] = monitor["memory"][-1]
			monitor_warnings["memory"]["percent_count"] = 1
			monitor_warnings["memory"]["db"] = None

		else:
			memory = monitor_warnings["memory"]["percent"] * monitor_warnings["memory"]["percent_count"] + monitor["memory"][-1]
			monitor_warnings["memory"]["end_time"] = now_time
			monitor_warnings["memory"]["percent"] = round(memory / (monitor_warnings["memory"]["percent_count"] + 1), 2)
			monitor_warnings["memory"]["percent_count"] += 1

			if monitor_warnings["memory"]["end_time"] - monitor_warnings["memory"]["start_time"] >= WARNING_START_THRESHOLD * RECORD_INTERVAL:
				if monitor_warnings["memory"]["db"] == None:
					monitor_warnings["memory"]["db"] = {
						"start_time": monitor_warnings["memory"]["start_time"],
						"end_time": monitor_warnings["memory"]["end_time"],
						"percent": monitor_warnings["memory"]["percent"]
					}
					monitor["warnings"]["memory"].append(monitor_warnings["memory"]["db"])

				else:
					# modify monitor_warnings implicitly
					monitor_warnings["memory"]["db"]["end_time"] = monitor_warnings["memory"]["end_time"]
					monitor_warnings["memory"]["db"]["percent"] = monitor_warnings["memory"]["percent"]


def upgrade_proc_status(monitor_second, monitor, procs, monitor_warnings):
	cpu = 0
	memory = 0
	net_io = {
		"tx" : 0,
		"rx" : 0
	}
	disk_io = {
		"read" : 0,
		"write" : 0
	}

	Klogger().info("minutes {}".format(monitor["minutes"]))

	last_min = time_op.get_last_min((monitor_second["start_record"] + timedelta(seconds = RECORD_INTERVAL)).timestamp())
	last_index = len(monitor_second["cpu"]) - 1

	for i in range(RECORD_INTERVAL):
		cpu += monitor_second["cpu"][last_index - i]
		memory += monitor_second["memory"][last_index - i]
		net_io["tx"] += monitor_second["net_io"]["tx"][last_index - i]
		net_io["rx"] += monitor_second["net_io"]["rx"][last_index - i]
		disk_io["read"] += monitor_second["disk_io"]["read"][last_index - i]
		disk_io["write"] += monitor_second["disk_io"]["write"][last_index - i]

	monitor["cpu"].append(round(cpu / RECORD_INTERVAL, 2))
	monitor["memory"].append(round(memory / RECORD_INTERVAL, 2))
	monitor["net_io"]["tx"].append(round(net_io["tx"] / RECORD_INTERVAL, 2))
	monitor["net_io"]["rx"].append(round(net_io["rx"] / RECORD_INTERVAL, 2))
	monitor["disk_io"]["read"].append(round(disk_io["read"] / RECORD_INTERVAL, 2))
	monitor["disk_io"]["write"].append(round(disk_io["write"] / RECORD_INTERVAL, 2))

	procs_result = {}
	for pid, proc in procs.items():
		if not pid in monitor_second["procs"]:
			cpu = proc["data"][0]
			memory = proc["data"][1]

			delta = int((monitor_second["start_record"] + timedelta(seconds = RECORD_INTERVAL)).timestamp()) - proc["beginat"]
			delta = delta if delta > 0 else 1
			io_read = proc["io_rb"] / delta
			io_write = proc["io_wb"] / delta

			procs_result[pid] = [proc["name"],
						proc["username"],
						round(cpu, 2),
						round(memory, 2),
						round(io_read, 2),
						round(io_write, 2),
						0,
						0]

		else:
			cpu = proc["data"][0]
			memory = (proc["data"][1] + monitor_second["procs"][pid]["data"][1]) / 2

			delta = RECORD_INTERVAL
			io_read = (proc["io_rb"] - monitor_second["procs"][pid]["io_rb"]) / delta
			io_write = (proc["io_wb"] - monitor_second["procs"][pid]["io_wb"]) / delta

			procs_result[pid] = [proc["name"],
						proc["username"],
						round(cpu, 2),
						round(memory, 2),
						round(io_read, 2),
						round(io_write, 2),
						0,
						0]

	# set new procs
	monitor_second["procs"] = procs

	monitor["times"].append(last_min)
	monitor["procs"].append(procs_result)
	monitor["minutes"] += 1

	if len(monitor["cpu"]) > 7 * 24 * 60:
		pop_status(monitor)

		del monitor["times"][0]
		del monitor["procs"][0]
		monitor["minutes"] -= 1

	upgrade_warnings_info(monitor, monitor_warnings)
	Kdatabase().dump("monitor")

def pop_status(status):
	del status["cpu"][0]
	del status["memory"][0]
	del status["net_io"]["tx"][0]
	del status["net_io"]["rx"][0]
	del status["disk_io"]["read"][0]
	del status["disk_io"]["write"][0]

def run(payload, socket):
	monitor = Kdatabase().get_obj("monitor")
	monitor_second = Kdatabase().get_monitor_second()
	monitor_warnings = {
		"cpu": {
			"start_time": 0,
			"end_time": 0,
			"percent": 0.0,
			"percent_count": 0,
			"db": None
		},
		"memory": {
			"start_time": 0,
			"end_time": 0,
			"percent": 0.0,
			"percent_count": 0,
			"db": None
		}
	}
	counters_ts = 0

	while True:
		if Kevent().is_terminate():
			print("resource thread terminate")
			break

		if not counters_ts:
			psutil.cpu_percent()
			disk_counters = psutil.disk_io_counters()
			net_counters = psutil.net_io_counters()
			counters_ts = datetime.now()

			time.sleep(1)
			continue

		#update counters
		now = datetime.now()
		interval = (now - counters_ts).total_seconds()
		counters_ts = now

		if interval > 15.0:
			Kdatabase().reset_monitor_second()
			monitor_second = Kdatabase().get_monitor_second()
			counters_ts = 0
			continue

		#calculate
		net = psutil.net_io_counters()
		tx_bytes = (net.bytes_sent - net_counters.bytes_sent) / interval
		rx_bytes = (net.bytes_recv - net_counters.bytes_recv) / interval
		net_counters = net

		disk = psutil.disk_io_counters()
		dru = (disk.read_bytes - disk_counters.read_bytes) / interval
		dwu = (disk.write_bytes - disk_counters.write_bytes) / interval
		disk_counters = disk

		monitor_second["cpu"].append(psutil.cpu_percent())
		monitor_second["memory"].append(psutil.virtual_memory()[2])
		monitor_second["net_io"]["tx"].append(tx_bytes)
		monitor_second["net_io"]["rx"].append(rx_bytes)
		monitor_second["disk_io"]["read"].append(dru)
		monitor_second["disk_io"]["write"].append(dwu)
		if not "start_record" in monitor_second or not monitor_second["start_record"]:
			monitor_second["start_record"] = now
			for proc in psutil.process_iter():
				try:
					proc.cpu_percent()
				except:
					pass

		if now > monitor_second["start_record"] + timedelta(seconds = RECORD_INTERVAL):
			procs = {}
			for proc in psutil.process_iter():
				try:
					if common.is_kernel_thread(proc):
						continue

					pid = proc.pid

					username = "unknown"
					status = "unknown"
					beginat = int(time.time())
					name = "unknown"
					proc_read_bytes = 0
					proc_write_bytes = 0
					cpu_percent = 0.0
					memory_percent = 0.0
					thread_num = 0
					fds_num = 0

					with proc.oneshot():
						try:
							username = proc.username()
							status = proc.status()
							beginat = int(proc.create_time())
						except:
							continue

						try:
							cmdline = proc.cmdline()
							exe = proc.exe()

							if exe:
								cmdline[0] = exe

							name = " ".join(cmdline[:3])
						except:
							try:
								name = proc.name()
							except:
								continue

						try:
							io = proc.io_counters()

							proc_read_bytes = io[2]
							proc_write_bytes = io[3]
						except:
							pass

						try:
							cpu_percent = proc.cpu_percent()
							memory_percent = proc.memory_percent()
						except:
							pass

						try:
							thread_num = proc.num_threads()
							if common.is_linux():
								fds_num = proc.num_fds()
							elif common.is_windows():
								fds_num = proc.num_handles()
						except:
							pass

					procs[pid] = {
						"name" : name,
						"username" : username,
						"io_rb": proc_read_bytes,
						"io_wb": proc_write_bytes,
						"beginat" : beginat,
						"status" : status,
						"fd" : fds_num,
						"thread" : thread_num,
						"data" : (cpu_percent, memory_percent)
					}

				except Exception as e:
					#print("pid : {} name : {} error : {}".format(pid, name, str(e)))
					pass

			upgrade_proc_status(monitor_second, monitor, procs, monitor_warnings)

			monitor_second["start_record"] = monitor_second["start_record"] + timedelta(seconds = RECORD_INTERVAL)

		if len(monitor_second["cpu"]) > 120:
			pop_status(monitor_second)

		if interval >= 1:
			sleep = 1 - (interval - 1)

			if sleep < 0:
				sleep = 1
		else:
			sleep = 1

		time.sleep(sleep)
