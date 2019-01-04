from utils import common
from core.db import Kdatabase
from core.ueba import macro
from core.language import Klanguage
import platform

def translate(introduction):
	ret = [
		introduction[0],
		introduction[1],
		""]

	ret[2] = Klanguage().decode_ts(introduction[2])

	return ret

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"check_resolved" : payload["args"]["check_resolved"],
		"error" : ""
	}

	ueba = Kdatabase().get_obj("ueba")
	kind = [{} for x in range(macro.STORY_KIND["MAX"])]
	check_resolved = payload["args"]["check_resolved"]

	for key, story in ueba["storys"].items():
		if check_resolved == story["resolved"]:
			resolved_ts = -1

			if story["resolved"]:
				resolved_ts = story["resolved_ts"]

			kind[story["kind"]][key] = {
				"distro" : common.get_distribution(),
				"hostname" : platform.node(),
				"icon" : story["icon"],
				"activities" : story["activities"],
				"introduction" : translate(story["introduction"]),
				"ts" : story["ts"],
				"resolved" : story["resolved"],
				"resolved_ts" : resolved_ts
			}

	response["kind"] = kind

	socket.response(response)
