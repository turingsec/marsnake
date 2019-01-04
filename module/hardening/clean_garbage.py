from core.db import Kdatabase
from core.cleaner import Kcleaner
from core.language import Klanguage
from core.profile_reader import KProfile
from utils import common
import shutil, time, os

def clean(items, socket, session_id):
	response = {
		"cmd_id" : "1044",
		"session_id" : session_id,
		"kind" : None,
		"size" : 0,
		"id" : None
	}

	total_size = 0
	total_failed = 0

	if len(items) > 0:
		cleaner = Kdatabase().get_obj("cleaner")

		for i in items:
			for kind, info in cleaner["kinds"].items():
				if i in list(info["items"].keys()):
					ret = Kcleaner().clean_option(info, i, cleaner["record"])
					total_size += ret[0]
					total_failed += ret[1]

					if ret[1] == 0:
						response["kind"] = kind
						response["size"] = info["size"]
						response["id"] = i

						socket.response(response)

					break

		if total_size > 0:
			Kdatabase().dump("cleaner")

	return total_failed, total_size

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	if payload["args"]["user_id"] != KProfile().read_key("username"):
		response["error"] = Klanguage().to_ts(4007)
		socket.response(response)
		return

	with Kcleaner().get_lock():
		total_failed, total_size = clean(payload["args"]["items"], socket, payload["args"]["session_id"])

	if total_failed + total_size > 0:
		prompt = "{} {}".format(common.size_human_readable(total_size), Klanguage().to_ts(1830))
		'''
		if total_failed > 0:
			response["error"] = "{}, {}".format(prompt, Klanguage().to_ts(1831))
		else:
			response["prompt"] = prompt
		'''
		response["prompt"] = prompt
	else:
		response["error"] = Klanguage().to_ts(4006)

	socket.response(response)
