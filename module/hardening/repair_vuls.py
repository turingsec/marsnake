from core.db import Kdatabase
from core.vuls import Kvuls
from core.language import Klanguage
from core.profile_reader import KProfile
from utils import common, lib, time_op

def repair(package, socket, session_id):
	response = {
		"cmd_id" : "1052",
		"session_id" : session_id,
		"package" : package
	}

	ret = Kvuls().repair(package)

	if ret:
		return ret

	socket.response(response)

	return None

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"prompt" : "",
		"error" : ""
	}

	if payload["args"]["user_id"] != KProfile().read_key("username"):
		response["error"] = Klanguage().to_ts(4007)
		socket.response(response)
		return

	vuls = Kdatabase().get_obj("vuls")

	if common.is_program_running("apt-get") or common.is_program_running("yum"):
		response["error"] = Klanguage().to_ts(4005)
	else:
		if lib.check_root():
			with Kvuls().get_lock():
				repaired_count = 0
				failed_count = 0

				for package in payload["args"]["packages"]:
					if package in vuls["items"]:
						error = repair(package, socket, payload["args"]["session_id"])

						if not error:
							repaired_count += 1
						else:
							failed_count += 1
							print(__name__, error)

				if repaired_count > 0:
					Kdatabase().dump("vuls")
					response["prompt"] = "{} {}".format(repaired_count, Klanguage().to_ts(1198))

				if failed_count > 0:
					response["error"] = "{} {}".format(failed_count, Klanguage().to_ts(1199))
					del response["prompt"]

		else:
			response["error"] = Klanguage().to_ts(4002)

	last_8week_ts = time_op.get_last_nmonday_ts(8)
	history = list(range(8))

	for i in range(len(last_8week_ts)):
		history[i] = {
			"time" : last_8week_ts[i],
			"cves" : []
		}

	for record in vuls["record"]:
		for value in history:
			if record["time"] >= value["time"]:
				value["cves"].extend(record["cves"])
				value["cves"] = list(set(value["cves"]))
				break

	history = sorted(history, key = lambda t : t["time"])

	response["records"] = history
	socket.response(response)
