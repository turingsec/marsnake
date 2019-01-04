from utils import common
from core.icloud import Kicloud
from utils.randomize import Krandom

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"pair_id" : payload["args"]["pair_id"],
		"error" : ""
	}

	random_code = Krandom().purely(32)
	response["random_code"] = random_code
	socket.response(response)

	Kicloud().punch_as_server(payload["args"]["pair_id"], 
		payload["args"]["target_ip"],
		payload["args"]["target_port"],
		random_code, socket)
