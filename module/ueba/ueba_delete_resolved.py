from core.db import Kdatabase

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"key" : None,
		"error" : ""
	}

	unlucky = payload["args"]["key"]
	ueba = Kdatabase().get_obj("ueba")

	for key, story in ueba["storys"].items():
		if story["resolved"] and key == unlucky:
			del ueba["storys"][unlucky]
			response["key"] = unlucky
			Kdatabase().dump("ueba")

			break

	socket.response(response)
