from core.db import Kdatabase
from core.baseline import macro
from utils import time_op

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	baseline = Kdatabase().get_obj("baseline")
	risk_id = payload["args"]["risk_id"]

	if len(risk_id) > 0:
		for i in risk_id:
			baseline["risks"][i]["stage"] = macro.BASELINE_STAGE["IGNORED"]
			baseline["risks"][i]["handle_ts"] = time_op.now()

		Kdatabase().dump('baseline')
	else:
		response["error"] = "Nothing to ignore"
		
	socket.response(response)
