from core.db import Kdatabase
from core.language import Klanguage
from utils import time_op

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"items" : {},
		"lasttime" : 0,
		"error" : ""
	}

	cleaner = Kdatabase().get_obj("cleaner")

	for kind, info in cleaner["kinds"].items():
		values = []

		for key, array in info["items"].items():
			values.append([Klanguage().to_ts(array[0]), array[1], array[2], key])

		response["items"][kind] = {
			"name" : Klanguage().to_ts(info["name"]),
			"des" : Klanguage().to_ts(info["des"]),
			"size" : info["size"],
			"values" : values
		}

	last_8week_ts = time_op.get_last_nmonday_ts(8)
	history = list(range(8))

	for i in range(len(last_8week_ts)):
		history[i] = {
			"time" : last_8week_ts[i],
			"size" : 0
		 }

	for record in cleaner["record"]:
		for value in history:
			if record["time"] >= value["time"]:
				value["size"] += record["size"]
				break

	history = sorted(history, key = lambda t : t["time"])
	
	response["lasttime"] = cleaner["lasttime"]
	response["record"] = history

	socket.response(response)
