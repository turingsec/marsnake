from utils import lib, common, file_op
from utils.harden_mgr import Kharden
import re, os, platform

def check_selinux(response):
    selinux_config = "/etc/selinux/config"
    selinux_root = ["/sys/fs/selinux", "/selinux"]

    current_mode = "Disabled"
    config_mode = "Disabled"
    mls_status = "Disabled"
    deny_unknown = "Denied"
    policyvers = "Unknown"
    policy = "Unknown"
    mount = ""

    for i in selinux_root:
        if os.path.exists(i) and os.path.isdir(i):

            mount = i
            data = file_op.cat(os.path.join(i, "enforce"), "r")

            if data:
                if int(data) == 1:
                    current_mode = "enforcing"

                if int(data) == 0:
                    current_mode = "permissive"

            data = file_op.cat(os.path.join(i, "mls"), "r")

            if data:
                if int(data) == 1:
                    mls_status = "enabled"

            data = file_op.cat(os.path.join(i, "deny_unknown"), "r")

            if data:
                if int(data) == 0:
                    deny_unknown = "allowed"

            data = file_op.cat(os.path.join(i, "policyvers"), "r")

            if data:
                policyvers = data

            break

    if os.path.exists(selinux_config):
        with open(selinux_config, "r") as f:
            for line in f.readlines():
                if line:
                    if line.startswith("#"):
                        continue

                    if "=" in line:
                        key, value = line.split("=")
                        value = value.strip()

                        if value in ["enforcing", "permissive", "disabled"]:
                            config_mode = value

                        if value in ["targeted", "minimum", "mls"]:
                            policy = value

    response["kernel"].append({"name" : "SElinux Status",
                                "value" : config_mode,
                                "values" : [
                                [],
                                ["SELinuxfs mount", mount],
                                ["Loaded policy name", policy],
                                ["Current mode", current_mode],
                                ["Policy MLS status", mls_status],
                                ["Policy deny_unknown status", deny_unknown],
                                ["Max kernel policy version", policyvers]]})

def security_info(response):
    response["kernel"].append({"name" : "SMEP",
                                "value" : is_smep_enable()})

    response["kernel"].append({"name" : "ASLR",
                                "value" : is_aslr_enable()})

def is_aslr_enable():
    status = ["No randomization", "Conservative randomization", "Full randomization"]

    if os.path.exists("/proc/sys/kernel/randomize_va_space"):
        with open("/proc/sys/kernel/randomize_va_space") as f:
            v = f.read().strip()

            if v.isdigit():
                if int(v) in [0, 1, 2]:
                    return status[int(v)]

    return status[0]

def is_smep_enable():
    if os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo") as f:
            if "smep" in f.read():
                return "Enabled"

    return "Disabled"

#/usr/share/update-notifier/notify-reboot-required
# Wake the applet up
#echo "*** $(eval_gettext "System restart required") ***" > /var/run/reboot-required
#echo "$DPKG_MAINTSCRIPT_PACKAGE" >> /var/run/reboot-required.pkgs
def check_need_reboot(response):
	#linux-image-4.4.0-96-generic
	#linux-base
	#linux-base
	pkgs = "/var/run/reboot-required.pkgs"

	#*** System restart required ***
	reboot = "/var/run/reboot-required"
	values = [["Packages"]]

	if os.path.exists(reboot) and os.path.exists(pkgs):

		response["kernel"].append({
			"name" : "Reboot Required",
			"value" : "Yes"
		})

		data = file_op.cat("/var/run/reboot-required.pkgs", "r")

		if data:
			lines = data.split("\n")

			for line in lines:
				if line:
					values.append([line])

	if len(values) > 1:
		response["kernel"].append({
			"name" : "Reboot Required Packages",
			"value" : len(values) - 1,
			"values" : values
		})

def default_io_scheduler(response):
	config_file = find_kernel_config()

	if config_file:
		data = file_op.cat(config_file, "r")
		if data:
			io_scheduler, num = common.grep(data, r"CONFIG_DEFAULT_IOSCHED=(\S*)")

			if num:
				response["kernel"].append({
					"name" : "IO Scheduler",
					"value" : io_scheduler
				})

def find_kernel_config():
	config_file = "/boot/config-{}".format(platform.release())

	if common.check_file_exists([config_file]):
		return config_file

	'''
	config_file = "/proc/config.gz"

	if lib.check_file_exists([config_file]):
		return config_file
	'''
	return ""

def get_module_description(module):
	data, success, retcode = common.exec_command(["modinfo", module])

	if success:
		lines = data.split("\n")
		pattern = re.compile(r"^description:\s+(.+)")

		for line in lines:
			match = pattern.match(line)

			if match and len(match.groups()):
				return match.groups()[0]

	return ""

