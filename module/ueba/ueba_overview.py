from utils import common, net_op, time_op
from core.db import Kdatabase
from core.ueba import macro
import json

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"error" : ""
	}

	ueba = Kdatabase().get_obj("ueba")
	kind = [0 for x in range(macro.STORY_KIND["MAX"])]
	last_7day_ts = time_op.get_last_nday_ts(7)
	history = list(range(7))
	score = 0
	risk_level = macro.RISK_LEVEL["NORMAL"]

	for i in range(len(last_7day_ts)):
		history[i] = {
			"ts" : last_7day_ts[i],
			"num" : 0
		}

	for key, story in ueba["storys"].items():
		for value in history:
			if story["ts"] >= value["ts"]:
				value["num"] += 1
				break

		if not story["resolved"]:
			kind[story["kind"]] += 1
			score += story["score"]

	if (score > 0 and score <= 40):
		risk_level = macro.RISK_LEVEL["LOW_RISK"]
	elif (score > 40 and score <= 99):
		risk_level = macro.RISK_LEVEL["HIGH_RISK"]
	elif score >= 100:
		risk_level = macro.RISK_LEVEL["VULNERABLE"]

	listen_port, external_ip = net_op.get_listening_port()
	incoming = []
	outgoing = []

	for remote_ip, local in external_ip.items():
		if local["port"] in listen_port:
			incoming.append({
				"remote_ip": remote_ip,
				"exe": local["exe"]
			})
		else:
			outgoing.append({
				"remote_ip": remote_ip,
				"exe": local["exe"]
			})
			
	response["incoming"] = incoming
	response["outgoing"] = outgoing
	response["kind"] = kind
	response["history"] = history
	response["risk_level"] = risk_level
	response["2018061418"] = True

	socket.response(response)
