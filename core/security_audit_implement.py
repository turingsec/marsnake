from utils import lib, common, file_op, time_op
from core.vuls import Kvuls
from core.language import Klanguage
import re, os, platform, psutil

uid_min = 1000
uid_max = 60000

LEVEL_INVALID = -1
LEVEL_SECURITY = 0
LEVEL_WARNING = 1
LEVEL_CRITICAL = 2

def get_useradd_list(response):
	global uid_min
	global uid_max

	#root:x:0:0:root:/root:/bin/bash
	uid_values = [[Klanguage().to_ts(1135), Klanguage().to_ts(1136), Klanguage().to_ts(1137), Klanguage().to_ts(1138), Klanguage().to_ts(1139)]]
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

	response["authentication"].append({
		"name" : Klanguage().to_ts(1134),
		"values" : uid_values
	})

def login_defs_policy(response):
	global uid_min
	global uid_max

	values = [[Klanguage().to_ts(1148), Klanguage().to_ts(1149), Klanguage().to_ts(1119)]]
	data = file_op.cat("/etc/login.defs", "r")

	if data:
		lines = data.split("\n")

		for line in lines:
			if line:
				# The default PATH settings, for superuser.
				tmp, num = common.grep(line, r"^ENV_SUPATH\s*(\S+)")
				if num:
					values.append([Klanguage().to_ts(1180), tmp, LEVEL_INVALID, ""])
					continue

				# The default PATH settings, for normal users.
				tmp, num = common.grep(line, r"^ENV_PATH\s*(\S+)")
				if num:
					values.append([Klanguage().to_ts(1179), tmp, LEVEL_INVALID, ""])
					continue

				# UMASK is the default umask value for pam_umask and is used by
				# useradd and newusers to set the mode of the new home directories.
				tmp, num = common.grep(line, r"^UMASK\s*(\S+)")
				if num:
					if tmp == "077" or tmp == "027" or tmp == "0077" or tmp == "0027":
						level = LEVEL_SECURITY
					else:
						level = LEVEL_WARNING
						response["statistic"]["warning"] += 1

					values.append([Klanguage().to_ts(1178), tmp, level, Klanguage().to_ts(1177)])
					continue

				# If defined, login failures will be logged here in a utmp format
				# last, when invoked as lastb, will read /var/log/btmp, so...
				tmp, num = common.grep(line, r"^FTMP_FILE\s*(\S+)")
				if num:
					values.append([Klanguage().to_ts(1176), tmp, LEVEL_INVALID, ""])
					continue

				# Algorithm will be used for encrypting password
				tmp, num = common.grep(line, r"^ENCRYPT_METHOD\s*(\S+)")
				if num:
					if tmp == "SHA512":
						level = LEVEL_SECURITY
						suggest = Klanguage().to_ts(1173)
					else:
						level = LEVEL_WARNING
						suggest = Klanguage().to_ts(1174)
						response["statistic"]["warning"] += 1

					values.append([Klanguage().to_ts(1175), tmp, level, suggest])
					continue

				#Password aging controls
				#Maximum number of days a password may be used
				tmp, num = common.grep(line, r"^PASS_MAX_DAYS\s*(\d+)")
				if num:
					if tmp == "99999":
						level = LEVEL_WARNING
						suggest = Klanguage().to_ts(1170)
						response["statistic"]["warning"] += 1
					else:
						level = LEVEL_SECURITY
						suggest = Klanguage().to_ts(1171)

					values.append([Klanguage().to_ts(1172), tmp, level, suggest])
					continue

				#Minimum number of days allowed between password changes.
				tmp, num = common.grep(line, r"^PASS_MIN_DAYS\s*(\d+)")
				if num:
					if tmp == "0":
						level = LEVEL_WARNING
						suggest = Klanguage().to_ts(1167)
						response["statistic"]["warning"] += 1
					else:
						level = LEVEL_SECURITY
						suggest = Klanguage().to_ts(1168)

					values.append([Klanguage().to_ts(1169), tmp, level, suggest])
					continue

				#Number of days warning given before a password expires.
				tmp, num = common.grep(line, r"^PASS_WARN_AGE\s*(\d+)")
				if num:
					level = LEVEL_SECURITY
					suggest = Klanguage().to_ts(1165)

					values.append([Klanguage().to_ts(1166), tmp, level, suggest])
					continue

				#Min/max values for automatic uid selection in useradd
				tmp, num = common.grep(line, r"^UID_MIN\s*(\d+)")
				if num:
					uid_min = tmp
					continue

				#Min/max values for automatic uid selection in useradd
				tmp, num = common.grep(line, r"^UID_MAX\s*(\d+)")
				if num:
					uid_max = tmp
					continue

	response["authentication"].append({
		"name" : Klanguage().to_ts(1147),
		"values" : values
	})

