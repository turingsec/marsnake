from utils import common
from core.db import Kdatabase

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	fingerprint = Kdatabase().get_obj("fingerprint")
	change = fingerprint["port"]["change"]
	change_id = payload["args"]["change_id"]

	if change_id in change:
		del change[change_id]
		response["change_id"] = change_id
		Kdatabase().dump("fingerprint")
	else:
		response["error"] = "Change ID Not Found"

	socket.response(response)
