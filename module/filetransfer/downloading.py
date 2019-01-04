from core.icloud import Kicloud

def run(payload, socket):
	Kicloud().downloading(payload["args"]["identity"],
						socket,
						payload["args"]["session_id"])
