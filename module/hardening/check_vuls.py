from core.db import Kdatabase
from utils import time_op

def run(payload, socket):
	response = {
		'cmd_id' : payload['cmd_id'],
		"session_id" : payload["args"]["session_id"],
		"items" : None,
		"lasttime" : 0,
		'error' : ""
	}

	vuls = Kdatabase().get_obj("vuls")
	last_8week_ts = time_op.get_last_nmonday_ts(8)
	history = list(range(8))

	for i in range(len(last_8week_ts)):
		history[i] = {
			"time" : last_8week_ts[i],
			"cves" : []
		}

	for record in vuls["record"]:
		for value in history:
			if record["time"] >= value["time"]:
				value["cves"].extend(record["cves"])
				value["cves"] = list(set(value["cves"]))
				break

	history = sorted(history, key = lambda t : t["time"])

	response["items"] = vuls["items"]
	response["records"] = history
	response["lasttime"] = vuls["lasttime"]

	socket.response(response)
