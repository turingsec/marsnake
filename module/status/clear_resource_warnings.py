from utils import common
from core.db import Kdatabase

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	monitor = Kdatabase().get_obj("monitor")
	warnings = monitor["warnings"]

	kind = payload["args"]["kind"]
	start_time = payload["args"]["start_time"]

	if start_time == 0:
		warnings[kind] = []
	else:
		for each in range(len(warnings[kind])):
			if warnings[kind][each]["start_time"] == start_time:
				del warnings[kind][each]
				break

	response["start_time"] = start_time
	socket.response(response)
