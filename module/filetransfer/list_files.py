from utils import common, time_op, file_op
import os
import stat

def list_item(path):
	try:
		_stat = os.lstat(path)

		if path.endswith(os.path.sep):
			path = path.rsplit(os.path.sep, 1)[0]

		name = os.path.basename(path)

		if stat.S_ISLNK(_stat.st_mode):
			try:
				name += ' -> ' + os.readlink(path)
			except:
				pass

		return {
			'name': common.decode2utf8(name),
			'type': file_op.identifytype(path),
			'size': common.size_human_readable(_stat.st_size),
			'ts': time_op.timestamp2string(int(_stat.st_mtime))
		}
	except Exception as e:
		return None

def ls(response, path):
	try:
		path = common.path_translate(path)

		for x in os.listdir(path):
			url = os.path.join(path, x)
			item = list_item(url)

			if item:
				if os.path.isfile(url):
					response["files"].append(item)

				if os.path.isdir(url):
					response["dirs"].append(item)

	except Exception as e:
		response["error"] = str(e)

	response["path"] = path

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"sep" : os.path.sep,
		"files" : [],
		"dirs" : [],
		"error" : ""
	}

	ls(response, payload["args"]["path"])

	socket.response(response)
