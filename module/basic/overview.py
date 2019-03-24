from utils import lib, common, file_op, time_op
from utils.randomize import Krandom
from datetime import datetime
from core.logger import Klogger
from core.db import Kdatabase
from core.language import Klanguage
from config import constant

import platform, psutil, os, sys, pwd, getpass, json, time, locale

pcidb = None

def get_system_info(response):

	system_info = response["system_info"]
	home, shell = home_shell()
	language_code, encoding = locale.getdefaultlocale()

	# boot_time = lib.get_boot_time()

	# if boot_time:
	#	 if len(boot_time) == 4:
	#		 system_info.append({"BOOTUPTIME" : boot_time[3]})

	#	 if len(boot_time) == 3:
	#		 system_info.append({"BOOTUPTIME" : boot_time[2]})

	system_info.append({Klanguage().to_ts(1020) : home})
	system_info.append({Klanguage().to_ts(1021) : shell})

	#if language_code and encoding:
	#	system_info.append({"Language" : "{}/{}".format(language_code, encoding)})

	system_info.append({Klanguage().to_ts(1022) : "{0}-{1}".format(*platform.libc_ver())})

	system_info.append({Klanguage().to_ts(1024) : "{}/{}".format(platform.system(), platform.machine())})
	system_info.append({Klanguage().to_ts(1025) : "{} {}".format(*(lib.detect_distribution()))})
	system_info.append({Klanguage().to_ts(1026) : platform.release()})
	system_info.append({Klanguage().to_ts(1027) : time_op.timestamp2string(psutil.boot_time())})
	system_info.append({Klanguage().to_ts(1028) : time_op.timestamp2string(time.time())})

def home_shell():
	user_shell = "unknown"
	user_home = "unknown"
	users = pwd.getpwall()

	for user in users:
		if user[0] == getpass.getuser():
			user_home = user[5]
			user_shell = user[6]
			break

	return user_home, user_shell

def smbios_checksum(smbios_str, length):
	if len(smbios_str) < length:
		return False

	sum = 0
	for i in range(length):
		sum += int(smbios_str[i])

	return (sum & 0xff) == 0

def smbios_entry_point(smbios_ep):
	majver = 0
	minver = 0
	table_len = 0
	table_base = 0

	if len(smbios_ep) >= 24 and smbios_ep[: 5] == b'_SM3_' and smbios_checksum(smbios_ep, int(smbios_ep[6])):

		majver = int(smbios_ep[7])
		minver = int(smbios_ep[8])
		table_len = (int(smbios_ep[15]) << 24) + (int(smbios_ep[14]) << 16) + (int(smbios_ep[13]) << 8) + int(smbios_ep[12])
		table_base = ((int(smbios_ep[23]) << 56) + (int(smbios_ep[22]) << 48) + (int(smbios_ep[21]) << 40) + (int(smbios_ep[20]) << 32) +
						(int(smbios_ep[19]) << 24) + (int(smbios_ep[18]) << 16) + (int(smbios_ep[17]) << 8) + int(smbios_ep[16]))

	elif len(smbios_ep) >= 31 and smbios_ep[: 4] == b'_SM_' and smbios_ep[16 : 21] == b'_DMI_' and smbios_checksum(smbios_ep[16 :], 15):

		majver = int(smbios_ep[6])
		minver = int(smbios_ep[7])
		table_len = (int(smbios_ep[23]) << 8) + int(smbios_ep[22])
		table_base = (int(smbios_ep[27]) << 24) + (int(smbios_ep[26]) << 16) + (int(smbios_ep[25]) << 8) + int(smbios_ep[24])

	return (majver, minver, table_len, table_base)

'''
def dmi_get_hardware_info(response, smbios_info, dmi):
	offset = 0

	while offset + 4 <= len(dmi):
		_type = int(dmi[offset + 0])
		_length = int(dmi[offset + 1])

		if offset + _length > len(dmi):
			break
'''

