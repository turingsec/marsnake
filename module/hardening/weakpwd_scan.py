import copy
import os
from utils.harden_mgr import Kharden
from utils import lib, common

userlist = []
pwdlist = []

percent = 0.0
count = 0
ip = "127.0.0.1"

def add_percent(delta, finished = False):
	global percent

	percent += delta

	if not finished:
		percent = percent if percent < 0.99 else 0.99
	else:
		percent = 1.0

	return percent

def get_percent():
	global percent
	return percent

def redispwdAuth(port, response):
	global pwdlist, ip, count

	try:
		import redis
	except Exception:
		pass
	else:
		for pwd in pwdlist:
			try:
				r = redis.Redis(host = ip, port = port, password = pwd)
				r.get("test")

				count += 1
				response["pwd"].append({
					"name" : "Redis",
					"value" : "Very Weak"
				})

				return
			except Exception as e:
				if "but no password is set" in str(e):
					count += 1
					response["pwd"].append({
						"name" : "Redis",
						"value" : "No Password Is Set"
					})
					return
					
	response["pwd"].append({
		"name" : "Redis",
		"value" : "Password Complexity Strong"
	})

def sshpwdAuth(port, response):
	global userlist, pwdlist, ip, count

	values = [["Username", "Password Complexity"]]

	try:
		import paramiko
	except Exception:
		pass
	else:
		for username in userlist:

			weak = False

			for pwd in pwdlist:
				try:
					client = paramiko.SSHClient()
					client.load_system_host_keys()
					client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					client.connect(ip, port, username, pwd)
					
					count += 1
					values.append([username, "Very Weak"])
					weak = True
					
					break
				except Exception:
					continue
					
			if not weak:
				values.append([username, "Good"])

	response["pwd"].append({
		"name" : "SSH",
		"value" : len(values) - 1,
		"values" : values
	})

def mysqlpwdAuth(port, response):
	global userlist, pwdlist, ip, count

	values = [["Username", "Password Complexity"]]

	try:
		import MySQLdb
	except Exception:
		pass
	else:
		for username in userlist:
			for pwd in pwdlist:
				try:
					MySQLdb.connect(host = ip, port = port, user = username, passwd = pwd)

					count += 1
					values.append([username, "Very Weak"])

					break
				except Exception as e:
					continue

	response["pwd"].append({
		"name" : "MySQL",
		"value" : len(values) - 1,
		"values" : values
	})

def mondbpwdAuth(port, response):
	global userlist, pwdlist, ip, count

	values = [["Username", "Password Complexity"]]

	try:
		from pymongo import MongoClient
	except Exception:
		pass
	else:
		for username in userlist:
			for pwd in pwdlist:
				try:
					client = MongoClient(ip, port)
					db = client.testdb
					db.authenticate(username, pwd)

					count += 1
					values.append([username, "Very Weak"])

					break
				except Exception as e:
					continue
		
	response["pwd"].append({
		"name" : "MongoDB",
		"value" : len(values) - 1,
		"values" : values
	})

def read_config():
	global userlist, pwdlist
	
	strip = lambda lines : [ line.strip() for line in lines]
	word_dir = common.get_work_dir()
	
	try:
		with open(os.path.join(word_dir, "config/user.txt"), "r") as f:
			userlist = strip(f.readlines())
			
		with open(os.path.join(word_dir, "config/pwd_list.txt"), "r") as f:
			pwdlist = strip(f.readlines())
	except Exception:
		pass
		
	userlist.extend(lib.find_useradd_users())

def run(payload, socket):
	session_id = payload["args"]["session_id"]
	response = {
		"error" :  "",
		"cmd_id" : payload["cmd_id"],
		"session_id" :payload["args"]["session_id"],
		"pwd" : []
	}

	global count, percent

	count = 0
	percent = 0.0

	read_config()
	Kharden().sync_process(socket, session_id, Kharden().WEAKPWD, count, [get_percent()], ["Scanning running service now"])
	
	servlist = {22 : 'ssh', 3306 : 'mysql', 6379 : 'redis', 27017 : 'mongodb'}
	serv2func = {"ssh" : sshpwdAuth, 
				"mysql" : mysqlpwdAuth, 
				"redis" : redispwdAuth, 
				"mongodb" : mondbpwdAuth}

	existports = common.get_listen_port(servlist.keys())
	existports_num = len(existports)

	Kharden().sync_process(socket, session_id, Kharden().WEAKPWD, count, [add_percent(0.1)], ["Found {} ports listening on localhost".format(existports_num)])

	if existports_num:
		tmp = 1.0 / existports_num

		for existport in existports:				
			service = servlist[existport]

			Kharden().sync_process(socket, session_id, Kharden().WEAKPWD, count, [add_percent(tmp)], ["Scanning weak pwd of {} ".format(service)])

			obj = copy.deepcopy(response)
			serv2func[service](existport, obj)
			socket.response(obj)

	Kharden().sync_process(socket, session_id, Kharden().WEAKPWD, count, [1], ["Finished"])
