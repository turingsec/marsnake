import os, time, psutil
from utils import lib, common
from core.db import Kdatabase

def enum_process_by_users():
	process_by_user = {}

	# use monitor_second directly may be dangerous since there is no lock
	monitor_second = Kdatabase().get_monitor_second().copy()

	for proc in psutil.process_iter():
		try:
			if common.is_kernel_thread(proc):
				continue

			pid = proc.pid

			if pid in monitor_second["procs"]:
				saved_proc = monitor_second["procs"][pid]

				username = saved_proc["username"]

				name = saved_proc["name"]
				cpu = saved_proc["data"][0]
				memory = saved_proc["data"][1]
				threads = saved_proc["thread"]
				fds = saved_proc["fd"]
				delta = int(time.time()) - saved_proc["beginat"]
				delta = delta if delta > 0 else 1
				io_read = saved_proc["io_rb"]
				io_write = saved_proc["io_wb"]
				status = saved_proc["status"]

				with proc.oneshot():
					try:
						memory = proc.memory_percent()
					except:
						pass

					try:
						threads = proc.num_threads()
						if common.is_linux():
							fds = proc.num_fds()
						elif common.is_windows():
							fds = proc.num_handles()
					except:
						pass

					try:
						if "start_record" in monitor_second and monitor_second["start_record"]:
							_delta = int(time.time()) - int(monitor_second["start_record"].timestamp())
							if _delta <= 0:
								_delta = 1

							_io = proc.io_counters()
							_io_read = _io[2]
							_io_write = _io[3]

							delta = _delta
							io_read = _io_read - saved_proc["io_rb"]
							io_write = _io_write - saved_proc["io_wb"]
					except:
						pass

					try:
						status = proc.status()
					except:
						pass

			else:
				username = "unknown"

				name = "unknown"
				cpu = 0.0
				memory = 0.0
				threads = 0
				fds = 0
				delta = 1
				io_read = 0.0
				io_write = 0.0
				status = "unknown"

				with proc.oneshot():
					try:
						username = proc.username()
						status = proc.status()
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
						memory = proc.memory_percent()
					except:
						pass

					try:
						threads = proc.num_threads()
						if common.is_linux():
							fds = proc.num_fds()
						elif common.is_windows():
							fds = proc.num_handles()
					except:
						pass

					try:
						_delta = int(time.time()) - int(proc.create_time())
						if _delta <= 0:
							_delta = 1

						_io = proc.io_counters()
						_io_read = _io[2]
						_io_write = _io[3]

						delta = _delta
						io_read = _io_read
						io_write = _io_write
					except:
						pass


			if not username in process_by_user:
				process_by_user[username] = {
					"username": username,
					"cpu": 0.0,
					"memory": 0.0,
					"fds": 0,
					"threads": 0,
					"disk_io": {
						"read": 0.0,
						"write": 0.0
					},
					"process": []
				}

			process_by_user[username]["cpu"] += cpu
			process_by_user[username]["memory"] += memory
			process_by_user[username]["fds"] += fds
			process_by_user[username]["threads"] += threads
			process_by_user[username]["disk_io"]["read"] += io_read / delta
			process_by_user[username]["disk_io"]["write"] += io_write / delta
			process_by_user[username]["process"].append({
				"pid": pid,
				"name": name,
				"cpu": round(cpu, 2),
				"memory": round(memory, 2),
				"threads": threads,
				"fds": fds,
				"disk_io": {
					"read": round((io_read / delta), 2),
					"write": round((io_write / delta), 2)
				},
				"status": status
			})

		except Exception as e:
			pass

	for each in process_by_user.values():
		each["cpu"] = round(each["cpu"], 2)
		each["memory"] = round(each["memory"], 2)
		each["disk_io"]["read"] = round(each["disk_io"]["read"], 2)
		each["disk_io"]["write"] = round(each["disk_io"]["write"], 2)

	return process_by_user

def list_process_by_users():
	process_by_users = enum_process_by_users()

	if common.is_linux():

		result = []

		useradd_users = lib.find_useradd_users()

		import pwd
		pwall_users = [ x[0] for x in pwd.getpwall() ]

		users = [ x for x in useradd_users if x in pwall_users ]

		if "root" in process_by_users:
			users.insert(0, "root")

		for user in users:
			if user in process_by_users:
				result.append(process_by_users[user])
				del process_by_users[user]

		if not process_by_users:
			return result

		non_useradd_users = {
			"username": "non-useradd-users",
			"cpu": 0.0,
			"memory": 0.0,
			"fds": 0,
			"threads": 0,
			"disk_io": {
				"read": 0.0,
				"write": 0.0
			},
			"process": []
		}

		for each in process_by_users.values():
			non_useradd_users["cpu"] += each["cpu"]
			non_useradd_users["memory"] += each["memory"]
			non_useradd_users["fds"] += each["fds"]
			non_useradd_users["threads"] += each["threads"]
			non_useradd_users["disk_io"]["read"] += each["disk_io"]["read"]
			non_useradd_users["disk_io"]["write"] += each["disk_io"]["write"]
			non_useradd_users["process"] += each["process"]

		non_useradd_users["cpu"] = round(non_useradd_users["cpu"], 2)
		non_useradd_users["memory"] = round(non_useradd_users["memory"], 2)
		non_useradd_users["disk_io"]["read"] = round(non_useradd_users["disk_io"]["read"], 2)
		non_useradd_users["disk_io"]["write"] = round(non_useradd_users["disk_io"]["write"], 2)

		result.append(non_useradd_users)

		return result

	elif common.is_windows():

		for each in process_by_users.values():
			if '\\' in each["username"]:
				each["username"] = each["username"].split("\\")[1]

		return list(process_by_users.values())

	else:
		return list(process_by_users.values())

def run(payload, socket):
	
	users = list_process_by_users()

	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"users" : users,
		"error" : ""
	}

	socket.response(response)
