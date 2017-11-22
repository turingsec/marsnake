# -*- coding: utf-8 -*-
from utils.singleton import singleton

@singleton
class Kharden():

	VULSCAN = 0
	NETWORK = 1
	WEAKPWD = 2
	KERNEL = 3
	AUTHENTICATION = 4
	BOOT = 5
	WEBSCAN = 6

	def __init__(self):
		pass

	#@socket
	#@session_id - 
	#@module_id - module id of hardening
	#@num - number of issues we found
	#@percent - percent of audit process
	#@command - which command is being used now
	def sync_process(self, socket, session_id, module_id, num, percent, command):
		response = {
			"cmd_id" : "1029",
			"session_id" : session_id,
			"module_id" : module_id,
			"num" : num,
			"percent" : percent,
			"command" : command,
			"error" : ""
		}

		socket.response(response)