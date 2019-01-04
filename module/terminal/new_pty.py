from core.ptys import Kptys

def run(payload, socket):
	args = payload["args"]
	data = args["data"]

	if len(data) == 5 and data[0] == "new_terminal":
		Kptys().new_terminal(args["session_id"], socket)
		Kptys().resize(data[1], data[2], data[3], data[4])
