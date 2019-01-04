from core.db import Kdatabase
from utils import time_op

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	ueba = Kdatabase().get_obj("ueba")
	marked = payload["args"]["marked"]

	for key, story in ueba["storys"].items():
		if key == payload["args"]["key"]:

			if marked:
				story["resolved"] = True
				story["resolved_ts"] = time_op.now()

				print("marked key:" + key)
			else:
				story["resolved"] = False
				story["resolved_ts"] = -1
				print("unmarked key:" + key)

			response["resolved"] = story["resolved"]
			response["resolved_ts"] = story["resolved_ts"]

			Kdatabase().dump("ueba")

			break
			
	socket.response(response)
