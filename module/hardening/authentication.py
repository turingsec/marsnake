from utils import lib, common, file_op, time_op
from utils.harden_mgr import Kharden
import psutil, re, os

uid_min = 1000
uid_max = 60000

#https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Managing_Smart_Cards/PAM_Configuration_Files.html#PAM_Configuration_Files-PAM_Service_Files
def get_useradd_list(response):
	global uid_min
	global uid_max

	user_connect_time = {}

	if lib.check_programs_installed("ac"):
		data, success, retcode = common.exec_command(["ac", "-p"])

		if success:
			lines = data.split("\n")

			for line in lines:
				result = line.split()

				if len(result) == 2:
					user_connect_time[result[0]] = result[1]

	uid_values = [["USERNAME", "UID", "GID", "HOME", "SHELL"]]

	if user_connect_time:
		uid_values[0].append("TOTAL CONNECT HOURS")

	gid_values = [["GID", "GROUP NAME", "MEMBERS"]]

	#root:x:0:0:root:/root:/bin/bash
	#bin:x:1:1:bin:/bin:/sbin/nologin
	#daemon:x:2:2:daemon:/sbin:/sbin/nologin
	data = file_op.cat("/etc/passwd", "r")

	if data:
		lines = data.split("\n")

		for line in lines:
			if line:
				username, password, uid, gid, comment, home, shell = line.split(":")

				if int(uid) >= int(uid_min) and int(uid) <= int(uid_max):
					uid_values.append([
						username,
						uid,
						gid,
						home,
						shell
					])

					if user_connect_time:
						uid_values[len(uid_values) - 1].append(user_connect_time[username] if username in user_connect_time else "Unknown")

	#root:x:0:
	#bin:x:1:
	#daemon:x:2:
	data = file_op.cat("/etc/group", "r")

	if data:
		lines = data.split("\n")

		for line in lines:
			if line:
				group_name, password, gid, members = line.split(":")

				gid_values.append([
					gid,
					group_name,
					members
				])

	response["authentication"].append({
		"name" : "Users create with useradd",
		"value" : len(uid_values) - 1,
		"values" : uid_values
	})

	response["authentication"].append({
		"name" : "User groups",
		"value" : len(gid_values) - 1,
		"values" : gid_values
	})

def login_defs_policy(response):
	global uid_min
	global uid_max

	values = [["ITEM", "VALUE"]]
	data = file_op.cat("/etc/login.defs", "r")

	if data:
		lines = data.split("\n")

		for line in lines:
			if line:
				# The default PATH settings, for superuser.
				tmp, num = common.grep(line, r"^ENV_SUPATH\s*(\S+)")
				if num:
					values.append(["Default PATH settings for superuser", tmp])
					continue

				# The default PATH settings, for normal users.
				tmp, num = common.grep(line, r"^ENV_PATH\s*(\S+)")
				if num:
					values.append(["Default PATH settings for normal users", tmp])
					continue

				# UMASK is the default umask value for pam_umask and is used by
				# useradd and newusers to set the mode of the new home directories.
				tmp, num = common.grep(line, r"^UMASK\s*(\S+)")
				if num:
					values.append(["UMASK", tmp])
					continue

				# If defined, login failures will be logged here in a utmp format
				# last, when invoked as lastb, will read /var/log/btmp, so...
				tmp, num = common.grep(line, r"^FTMP_FILE\s*(\S+)")
				if num:
					values.append(["Login failures will be logged in", tmp])
					continue

				# Algorithm will be used for encrypting password
				tmp, num = common.grep(line, r"^ENCRYPT_METHOD\s*(\S+)")
				if num:
					values.append(["Algorithm will be used for encrypting password", tmp])
					continue

				#Min/max values for automatic uid selection in useradd
				tmp, num = common.grep(line, r"^UID_MIN\s*(\d+)")
				if num:
					values.append(["Min values for automatic uid selection in useradd", tmp])
					uid_min = tmp
					continue

				#Min/max values for automatic uid selection in useradd
				tmp, num = common.grep(line, r"^UID_MAX\s*(\d+)")
				if num:
					values.append(["Max values for automatic uid selection in useradd", tmp])
					uid_max = tmp
					continue

				#Min/max values for automatic gid selection in groupadd
				tmp, num = common.grep(line, r"^GID_MIN\s*(\d+)")
				if num:
					values.append(["Min values for automatic gid selection in groupadd", tmp])
					continue

				#Min/max values for automatic gid selection in groupadd
				tmp, num = common.grep(line, r"^GID_MAX\s*(\d+)")
				if num:
					values.append(["Max values for automatic gid selection in groupadd", tmp])
					continue

				#Password aging controls
				#Maximum number of days a password may be used
				tmp, num = common.grep(line, r"^PASS_MAX_DAYS\s*(\d+)")
				if num:
					values.append(["Maximum number of days a password may be used", tmp])
					continue

				#Minimum number of days allowed between password changes.
				tmp, num = common.grep(line, r"^PASS_MIN_DAYS\s*(\d+)")
				if num:
					values.append(["Minimum number of days allowed between password changes.", tmp])
					continue

				#Number of days warning given before a password expires.
				tmp, num = common.grep(line, r"^PASS_WARN_AGE\s*(\d+)")
				if num:
					values.append(["Number of days warning given before a password expires.", tmp])
					continue

	response["authentication"].append({
		"name" : "Configuration control definitions for the login package",
		"value" : len(values) - 1,
		"values" : values
	})

def logged_user(response):

	values = [["NAME", "TERMINAL", "HOST", "STARTED"]]

	for user in psutil.users():
		values.append([
			user[0],
			user[1],
			user[2],
			time_op.timestamp2string(int(user[3]))
		])

	response["authentication"].append({
		"name" : "Who is logged on",
		"value" : len(values) - 1,
		"values" : values
	})

def check_sudoers_file(response):
	sudoers = ["/etc/sudoers", "/usr/local/etc/sudoers", "/usr/pkg/etc/sudoers"]
	values = [[]]

	for path in sudoers:
		if os.path.exists(path):
			_stat = os.lstat(path)
			permissions = lib.permissions_to_unix_name(_stat.st_mode)
			values.append([path, permissions])

	if len(values) > 1:
		response["authentication"].append({
			"name" : "Permissions of sudoers",
			"value" : len(values) - 1,
			"values" : values
		})

#https://www.cyberciti.biz/faq/linux-unix-bsd-varaccountpacct-or-varlogaccountpacct-file/
def check_accounting(response):
	accounting_file = ["/var/account/acct", "/var/account/pacct", "/var/log/account/pacct", "/var/adm/pacct"]

	for file in accounting_file:
		if os.path.exists(file):
			pass

def run(payload, socket):

	session_id = payload["args"]["session_id"]

	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : session_id,
		"authentication" : [],
		"error" : ""
	}

	login_defs_policy(response)
	get_useradd_list(response)
	logged_user(response)
	check_sudoers_file(response)
	check_accounting(response)

	Kharden().sync_process(socket, session_id, Kharden().AUTHENTICATION, 0,
		[0, 0.125, 0.25, 0.5, 0.75, 1],
		["cat /etc/login.defs", "cat /etc/passwd",
		"cat /etc/group", "who",
		"ll /etc/sudoers", "Finished"])

	socket.response(response)