def enum_kernel_modules(response):
	data = file_op.cat("/proc/modules", "r")
	values = [["MODULE", "SIZE", "USED", "BY", "DESCRIPTION"]]

	#xt_CHECKSUM 16384 1 - Live 0xffffffffc0c19000
	#ipt_MASQUERADE 16384 3 - Live 0xffffffffc0c0f000
	#video 40960 3 thinkpad_acpi,nouveau,i915, Live 0xffffffffc0296000
	#wmi 20480 2 nouveau,mxm_wmi, Live 0xffffffffc028c000
	if data:
		lines = data.split("\n")

		for line in lines:
			if line:
				module, size, used, by, _ = line.split(" ", 4)

				values.append([module,
					size,
					used,
					by,
					get_module_description(module)
				])

	if len(values) > 1:
		response["kernel"].append({
			"name" : "Modules",
			"value" : len(values) - 1,
			"values" : values
		})

	response["kernel"].append({
		"name" : "Kernel Type",
		"value" : "Modular" if len(values) > 1 else "Monolithic"
	})

def kernel_default_limits(response):
	data = file_op.cat("/proc/1/limits", "r")
	values = [["Limit", "Soft Limit", "Hard Limit", "Units"]]

	if data:
		lines = data.split("\n")
		keys = {"Max cpu time" : "CPU time",
				"Max file size" : "file size",
				"Max data size" : "data seg size",
				"Max stack size" : "stack size",
				"Max core file size" : "core file size",
				"Max resident set" : "resident set size",
				"Max processes" : "max user processes",
				"Max open files" : "number of open files",
				"Max locked memory" : "locked-in-memory address space",
				"Max address space" : "address space limit",
				"Max file locks" : "file locks",
				"Max pending signals" : "pending signals",
				"Max msgqueue size" : "POSIX message queues",
				"Max nice priority" : "scheduling priority",
				"Max realtime priority" : "realtime priority",
				"Max realtime timeout" : "realtime timeout"
				}

		for line in lines:
			if line:
				for key in keys:
					pattern = re.compile(r"^({})\s*(\S*)\s*(\S*)\s*(\S*)".format(key))
					match = pattern.match(line)

					if match:
						item, soft, hard, units = match.groups()

						values.append([
							keys[item],
							soft,
							hard,
							units
						])

		if len(values) > 1:
			response["kernel"].append({
				"name" : "Resource Limit",
				"value" : len(values) - 1,
				"values" : values
			})

def kernel_available_version(response):
	available_kernel = ""

	if lib.check_programs_installed("yum"):
		data, success, retcode = common.exec_command(["yum", "list", "updates", "kernel"])

		if success:
			lines = data.split("\n")
			begin_pattern = re.compile(r"^Available Upgrades")
			begin_pattern2 = re.compile(r"^Updated Packages")
			is_begin = False

			for line in lines:
				if not is_begin:
					if begin_pattern.match(line):
						is_begin = True

					if begin_pattern2.match(line):
						is_begin = True

				result = line.split()

				if len(result) == 3:
					available_kernel = result[1]
					break

	elif lib.check_programs_installed("apt-cache"):
		data, success, retcode = common.exec_command(["apt-cache", "search", "linux-generic"])

		if success:
			lines = data.split("\n")
			pattern = re.compile(r"^linux-image-([0-9]+\S+)-generic.*")
			kernel_versions = []

			for line in lines:
				match = pattern.match(line)

				if match and len(match.groups()):
					kernel_versions.append(match.groups()[0])

			kernel_versions.sort(key = lambda t : int(t.replace(".", "").replace("-", "")), reverse = True)

			if len(kernel_versions):
				available_kernel = kernel_versions[0]

	response["kernel"].append({
		"name" : "Kernel current version",
		"value" : platform.release()
	})

	if available_kernel:
		response["kernel"].append({
			"name" : "Kernel latest stable version",
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
					"name" : "Core dump mode",
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
					values = [["Key", "Value"], ["Reserved memory", crashkernel]]
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
						"name" : "Kernel Dump Configuration",
						"value" : len(values) - 1,
						"values" : values
					})

#https://fedoraproject.org/wiki/QA/Sysrq
def check_magickey_configuration(response):
	magickey = "/proc/sys/kernel/sysrq "

	if os.path.exists(magickey):
		data_magickey = file_op.cat(magickey, "r")

		response["kernel"].append({
			"name" : "Magic system request Key",
			"Value" : "Disable" if data_magickey == "0" else "Enabled"
		})

def run(payload, socket):

	session_id = payload["args"]["session_id"]

	response = {
		'cmd_id' : payload['cmd_id'],
		"session_id" : session_id,
		"kernel" : [],
		'error' : ""
	}

	kernel_available_version(response)
	enum_kernel_modules(response)
	check_need_reboot(response)
	default_io_scheduler(response)
	kernel_default_limits(response)
	check_coredump_config(response)
	check_kdump_config(response)
	check_magickey_configuration(response)
	check_selinux(response)
	security_info(response)

	Kharden().sync_process(socket, session_id, Kharden().KERNEL, 0,
		[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
		["cat /etc/selinux/config",
		"test -d /sys/fs/selinux",
		"test -d /selinux",
		"cat /proc/sys/kernel/randomize_va_space",
		"cat /proc/cpuinfo",
		"cat /proc/modules",
		"test -f /var/run/reboot-required.pkgs",
		"/proc/1/limits",
		"test -f /var/run/reboot-required",
		"Finished"])

	socket.response(response)
