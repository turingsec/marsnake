from utils.randomize import Krandom
from utils import common
import socket
import sys

def run(payload, socket):
	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"pair_id" : payload["args"]["pair_id"],
		"error" : ""
	}
	
	# Create a UDP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.settimeout(5)
	
	# Bind the socket to the port
	server_address = (payload["args"]["ip"], payload["args"]["port"])
	message = payload["args"]["random_code"]
	
	sock.sendto(message, server_address)
	
	try:
		data, server = sock.recvfrom(1024)
		
		if data != payload["args"]["server2client_key"]:
			response["error"] = "data error"
			socket.response(response)
			return
			
		#UDP connection established
		socket.response(response)
		
		path = payload["args"]["path"]
		
		
	except socket.timeout as e:
		response["error"] = "data error"
		socket.response(response)

	sock.close()