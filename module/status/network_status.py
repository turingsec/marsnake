import psutil, socket
from utils import common

def network_status(response):
	interfaces = psutil.net_if_addrs()

	for name, addrs in interfaces.items():
		key = common.decode2utf8(name) if common.is_python2x() else name
		status = {
			"ipv4" : "-",
			"ipv6" : "-",
			"mac" : "-"
		}
		
		for addr in addrs:
			if addr.family == socket.AF_INET:
				status["ipv4"] = addr.address

			if addr.family == socket.AF_INET6:
				status["ipv6"] = addr.address

			if addr.family == psutil.AF_LINK:
				status["mac"] = addr.address

		response["nic"][key] = status

def run(payload, socket):

	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"nic" : {},
		"error" : ""
	}

	network_status(response)

	socket.response(response)