def get_hardware_info(response):
	smbios_ep = None
	dmi = None
	'''
	try:
		with open("/sys/firmware/dmi/tables/smbios_entry_point", "rb") as smbios_ep_f:
			smbios_ep = smbios_ep_f.read()

		with open("/sys/firmware/dmi/tables/DMI", "rb") as dmi_f:
			dmi = dmi_f.read()
	except:
		pass
	'''
	if smbios_ep and dmi:
		dmi_get_hardware_info(response, smbios_ep, dmi)
	else:
		get_model_info(response)
		get_cpuinfo(response)
		get_motherboard_info(response)
		get_disk_info(response)
		get_pci_info(response)

def load_pcidb():
	global pcidb

	pcidb = {}
	pcidb_path = os.path.join(common.get_work_dir(), constant.PCIDB_CONF)

	try:
		pcidb_f = open(pcidb_path, "r", encoding = "utf8")
		pcidb_raw = pcidb_f.read().split("\n")
		pcidb_f.close()
	except:
		pcidb = None
		return

	current_vendor = None

	for line in pcidb_raw:
		if not line or line[0] == '#' or line.startswith("\t\t"):
			continue

		try:
			ident, name = line.strip().split(maxsplit = 1)
			ident = int(ident, 16)
		except:
			continue

		if line.startswith("\t"):
			if current_vendor is None:
				pcidb = None
				return

			current_vendor[ident] = name

		else:
			pcidb[ident] = (name, {})
			current_vendor = pcidb[ident][1]

def get_pci_string(vendor, device):
	global pcidb

	if pcidb == None:
		load_pcidb()
		if pcidb == None:
			return "%s %s" % (vendor, device)

	try:
		_vendor = int(vendor, 16)
		_device = int(device, 16)
	except:
		return "%s %s" % (vendor, device)

	if not _vendor in pcidb:
		return "%s %s" % (vendor, device)

	if not _device in pcidb[_vendor][1]:
		return "%s %s" % (pcidb[_vendor][0], "Unknown")
	else:
		return "%s %s" % (pcidb[_vendor][0], pcidb[_vendor][1][_device])

def get_model_info(response):
	sys_vendor = ""
	product_name = ""
	product_version = ""

	try:
		with open("/sys/class/dmi/id/sys_vendor", "r") as f:
			sys_vendor = f.read().strip()
	except:
		pass

	try:
		with open("/sys/class/dmi/id/product_name", "r") as f:
			product_name = f.read().strip()

		if product_name == "None":
			product_name = ""
	except:
		pass

	try:
		with open("/sys/class/dmi/id/product_version", "r") as f:
			product_version = f.read().strip()

		if product_version == "None":
			product_version = ""
	except:
		pass
	
	if sys_vendor or product_name or product_version:
		response["hardware"].append({Klanguage().to_ts(1014) : [ "{} {} {}".format(sys_vendor, product_name, product_version) ]})

def get_cpuinfo(response):
	try:
		data = file_op.cat("/proc/cpuinfo", "r")

		if data:
			#vendor_id, num = lib.grep(data, r"vendor_id\s*:\s(.*)")
			model_name, num = common.grep(data, r"model name\s*:\s(.*)")

			response["hardware"].append({Klanguage().to_ts(1011) : [ "{}".format(model_name) ]})

	except:
		pass

def get_motherboard_info(response):
	board_vendor = ""
	board_name = ""

	try:
		with open("/sys/class/dmi/id/board_vendor", "r") as f:
			board_vendor = f.read().strip()
	except:
		pass

	try:
		with open("/sys/class/dmi/id/board_name", "r") as f:
			board_name = f.read().strip()

		if board_name == "None":
			with open("/sys/class/dmi/id/board_version", "r") as f:
				board_name = f.read().strip()

			if board_name == "None":
				board_name = ""
	except:
		pass

	if board_vendor or board_name:
		response["hardware"].append({Klanguage().to_ts(1017) : [ "{} {}".format(board_vendor, board_name) ]})

def get_disk_info(response):
	disks = []

	for block_dev in file_op.listdir("/sys/class/block"):
		vendor = ""
		model = ""
		size = ""

		try:
			with open(os.path.join(block_dev, "device", "type"), "r") as f:
				device_type = f.read().strip()
				if device_type != '0' and device_type != '14':
					continue
		except:
			continue

		try:
			with open(os.path.join(block_dev, "device", "vendor"), "r") as f:
				vendor = f.read().strip()
		except:
			pass

		try:
			with open(os.path.join(block_dev, "device", "model"), "r") as f:
				model = f.read().strip()
		except:
			pass

		if not vendor and not model:
			continue

		try:
			with open(os.path.join(block_dev, "size"), "r") as f:
				_size = f.read().strip()

			size = common.size_human_readable(int(_size) * 512)
		except:
			pass

		disks.append("{} {} {}".format(vendor, model, size))

	if disks:
		response["hardware"].append({Klanguage().to_ts(1016) : disks})

