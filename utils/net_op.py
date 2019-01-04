from utils import common
import struct, socket, psutil, ipaddress

def create_http_request(addr, method, url, data, header = None):
	host, port = addr.rsplit(":", 1)

	if common.is_python2x():
		import httplib

		if port == "443":
			conn = httplib.HTTPSConnection(host, port, timeout = 5)
		else:
			conn = httplib.HTTPConnection(host, port, timeout = 5)
	else:
		from http.client import HTTPConnection
		from http.client import HTTPSConnection

		if port == "443":
			conn = HTTPSConnection(host, port, timeout = 5)
		else:
			conn = HTTPConnection(host, port, timeout = 5)
	
	if not header:
		header = {"Content-type": "application/octet-stream", "Accept": "text/plain"}

	response_data = None
	status = 404

	try:
		conn.request(method, url, data, header)

		res = conn.getresponse()
		status = res.status

		if status == 200:
			response_data = res.read()
	except Exception as e:
		pass
	finally:
		conn.close()

	return status, response_data

def is_private_ip(ip):
	return ipaddress.ip_address(ip).is_private

def get_listening_port():
	listen_port = []
	external = {}

	for proc in psutil.process_iter():
		try:
			connections = proc.connections(kind = "inet")
		except Exception as e:
			connections = []

		if connections:
			try:
				exe = common.decode2utf8(proc.exe())
			except Exception as e:
				exe = "Unknown"
				
			for conn in connections:
				if conn.laddr:
					local_port = conn.laddr[1]

					if conn.status == "LISTEN":
						listen_port.append(local_port)

				if conn.raddr:
					remote_ip = conn.raddr[0]

					if is_private_ip(remote_ip):
						continue

					external[remote_ip] = {
						"port": local_port,
						"exe": exe
					}

	listen_port = list(set(listen_port))

	return listen_port, external
