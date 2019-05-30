def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	if "6666" != payload["args"]["code"]:
		response["error"] = "wrong code"
	
	socket.response(response)
