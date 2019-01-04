from utils import common, file_op, net_op
import psutil, os

def create_proc_info(pid):
	proc_info = {
		"pid" : pid,
		"signature" : "Unknown",
		"hash" : "Unknown",
		"user" : "Unknown",
		"exe" : "Unknown",
		"create_time" : "Unknown",
		"end_time" : "Unknown",
		"memory_maps" : [],
		"open_files" : [],
		"incomming" : [],
		"outgoing" : [],
		"children" : []
	}

	try:
		proc = psutil.Process(pid)

		proc_info["create_time"] = int(proc.create_time())
		proc_info["user"] = proc.username()
		
		try:
			proc_info["exe"] = common.decode2utf8(proc.cmdline()[0])
			proc_info["exe"] = common.decode2utf8(proc.exe())
		except Exception as e:
			pass

		if os.path.exists(proc_info["exe"]):
			proc_info["hash"] = file_op.md5(proc_info["exe"])

		memory_maps = proc.memory_maps()

		for region in memory_maps:
			proc_info["memory_maps"].append([
				region[0],
				region[1]
			])

		files = proc.open_files()

		for file in files:
			path = file[0]

			if os.path.exists(path):
				_stat = os.lstat(path)

				proc_info["open_files"].append([
					path,
					_stat.st_size,
					int(_stat.st_mtime)
				])

		listen_port, external_ip = net_op.get_listening_port()
		connections = proc.connections(kind = "inet")

		for conn in connections:
			fd, family, _type, laddr, raddr, status = conn

			local = "{}:{}".format(laddr[0], laddr[1])

			if _type == 1:
				_type = "TCP"
			elif _type == 2:
				_type = "UDP"

			if family == 2:
				family = "AF_INET"
			elif family == 10:
				family = "AF_INET6"
			else:
				family = "AF_UNIX"

			if len(raddr) == 0:
				remote = ""
			else:
				remote = "{}:{}".format(raddr[0], raddr[1])

			if laddr[0] in listen_port:
				proc_info["incomming"].append([
					family,
					_type,
					local,
					remote,
					status
				])
			else:
				proc_info["outgoing"].append([
					family,
					_type,
					local,
					remote,
					status
				])

		def find_child(parent_proc, info):
			children = parent_proc.children()

			for child in children:
				execute = common.decode2utf8(child.cmdline()[0])

				try:
					execute = common.decode2utf8(child.exe())
				except Exception as e:
					pass

				info.append({
					"pid" : child.pid,
					"name" : execute,
					"create" : int(child.create_time()),
					"children" : []
				})

				find_child(child, info[-1]["children"])

		find_child(proc, proc_info["children"])

	except Exception as e:
		pass

	return proc_info
