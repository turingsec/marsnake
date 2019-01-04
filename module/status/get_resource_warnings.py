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
	
	if kind == "all":
		response["data"] = [warnings["cpu"], warnings["memory"], warnings["net_io"], warnings["disk_io"]]
	elif kind in warnings:
		response["data"] = warnings[kind]
	else:
		response["data"] = []

	socket.response(response)
