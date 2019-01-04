from utils import lib, common
from core.language import Klanguage
from core.profile_reader import KProfile

def op_service(name, op, response):
	if common.is_linux():
		if common.check_programs_installed("systemctl"):
			#data, success, retcode = common.exec_command(['systemctl', 'is-enabled', name])

			if op == 0:
				data, success, retcode = common.exec_command(['systemctl', 'enable', name, "--no-ask-password"])

				if success:
					response["status"] = "enabled"
				else:
					response["error"] = "{} code : {}".format(data, retcode)

			else:
				data, success, retcode = common.exec_command(['systemctl', 'disable', name, "--no-ask-password"])

				if success:
					response["status"] = "disabled"
				else:
					response["error"] = "{} code : {}".format(data, retcode)
		else:
			response["error"] = Klanguage().to_ts(4003)

def run(payload, socket):
	response = {
		'cmd_id' : payload['cmd_id'],
		"session_id" : payload["args"]["session_id"],
		'status' : "",
		'error' : ""
	}

	if payload["args"]["user_id"] != KProfile().read_key("username"):
		response["error"] = Klanguage().to_ts(4007)
		socket.response(response)
		return

	if lib.check_root():
		op_service(payload["args"]["name"], payload["args"]["op"], response)
	else:
		response["error"] = Klanguage().to_ts(4002)

	socket.response(response)
