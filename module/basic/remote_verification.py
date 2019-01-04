from core.profile_reader import KProfile

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	settings = KProfile().read_key("settings")

	if settings["remote_support"]["code"] != payload["args"]["code"]:
		response["error"] = "wrong code"

	socket.response(response)