def logged_user(response):

	values = [[Klanguage().to_ts(1135), Klanguage().to_ts(1141), Klanguage().to_ts(1142), Klanguage().to_ts(1143)]]

	for user in psutil.users():
		values.append([
			user[0],
			user[1],
			user[2],
			time_op.timestamp2string(int(user[3]))
		])

	response["authentication"].append({
		"name" : Klanguage().to_ts(1140),
		"values" : values
	})

def check_sudoers_file(response):
	sudoers = ["/etc/sudoers", "/usr/local/etc/sudoers", "/usr/pkg/etc/sudoers"]
	values = [[Klanguage().to_ts(1145), Klanguage().to_ts(1146), Klanguage().to_ts(1119)]]

	for path in sudoers:
		if os.path.exists(path):
			_stat = os.lstat(path)
			permissions = lib.permissions_to_unix_name(_stat.st_mode)

			if permissions == "-r--r-----":
				level = LEVEL_SECURITY
				suggest = Klanguage().to_ts(1181)
			elif permissions == "-rw-------" or permissions == "-rw-rw----":
				level = LEVEL_WARNING
				suggest = Klanguage().to_ts(1182)
				response["statistic"]["warning"] += 1
			else:
				level = LEVEL_CRITICAL
				suggest = Klanguage().to_ts(1183)
				response["statistic"]["critical"] += 1

			values.append([path, permissions, level, suggest])

	if len(values) > 1:
		response["authentication"].append({
			"name" : Klanguage().to_ts(1184),
			"values" : values
		})

def security_info(response):

	selinux = check_selinux()
	smep = is_smep_enable()
	aslr = is_aslr_enable()
	nx = cpu_nx_support()

	if selinux[1] == LEVEL_WARNING:
		response["statistic"]["warning"] += 1
	elif selinux[1] == LEVEL_CRITICAL:
		response["statistic"]["critical"] += 1

	if smep[1] == LEVEL_WARNING:
		response["statistic"]["warning"] += 1
	elif smep[1] == LEVEL_CRITICAL:
		response["statistic"]["critical"] += 1

	if aslr[1] == LEVEL_WARNING:
		response["statistic"]["warning"] += 1
	elif aslr[1] == LEVEL_CRITICAL:
		response["statistic"]["critical"] += 1

	if nx[1] == LEVEL_WARNING:
		response["statistic"]["warning"] += 1
	elif nx[1] == LEVEL_CRITICAL:
		response["statistic"]["critical"] += 1

	response["feature"] = [[Klanguage().to_ts(1117), Klanguage().to_ts(1118), Klanguage().to_ts(1119)],
						[Klanguage().to_ts(1125), selinux[0], selinux[1], selinux[2]],
						[Klanguage().to_ts(1126), smep[0], smep[1], smep[2]],
						[Klanguage().to_ts(1127), aslr[0], aslr[1], aslr[2]],
						[Klanguage().to_ts(1128), nx[0], nx[1], nx[2]]]

def cpu_nx_support():
	suggest = Klanguage().to_ts(1185)

	try:
		data = file_op.cat("/proc/cpuinfo", "r")

		if data:
			flags, num = common.grep(data, r"flags\s*:\s(.*)")
			nx, num = common.grep(flags, r"nx")

		if nx == "nx":
			return Klanguage().to_ts(1120), LEVEL_SECURITY, suggest

	except Exception as e:
		pass

	return Klanguage().to_ts(1121), LEVEL_WARNING, suggest