def get_pci_info(response):
	graphics = []
	nics = []
	sounds = []

	for pci_dev in file_op.listdir("/sys/bus/pci/devices"):
		vendor = ""
		device = ""

		try:
			with open(os.path.join(pci_dev, "class"), "r") as f:
				_class = f.read()

			_class = int(_class, 16) >> 8
			if _class == 0x0300 or _class == 0x0301 or _class == 0x0380:
				category = graphics
			elif _class == 0x0200:
				category = nics
			elif _class == 0x0401 or _class == 0x0403:
				category = sounds
			else:
				continue
		except:
			continue

		try:
			with open(os.path.join(pci_dev, "vendor"), "r") as f:
				vendor = f.read().strip()
		except:
			continue

		try:
			with open(os.path.join(pci_dev, "device"), "r") as f:
				device = f.read().strip()
		except:
			pass

		category.append(get_pci_string(vendor, device))

	if graphics:
		response["hardware"].append({Klanguage().to_ts(1013) : graphics})
	if nics:
		response["hardware"].append({Klanguage().to_ts(1012) : nics})
	if sounds:
		response["hardware"].append({Klanguage().to_ts(1029) : sounds})

'''
motherboard
	cpu
	System Memory
	BIOS
	Host bridge
		PCI bridge
			VGA compatible controller
		VGA compatible controller
		USB controller
		Communication controller
		USB controller
		Audio device
		PCI bridge
			Unassigned class
		PCI bridge
			Wireless interface
		PCI bridge
		PCI bridge
			Ethernet interface
		USB controller
		ISA bridge
		SATA controller
		SMBus
	storage
		disk
	storage
		cdrom

battery
'''

def get_mem_disk_info(response):
	#name	STATS   USED	MOUNT   FILESYSTEM
	for item in psutil.disk_partitions():
		device, mountpoint, fstype, opts = item

		try:
			total, used, free, percent = psutil.disk_usage(mountpoint)

			response["disk"][device] = percent
		except Exception:
			pass

	mem = psutil.virtual_memory()
	response["ram"]["total"] = common.size_human_readable(mem[0])
	response["ram"]["used"] = common.size_human_readable(mem[3])

def get_vuls(response):
	vuls = Kdatabase().get_obj("vuls")

	response["vuls"] = len(vuls["items"].keys())

def run(payload, socket):

	response = {
		"cmd_id" : payload["cmd_id"],
		"session_id" : payload["args"]["session_id"],
		"hardware" : [],
		"system_info" : [],
		"usage" : {
			"cpu" : [],
			"memory" : 0,
			"disk" : {
				"read" : [],
				"write" : []
			},
			"network" : {
				"tx" : [],
				"rx" : []
			}
		},
		"disk" : {},
		"ram" : {
			"total" : 0,
			"used" : 0
		},
		"garbage" : [],
		"vuls" : 0,
		"error" : ""
	}

	get_hardware_info(response)
	get_system_info(response)
	get_mem_disk_info(response)
	get_vuls(response)

	monitor_second = Kdatabase().get_monitor_second()

	response["usage"]["cpu"] = common.extend_at_front(monitor_second["cpu"], 71, 0)
	try:
		response["usage"]["memory"] = monitor_second["memory"][-1]
	except:
		response["usage"]["memory"] = 0.0
	response["usage"]["disk"]["read"] = common.extend_at_front(monitor_second["disk_io"]["read"], 71, 0)
	response["usage"]["disk"]["write"] = common.extend_at_front(monitor_second["disk_io"]["write"], 71, 0)
	response["usage"]["network"]["tx"] = common.extend_at_front(monitor_second["net_io"]["tx"], 71, 0)
	response["usage"]["network"]["rx"] = common.extend_at_front(monitor_second["net_io"]["rx"], 71, 0)

	socket.response(response)
