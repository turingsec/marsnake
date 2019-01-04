from utils import common, time_op
from core.db import Kdatabase
from core.language import Klanguage

def translate(timeline):
	ret = []

	for i in range(len(timeline)):
		ret.append({
			"kind" : timeline[i]["kind"],
			"extra" : timeline[i]["extra"],
			"des" : Klanguage().decode_ts(timeline[i]["des"]),
			"time" : timeline[i]["time"],
			"title" : Klanguage().decode_ts(timeline[i]["title"]),
			"distro" : timeline[i]["distro"],
			"hostname" : timeline[i]["hostname"]
		})

	return ret

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	ueba = Kdatabase().get_obj("ueba")

	for key, story in ueba["storys"].items():
		if key == payload["args"]["key"]:
			response["ueba"] = {
				"key" : key,
				"description" : Klanguage().decode_ts(story["description"]),
				"root_cause" : Klanguage().decode_ts(story["root_cause"]),
				"suggestion" : Klanguage().decode_ts(story["suggestion"]),
				"timeline" : translate(story["timeline"]),
				"unread" : story["unread"],
				"resolved" : story["resolved"],
				"resolved_ts" : story["resolved_ts"]
			}

			story["unread"] = False
			story["read_ts"] = time_op.now()
			Kdatabase().dump("ueba")

			break

	socket.response(response)