def check_selinux():
	selinux_config = "/etc/selinux/config"
	selinux_root = ["/sys/fs/selinux", "/selinux"]
	mode = ["disabled", "permissive", "enforcing"]
	level = [LEVEL_CRITICAL, LEVEL_WARNING, LEVEL_SECURITY]
	suggest = [Klanguage().to_ts(1189), Klanguage().to_ts(1190), Klanguage().to_ts(1191)]

	if os.path.exists(selinux_config):
		with open(selinux_config, "r") as f:
			for line in f.readlines():
				if line:
					if line.startswith("#"):
						continue

					if "=" in line:
						key, value = line.split("=")
						value = value.strip()

						if value in mode:
							return value, level[mode.index(value)], suggest[mode.index(value)]

	return mode[0], level[0], suggest[0]

def is_aslr_enable():
	status = [Klanguage().to_ts(1192), Klanguage().to_ts(1193), Klanguage().to_ts(1194)]
	level = [LEVEL_CRITICAL, LEVEL_WARNING, LEVEL_SECURITY]
	suggest_0 = Klanguage().to_ts(1195)
	suggest = [suggest_0, suggest_0, Klanguage().to_ts(1196)]

	if os.path.exists("/proc/sys/kernel/randomize_va_space"):
		with open("/proc/sys/kernel/randomize_va_space") as f:
			v = f.read().strip()

			if v.isdigit():
				if int(v) in [0, 1, 2]:
					return status[int(v)], level[int(v)], suggest[int(v)]

	return status[0], level[0], suggest[0]

def is_smep_enable():
	suggest = Klanguage().to_ts(1197)

	if os.path.exists("/proc/cpuinfo"):
		with open("/proc/cpuinfo") as f:
			if "smep" in f.read():
				return Klanguage().to_ts(1120), LEVEL_SECURITY, suggest

	return Klanguage().to_ts(1121), LEVEL_WARNING, suggest

#/usr/share/update-notifier/notify-reboot-required
#echo "*** $(eval_gettext "System restart required") ***" > /var/run/reboot-required
#echo "$DPKG_MAINTSCRIPT_PACKAGE" >> /var/run/reboot-required.pkgs
def check_need_reboot(response):
	#linux-image-4.4.0-96-generic
	#linux-base
	pkgs = "/var/run/reboot-required.pkgs"

	#*** System restart required ***
	reboot = "/var/run/reboot-required"
	values = [["Packages"]]
	exists_pkgs = []

	if os.path.exists(reboot) and os.path.exists(pkgs):

		response["kernel"].append({
			"name" : Klanguage().to_ts(1164),
			"value" : "Yes"
		})

		data = file_op.cat(pkgs, "r")

		if data:
			lines = data.split("\n")

			for line in lines:
				if line:
					if line not in exists_pkgs:
						values.append([line])
						exists_pkgs.append(line)

	if len(values) > 1:
		response["kernel"].append({
			"name" : Klanguage().to_ts(1158),
			"values" : values
		})

def enum_kernel_modules(response):
	data = file_op.cat("/proc/modules", "r")
	count = 0

	#xt_CHECKSUM 16384 1 - Live 0xffffffffc0c19000
	if data:
		lines = data.split("\n")

		for line in lines:
			if line:
				count += 1

	response["kernel"].append({
		"name" : Klanguage().to_ts(1131),
		"value" : count
	})

	response["kernel"].append({
		"name" : Klanguage().to_ts(1132),
		"value" : "Modular" if count > 1 else "Monolithic"
	})

def kernel_default_limits(response):
	data = file_op.cat("/proc/1/limits", "r")
	values = [["Limit", "Soft Limit", "Hard Limit", "Units"]]

	if data:
		lines = data.split("\n")
		keys = ["Max cpu time",
				"Max file size",
				"Max data size",
				"Max stack size",
				"Max core file size",
				"Max resident set",
				"Max processes",
				"Max open files",
				"Max locked memory",
				"Max address space",
				"Max file locks",
				"Max pending signals",
				"Max msgqueue size",
				"Max nice priority",
				"Max realtime priority",
				"Max realtime timeout"]

		for line in lines:
			if line:
				for key in keys:
					pattern = re.compile(r"^({})\s*(\S*)\s*(\S*)\s*(\S*)".format(key))
					match = pattern.match(line)

					if match:
						_, soft, hard, units = match.groups()

						values.append([
							key,
							soft,
							hard,
							units])

		if len(values) > 1:
			response["kernel"].append({
				"name" : Klanguage().to_ts(1163),
				"values" : values
			})

