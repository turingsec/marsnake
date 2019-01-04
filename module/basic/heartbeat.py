from core.computer_score import KScore
from core.db import Kdatabase

def run(payload, socket):
	warning, score = KScore().get_status()
	fingerprint = Kdatabase().get_obj('fingerprint')

	response = {
		"cmd_id" : payload["cmd_id"],
		"warning" : warning,
		"score" : score,
		"open_ports" : len(fingerprint["port"]["current"]),
		"accounts" : len(fingerprint["account"]["current"])
	}

	socket.response(response)
