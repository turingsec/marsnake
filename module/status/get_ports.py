from utils import common
from core.db import Kdatabase

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	fingerprint = Kdatabase().get_obj("fingerprint")

	response["current"] = fingerprint["port"]["current"]
	response["change"] = fingerprint["port"]["change"]
	response["lasttime"] = fingerprint["port"]["lasttime"]

	socket.response(response)
