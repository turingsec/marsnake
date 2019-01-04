from utils import lib, common, file_op
from core.language import Klanguage
import re, os, stat

service_manager = ""
runlevel = ""
bootloader = ""

def runlevel2means():
	global runlevel

	levels_mean = {
		"0" : Klanguage().to_ts(1825),
		"1" : Klanguage().to_ts(1826),
		"234" : Klanguage().to_ts(1827),
		"5" : Klanguage().to_ts(1828),
		"6" : Klanguage().to_ts(1829)
	}

	for level, value in levels_mean.items():
		if str(runlevel) in level:
			return value

	return runlevel

def find_runlevel():
	global runlevel

	#runlevel
	#N 5
	#who -r
	#         run-level 5  2017-07-08 15:12
	data, success, retcode = common.exec_command(['runlevel'])
	if success:
		runlevel_pattern = re.compile(r'^N\s(\d)')
		match = runlevel_pattern.match(data)

		if match:
			runlevel = match.groups()[0]
			return

	#/etc/systemd/system/default.target -> /lib/systemd/system/graphical.target
	default_target = "/etc/systemd/system/default.target"
	target = lib.readlink(default_target, 1)

	if target != "":
		for i in ["runlevel5.target", "graphical.target"]:
			tmp, num = common.grep(target, i)
			if num:
				runlevel = 5
				return

		for i in ["runlevel3.target", "multi-user.target"]:
			tmp, num = common.grep(target, i)
			if num:
				runlevel = 3
				return

	## Default runlevel. The runlevels used are:
	#   0 - halt (Do NOT set initdefault to this)
	#   1 - Single user mode
	#   2 - Multiuser, without NFS (The same as 3, if you do not have networking)
	#   3 - Full multiuser mode
	#   4 - unused
	#   5 - X11
	#   6 - reboot (Do NOT set initdefault to this)
	#
	#id:3:initdefault:
	data = file_op.cat("/etc/inittab", "r")

	if data:
		lines = data.split("\n")

		for line in lines:
			tmp, num = common.grep(line, r"^id:(\d)")
			if num:
				runlevel = tmp
				return

	#         run-level 5  2017-09-17 13:35
	data, success, retcode = common.exec_command(['who', '-r'])
	if success:
		tmp, num = common.grep(data, r"^\s*run-level\s(\d)")
		if num:
			runlevel = tmp
			return

def find_boot_loader():
	global bootloader

	if file_op.check_file_exists(["/boot/syslinux/syslinux.cfg"]):
		bootloader = "Syslinux"

	if file_op.check_file_exists(["/boot/grub/grub.conf", "/boot/grub/menu.lst"]):
		bootloader = "GRUB"

	if file_op.check_file_exists(["/boot/grub/grub.cfg", "/boot/grub2/grub.cfg", "/boot/grub2/"]):
		bootloader = "GRUB2"

def find_service_manager():
	global service_manager

	data, success, retcode = common.exec_command(['cat', '/proc/1/cmdline'])
	if success:
		systemd_pattern = re.compile(r'systemd')

		if systemd_pattern.search(data):
			service_manager = "systemd"

		init_pattern = re.compile(r'init')

		if init_pattern.search(data):
			service_manager = "SysV Init"

		upstart_pattern = re.compile(r'upstart')

		if upstart_pattern.search(data):
			service_manager = "upstart"

