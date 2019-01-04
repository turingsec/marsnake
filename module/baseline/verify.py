from core.db import Kdatabase
from core.baseline import Kbaseline
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
	verified_1 = 0
	verified_2 = 0

	for i in baseline["risks"]:
		if baseline["risks"][i]["stage"] == macro.BASELINE_STAGE["VERIFIED"]:
			verified_1 += 1

	for i in risk_id:
		Kbaseline().verify_all(i)

	for i in baseline["risks"]:
		if baseline["risks"][i]["stage"] == macro.BASELINE_STAGE["VERIFIED"]:
			verified_2 += 1

	if verified_2 > verified_1:
		pass
	else:
		response["error"] = "No baseline verified"

	Kdatabase().dump('baseline')

	socket.response(response)