def kernel_available_version(response):
	available_kernel = ""

	if common.check_programs_installed("yum"):
		data, success, retcode = common.exec_command(["yum", "list", "updates", "kernel"])

		if success:
			lines = data.split("\n")
			begin_pattern = re.compile(r"^Available Upgrades")
			begin_pattern2 = re.compile(r"^Updated Packages")
			begin_pattern3 = re.compile(r"^Upgraded Packages")
			is_begin = False

			for line in lines:
				if not is_begin:
					if begin_pattern.match(line) or begin_pattern2.match(line) or begin_pattern3.match(line):
						is_begin = True
						continue
				else:
					result = line.split()

					if len(result) == 3:
						available_kernel = result[1]
						break

	elif common.check_programs_installed("apt-cache"):
		data, success, retcode = common.exec_command(["apt-cache", "search", "linux-image"])

		if success:
			lines = data.split("\n")
			pattern = re.compile(r"^linux-image-([\d\.]+)-(\d*)-")
			kernel_versions = []

			for line in lines:
				match = pattern.match(line.strip())

				if match and len(match.groups()) == 2:
					kernel_versions.append(match.groups())

			kernel_versions.sort(key = lambda v: "".join(x.zfill(5) for x in v[0].split(".") + [v[1]]), reverse = True)

			if len(kernel_versions):
				available_kernel = "-".join(kernel_versions[0])

	response["kernel"].append({
		"name" : Klanguage().to_ts(1129),
		"value" : platform.release()
	})

	if available_kernel:
		response["kernel"].append({
			"name" : Klanguage().to_ts(1130),
			"value" : available_kernel
		})

#https://serverfault.com/questions/56800/on-redhat-what-does-kernel-suid-dumpable-1-mean
def check_coredump_config(response):

	if common.is_linux():
		dumpable = "/proc/sys/fs/suid_dumpable"
		config = {
			"0" : "Default",
			"1" : "Debug",
			"2" : "Protected"
		}

		if os.path.exists(dumpable):
			data = file_op.cat(dumpable, "r")

			if data and data in config:
				response["kernel"].append({
					"name" : Klanguage().to_ts(1159),
					"value" : config[data]
				})

def check_kdump_config(response):
	if common.is_linux():
		kdump_cmdline = "/proc/cmdline"
		crashkernel = ""

		if os.path.exists(kdump_cmdline):
			data = file_op.cat(kdump_cmdline, "r")

			if data:
				crashkernel, num = common.grep(data, r"crashkernel=(\S+)")

		#enable
		if crashkernel:
			kdump_conf = "/etc/kdump.conf"
			if os.path.exists(kdump_conf):
				data = file_op.cat(kdump_conf, "r")

				if data:
					lines = data.split("\n")
					values = [["Reserved memory", crashkernel]]
					keys = ["Store the dump to a remote machine using the NFS protocol,",
							"Local directory in which the core dump is to be saved",
							"Write dump to storage devices",
							"Write the dump directly to a device",
							"Core collector to compress the data",
							"Action to perform in case dumping fails",
							"Store the dump to a remote machine using the SSH protocol",
							"SSH Key"]
					patterns = [re.compile(r"nfs\s(\S+)"),
								re.compile(r"path\s(\S+)"),
								re.compile(r"ext4\s(\S+)"),
								re.compile(r"raw\s(\S+)"),
								re.compile(r"core_collector\s(\S+).*"),
								re.compile(r"default\s(\S+)"),
								re.compile(r"ssh\s(\S+)"),
								re.compile(r"sshkey\s(\S+)")]

					for line in lines:
						for i in range(len(patterns)):
							match = patterns[i].match(line)

							if match and len(match.groups()):
								values.append([keys[i], match.groups()[0]])

					response["kernel"].append({
						"name" : Klanguage().to_ts(1160),
						"values" : values
					})

#https://fedoraproject.org/wiki/QA/Sysrq
def check_magickey_configuration(response):
	magickey = "/proc/sys/kernel/sysrq"

	if os.path.exists(magickey):
		data_magickey = file_op.cat(magickey, "r")

		response["kernel"].append({
			"name" : Klanguage().to_ts(1133),
			"value" : Klanguage().to_ts(1121) if data_magickey == "0" else Klanguage().to_ts(1120)
		})

def check_upgradable_packages(response):
	count = Kvuls().get_upgradable_packages_num()

	response["kernel"].append({
		"name" : Klanguage().to_ts(1161),
		"value" : count
	})