def get_boot_services(response):
	global runlevel

	if common.check_programs_installed("systemctl"):
		values = []
		blame = {}

		#service time
		data, success, retcode = common.exec_command(['systemd-analyze', 'blame'])

		if success:
			lines = data.split("\n")

			for line in lines:
				result = line.split()

				if len(result) == 2:
					index = result[0].find(".")
					if index >= 0 and len(result[0][index + 1 : index + 4]) == 3:
						result[0] = result[0][: index + 2] + result[0][index + 4 :]
					blame[result[1]] = result[0]

		data, success, retcode = common.exec_command(['systemctl', 'list-unit-files', '--type=service'])

		if success:
			lines = data.split("\n")

			for line in lines:
				result = line.split()

				if len(result) == 2 and (result[1] == "enabled" or result[1] == "disabled"):
					values.append([
						result[0],
						blame[result[0]] if result[0] in blame else "",
						lib.get_description_by_name(result[0], 0),
						result[1]
					])

		response["boot_services"] = {
			"value" : len(values),
			"values" : values
		}
	else:
		values = []

		if runlevel:
			init_rcd = "/etc/rc{}.d".format(runlevel)
			systemv_script_pattern = re.compile(r"S\d{2}(\S+)")

			for file in os.listdir(init_rcd):
				match = systemv_script_pattern.match(file)

				if match and len(match.groups()):
					values.append([
						match.groups()[0],
						"",
						lib.get_description_by_name(match.groups()[0], 2),
						"enabled"
					])

			response["boot_services"] = {
				"value" : len(values),
				"values" : values
			}

	'''
	elif lib.check_programs_installed("initctl"):
		values = [["Upstart Script", "Start On", "Stop On"]]
		upstart_config = []
		data, success, retcode = common.exec_command(['initctl', 'list'])

		if success:
			lines = data.split("\n")
			for line in lines:
				if line:
					upstart_config.append(line.split()[0])

		starton_pattern = re.compile(r"\s*start on\s(.*)")
		stopon_pattern = re.compile(r"\s*stop on\s(.*)")

		for config in upstart_config:
			data, success, retcode = common.exec_command(['initctl', 'show-config', config])

			if success:
				lines = data.split("\n")
				starton = ""
				stopon = ""

				for line in lines:
					match = starton_pattern.match(line)

					if match:
						starton = match.groups()[0]

					match = stopon_pattern.match(line)

					if match:
						stopon = match.groups()[0]

				values.append([
					config,
					starton,
					stopon])

		response["boot_services"].append({
			"name" : "Boot Services",
			"value" : len(values) - 1,
			"values" : values
		})
	'''

	'''
	elif service_manager == "upstart":
	else:
		data, success, retcode = common.exec_command(['chkconfig', '--list'])
		if success:
			lines = data.split("\n")
			result_pattern = re.compile(r'(\S*)\s*0:(\w+)\s*1:(\w+)\s*2:(\w+)\s*3:(\w+)\s*4:(\w+)\s*5:(\w+)\s*6:(\w+).*')

			for line in lines:
				result = result_pattern.match(line)

				if result and len(result.groups()) == 8:

					groups = result.groups()

					if groups[4] == "on" or groups[6] == "on":
						response["boot_services"].append([
							groups[0],
							"runlevel 3 or 5"
						])
	'''

#@path:absolute path
def check_writable_file(path, values):
	try:
		_stat = os.stat(path)

		if _stat.st_mode & stat.S_IWOTH:
			values.append([path, lib.permissions_to_unix_name(_stat.st_mode)])

	except Exception as e:
		pass

def do_enum_files(item, values):
	if os.path.exists(item):
		if os.path.isdir(item):
			for root, dirs, files in os.walk(item):
				for name in dirs:
					check_writable_file(os.path.join(root, name), values)

				for name in files:
					check_writable_file(os.path.join(root, name), values)

		elif os.path.isfile(item):
			check_writable_file(item, values)

def enum_etc_files(response):
	items = ["/etc/init.d", "/etc/rc.d", "/etc/rcS.d", "/etc/rc", "/etc/rc.local", "/etc/rc.d/rc.sysinit"]
	values = [[Klanguage().to_ts(1823), Klanguage().to_ts(1824)]]

	for item in items:
		do_enum_files(item, values)

	for i in range(7):
		item = "/etc/rc{}.d".format(i)
		do_enum_files(item, values)

	if len(values) > 1:
		response["boot_config"].append({
			"name" : Klanguage().to_ts(1822),
			"value" : len(values) - 1,
			"values" : values
		})

def check_startup_time(response):
	if common.is_linux():
		boot_time = lib.get_boot_time()

		if boot_time:
			if len(boot_time) == 4:
				response["startup_time"] = {
					"name" : [Klanguage().to_ts(1808), Klanguage().to_ts(1809), Klanguage().to_ts(1810), Klanguage().to_ts(1811)],
					"time" : [0, boot_time[0], boot_time[1], boot_time[3]],
					"icon" : [0, 1, 2, 3]
				}

				return

			if len(boot_time) == 3:
				response["startup_time"] = {
					"name" : [Klanguage().to_ts(1808), Klanguage().to_ts(1809), Klanguage().to_ts(1811)],
					"time" : [0, boot_time[0], boot_time[2]],
					"icon" : [0, 1, 3]
				}

				return

def run(payload, socket):
	global service_manager
	global bootloader

	session_id = payload["args"]["session_id"]

	response = {
		'cmd_id' : payload['cmd_id'],
		"session_id" : session_id,
		'boot_services' : {},
		'startup_time' : Klanguage().to_ts(1821),
		'boot_config' : [],
		"name" : [Klanguage().to_ts(1807), Klanguage().to_ts(1812), Klanguage().to_ts(1816)],
		'error' : ""
	}

	find_runlevel()
	find_boot_loader()
	find_service_manager()
	get_boot_services(response)
	enum_etc_files(response)
	check_startup_time(response)

	response["boot_config"].append({
		"name" : Klanguage().to_ts(1813),
		"value" : runlevel2means()
	})

	response["boot_config"].append({
		"name" : Klanguage().to_ts(1814),
		"value" : service_manager
	})

	response["boot_config"].append({
		"name" : Klanguage().to_ts(1815),
		"value" : bootloader
	})

	socket.response(response)
