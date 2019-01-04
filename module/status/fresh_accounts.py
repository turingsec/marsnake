from utils import common
from core.db import Kdatabase
from core.fingerprint import Kfingerprint

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	Kfingerprint().record_account()
	
	fingerprint = Kdatabase().get_obj("fingerprint")

	response["current"] = fingerprint["account"]["current"]
	response["change"] = fingerprint["account"]["change"]
	response["lasttime"] = fingerprint["account"]["lasttime"]

	socket.response(response)
