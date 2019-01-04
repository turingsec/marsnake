from core.db import Kdatabase
from core.language import Klanguage
from utils import time_op

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"items" : {},
		"error" : ""
	}

	baseline = Kdatabase().get_obj("baseline")

	for i in baseline["risks"]:
		response["items"][i] = baseline["risks"][i]

	socket.response(response)
