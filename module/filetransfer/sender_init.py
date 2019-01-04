import os, stat
from utils import file_op

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"pair_id" : payload["args"]["pair_id"],
		"size" : -1,
		"error" : ""
	}
	
	path = payload["args"]["path"];
	
	if os.path.exists(path):
		if os.path.isdir(path):
			response["size"] = file_op.getsizedir(path)
		else:
			response["size"] = file_op.getsize(path)
			
		socket.response(response)