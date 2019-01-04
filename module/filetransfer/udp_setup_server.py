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
	
	response_2 = {
		"cmd_id" : "1063",
		"pair_id" : payload["args"]["pair_id"],
		"error" : "data error"
	}
	
	# Create a UDP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	
	# Bind the socket to the port
	sock.bind(('', 0))
	sock.settimeout(5)
	
	random_code = Krandom().purely(32)
	
	response["random_code"] = random_code
	response["port"] = sock.getsockname()[1]
	response["ip"] = common.get_ip_gateway()
	
	socket.response(response)
	
	try:
		data, client = sock.recvfrom(1024)
		
		if data != random_code:
			socket.response(response_2)
			return
			
		sock.sendto(payload["args"]["server2client_key"], client)
		
	except socket.timeout as e:
		socket.response(response_2)
		
	sock.close()