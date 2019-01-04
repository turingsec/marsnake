from core.language import Klanguage
from core.baseline import macro
from core.db import Kdatabase
from utils import common, time_op
import re, os, platform, psutil

class system():
	def __init__(self):
		pass

	def do(self, target_risk_id):
		if common.is_linux():
			self.security_info(target_risk_id)

	def security_info(self, target_risk_id):
		baseline = Kdatabase().get_obj('baseline')

		selinux = self.check_selinux()
		smep = self.is_smep_enable()
		aslr = self.is_aslr_enable()
		nx = self.cpu_nx_support()

		if selinux[1] == macro.BASELINE_LEVEL["LOW"] or selinux[1] == macro.BASELINE_LEVEL["MEDIUM"]:
			if macro.BASELINE_ITEM["SYS_SELINUX"] in baseline["risks"]:
				baseline["risks"][macro.BASELINE_ITEM["SYS_SELINUX"]]["last_ts"] = time_op.now()
				baseline["risks"][macro.BASELINE_ITEM["SYS_SELINUX"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
			else:
				baseline["risks"][macro.BASELINE_ITEM["SYS_SELINUX"]] = {
					"name": "{} {}".format(Klanguage().to_ts(1125), selinux[0]),
					"level": selinux[1],
					"stage": macro.BASELINE_STAGE["UNRESOLVED"],
					"kind": macro.BASELINE_KIND["SYSTEM"],
					"extra": None,
					"ts": time_op.now(),
					"last_ts": time_op.now(),
					"handle_ts": None,
					"solution": selinux[2]
				}
		else:
			if target_risk_id == macro.BASELINE_ITEM["SYS_SELINUX"]:
				if macro.BASELINE_ITEM["SYS_SELINUX"] in baseline["risks"]:
					baseline["risks"][macro.BASELINE_ITEM["SYS_SELINUX"]]["handle_ts"] = time_op.now()
					baseline["risks"][macro.BASELINE_ITEM["SYS_SELINUX"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]

		if smep[1] == macro.BASELINE_LEVEL["LOW"]:
			if macro.BASELINE_ITEM["SYS_SMEP"] in baseline["risks"]:
				baseline["risks"][macro.BASELINE_ITEM["SYS_SMEP"]]["last_ts"] = time_op.now()
				baseline["risks"][macro.BASELINE_ITEM["SYS_SMEP"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
			else:
				baseline["risks"][macro.BASELINE_ITEM["SYS_SMEP"]] = {
					"name": "{} {}".format(Klanguage().to_ts(1126), Klanguage().to_ts(smep[0])),
					"level": smep[1],
					"stage": macro.BASELINE_STAGE["UNRESOLVED"],
					"kind": macro.BASELINE_KIND["SYSTEM"],
					"extra": None,
					"ts": time_op.now(),
					"last_ts": time_op.now(),
					"handle_ts": None,
					"solution": smep[2]
				}
		else:
			if target_risk_id == macro.BASELINE_ITEM["SYS_SMEP"]:
				if macro.BASELINE_ITEM["SYS_SMEP"] in baseline["risks"]:
					baseline["risks"][macro.BASELINE_ITEM["SYS_SMEP"]]["handle_ts"] = time_op.now()
					baseline["risks"][macro.BASELINE_ITEM["SYS_SMEP"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]

		if aslr[1] == macro.BASELINE_LEVEL["LOW"] or aslr[1] == macro.BASELINE_LEVEL["MEDIUM"]:
			if macro.BASELINE_ITEM["SYS_ASLR"] in baseline["risks"]:
				baseline["risks"][macro.BASELINE_ITEM["SYS_ASLR"]]["last_ts"] = time_op.now()
				baseline["risks"][macro.BASELINE_ITEM["SYS_ASLR"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
			else:
				baseline["risks"][macro.BASELINE_ITEM["SYS_ASLR"]] = {
					"name": "{} {}".format(Klanguage().to_ts(1127), aslr[0]),
					"level": aslr[1],
					"stage": macro.BASELINE_STAGE["UNRESOLVED"],
					"kind": macro.BASELINE_KIND["SYSTEM"],
					"extra": None,
					"ts": time_op.now(),
					"last_ts": time_op.now(),
					"handle_ts": None,
					"solution": aslr[2]
				}
		else:
			if target_risk_id == macro.BASELINE_ITEM["SYS_ASLR"]:
				if macro.BASELINE_ITEM["SYS_ASLR"] in baseline["risks"]:
					baseline["risks"][macro.BASELINE_ITEM["SYS_ASLR"]]["handle_ts"] = time_op.now()
					baseline["risks"][macro.BASELINE_ITEM["SYS_ASLR"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]

		if nx[1] == macro.BASELINE_LEVEL["LOW"]:
			if macro.BASELINE_ITEM["SYS_CPU_NX"] in baseline["risks"]:
				baseline["risks"][macro.BASELINE_ITEM["SYS_CPU_NX"]]["last_ts"] = time_op.now()
				baseline["risks"][macro.BASELINE_ITEM["SYS_CPU_NX"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
			else:
				baseline["risks"][macro.BASELINE_ITEM["SYS_CPU_NX"]] = {
					"name": "{} {}".format(Klanguage().to_ts(1128), nx[0]),
					"level": nx[1],
					"stage": macro.BASELINE_STAGE["UNRESOLVED"],
					"kind": macro.BASELINE_KIND["SYSTEM"],
					"extra": None,
					"ts": time_op.now(),
					"last_ts": time_op.now(),
					"handle_ts": None,
					"solution": nx[2]
				}
		else:
			if target_risk_id == macro.BASELINE_ITEM["SYS_CPU_NX"]:
				if macro.BASELINE_ITEM["SYS_CPU_NX"] in baseline["risks"]:
					baseline["risks"][macro.BASELINE_ITEM["SYS_CPU_NX"]]["handle_ts"] = time_op.now()
					baseline["risks"][macro.BASELINE_ITEM["SYS_CPU_NX"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]

	def check_selinux(self):
		selinux_config = "/etc/selinux/config"
		selinux_root = ["/sys/fs/selinux", "/selinux"]
		mode = ["disabled", "permissive", "enforcing"]
		level = [macro.BASELINE_LEVEL["MEDIUM"], macro.BASELINE_LEVEL["LOW"], macro.BASELINE_LEVEL["SECURITY"]]
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

	def is_smep_enable(self):
		suggest = Klanguage().to_ts(1197)

		if os.path.exists("/proc/cpuinfo"):
			with open("/proc/cpuinfo") as f:
				if "smep" in f.read():
					return Klanguage().to_ts(1120), macro.BASELINE_LEVEL["SECURITY"], suggest

		return Klanguage().to_ts(1121), macro.BASELINE_LEVEL["LOW"], suggest

	def is_aslr_enable(self):
		status = [Klanguage().to_ts(1192), Klanguage().to_ts(1193), Klanguage().to_ts(1194)]
		level = [macro.BASELINE_LEVEL["MEDIUM"], macro.BASELINE_LEVEL["LOW"], macro.BASELINE_LEVEL["SECURITY"]]
		suggest_0 = Klanguage().to_ts(1195)
		suggest = [suggest_0, suggest_0, Klanguage().to_ts(1196)]

		if os.path.exists("/proc/sys/kernel/randomize_va_space"):
			with open("/proc/sys/kernel/randomize_va_space") as f:
				v = f.read().strip()

				if v.isdigit():
					if int(v) in [0, 1, 2]:
						return status[int(v)], level[int(v)], suggest[int(v)]

		return status[0], level[0], suggest[0]

	def cpu_nx_support(self):
		suggest = Klanguage().to_ts(1185)

		try:
			data = file_op.cat("/proc/cpuinfo", "r")

			if data:
				flags, num = common.grep(data, r"flags\s*:\s(.*)")
				nx, num = common.grep(flags, r"nx")

			if nx == "nx":
				return Klanguage().to_ts(1120), macro.BASELINE_LEVEL["SECURITY"], suggest

		except Exception as e:
			pass

		return Klanguage().to_ts(1121), macro.BASELINE_LEVEL["LOW"], suggest
