from core.language import Klanguage
from core.baseline import macro
from core.db import Kdatabase
from utils import common, file_op, time_op
import re, os, platform, psutil

class authentication():
	def __init__(self):
		self.uid_min = 1000
		self.uid_max = 60000

	def do(self, target_risk_id):
		if common.is_linux():
			self.login_defs_policy(target_risk_id)
			self.check_sudoers_file(target_risk_id)

	def login_defs_policy(self, target_risk_id):
		baseline = Kdatabase().get_obj('baseline')
		data = file_op.cat("/etc/login.defs", "r")

		if data:
			lines = data.split("\n")

			for line in lines:
				if line:
					# UMASK is the default umask value for pam_umask and is used by
					# useradd and newusers to set the mode of the new home directories.
					tmp, num = common.grep(line, r"^UMASK\s*(\S+)")
					if num:
						if tmp == "077" or tmp == "027" or tmp == "0077" or tmp == "0027":
							if target_risk_id == macro.BASELINE_ITEM["AU_UMASK"]:
								if macro.BASELINE_ITEM["AU_UMASK"] in baseline["risks"]:
									baseline["risks"][macro.BASELINE_ITEM["AU_UMASK"]]["handle_ts"] = time_op.now()
									baseline["risks"][macro.BASELINE_ITEM["AU_UMASK"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]
						else:
							if macro.BASELINE_ITEM["AU_UMASK"] in baseline["risks"]:
								baseline["risks"][macro.BASELINE_ITEM["AU_UMASK"]]["last_ts"] = time_op.now()
								baseline["risks"][macro.BASELINE_ITEM["AU_UMASK"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
							else:
								baseline["risks"][macro.BASELINE_ITEM["AU_UMASK"]] = {
									"name": Klanguage().to_ts(1178),
									"level": macro.BASELINE_LEVEL["MEDIUM"],
									"stage": macro.BASELINE_STAGE["UNRESOLVED"],
									"kind": macro.BASELINE_KIND["AUTHENTICATION"],
									"extra": tmp,
									"ts": time_op.now(),
									"last_ts": time_op.now(),
									"handle_ts": None,
									"solution": Klanguage().to_ts(1177)
								}

						continue

					# Algorithm will be used for encrypting password
					tmp, num = common.grep(line, r"^ENCRYPT_METHOD\s*(\S+)")
					if num:
						if tmp == "SHA512":
							if target_risk_id == macro.BASELINE_ITEM["AU_ENCRYPT_METHOD"]:
								if macro.BASELINE_ITEM["AU_ENCRYPT_METHOD"] in baseline["risks"]:
									baseline["risks"][macro.BASELINE_ITEM["AU_ENCRYPT_METHOD"]]["handle_ts"] = time_op.now()
									baseline["risks"][macro.BASELINE_ITEM["AU_ENCRYPT_METHOD"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]
						else:
							if macro.BASELINE_ITEM["AU_ENCRYPT_METHOD"] in baseline["risks"]:
								baseline["risks"][macro.BASELINE_ITEM["AU_ENCRYPT_METHOD"]]["last_ts"] = time_op.now()
								baseline["risks"][macro.BASELINE_ITEM["AU_ENCRYPT_METHOD"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
							else:
								baseline["risks"][macro.BASELINE_ITEM["AU_ENCRYPT_METHOD"]] = {
									"name": Klanguage().to_ts(1175),
									"level": macro.BASELINE_LEVEL["LOW"],
									"stage": macro.BASELINE_STAGE["UNRESOLVED"],
									"kind": macro.BASELINE_KIND["AUTHENTICATION"],
									"extra": tmp,
									"ts": time_op.now(),
									"last_ts": time_op.now(),
									"handle_ts": None,
									"solution": Klanguage().to_ts(1174)
								}

						continue

					#Password aging controls
					#Maximum number of days a password may be used
					tmp, num = common.grep(line, r"^PASS_MAX_DAYS\s*(\d+)")
					if num:
						if tmp == "99999":
							if macro.BASELINE_ITEM["AU_PASS_MAX_DAYS"] in baseline["risks"]:
								baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MAX_DAYS"]]["last_ts"] = time_op.now()
								baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MAX_DAYS"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
							else:
								baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MAX_DAYS"]] = {
									"name": Klanguage().to_ts(1175),
									"level": macro.BASELINE_LEVEL["LOW"],
									"stage": macro.BASELINE_STAGE["UNRESOLVED"],
									"kind": macro.BASELINE_KIND["AUTHENTICATION"],
									"extra": tmp,
									"ts": time_op.now(),
									"last_ts": time_op.now(),
									"handle_ts": None,
									"solution": Klanguage().to_ts(1170)
								}
						else:
							if target_risk_id == macro.BASELINE_ITEM["AU_PASS_MAX_DAYS"]:
								if macro.BASELINE_ITEM["AU_PASS_MAX_DAYS"] in baseline["risks"]:
									baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MAX_DAYS"]]["handle_ts"] = time_op.now()
									baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MAX_DAYS"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]

						continue

					#Minimum number of days allowed between password changes.
					tmp, num = common.grep(line, r"^PASS_MIN_DAYS\s*(\d+)")
					if num:
						if tmp == "0":
							if macro.BASELINE_ITEM["AU_PASS_MIN_DAYS"] in baseline["risks"]:
								baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MIN_DAYS"]]["last_ts"] = time_op.now()
								baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MIN_DAYS"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
							else:
								baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MIN_DAYS"]] = {
									"name": Klanguage().to_ts(1175),
									"level": macro.BASELINE_LEVEL["LOW"],
									"stage": macro.BASELINE_STAGE["UNRESOLVED"],
									"kind": macro.BASELINE_KIND["AUTHENTICATION"],
									"extra": tmp,
									"ts": time_op.now(),
									"last_ts": time_op.now(),
									"handle_ts": None,
									"solution": Klanguage().to_ts(1167)
								}
						else:
							if target_risk_id == macro.BASELINE_ITEM["AU_PASS_MIN_DAYS"]:
								if macro.BASELINE_ITEM["AU_PASS_MIN_DAYS"] in baseline["risks"]:
									baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MIN_DAYS"]]["handle_ts"] = time_op.now()
									baseline["risks"][macro.BASELINE_ITEM["AU_PASS_MIN_DAYS"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]

						continue

					#Min/max values for automatic uid selection in useradd
					tmp, num = common.grep(line, r"^UID_MIN\s*(\d+)")
					if num:
						self.uid_min = tmp
						continue

					#Min/max values for automatic uid selection in useradd
					tmp, num = common.grep(line, r"^UID_MAX\s*(\d+)")
					if num:
						self.uid_max = tmp
						continue

	def check_sudoers_file(self, target_risk_id):
		from utils import lib

		baseline = Kdatabase().get_obj('baseline')
		sudoers = ["/etc/sudoers", "/usr/local/etc/sudoers", "/usr/pkg/etc/sudoers"]

		for path in sudoers:
			if os.path.exists(path):
				_stat = os.lstat(path)
				permissions = lib.permissions_to_unix_name(_stat.st_mode)

				if permissions == "-r--r-----":
					if target_risk_id == macro.BASELINE_ITEM["AU_SUDOERS_PERM"]:
						if macro.BASELINE_ITEM["AU_SUDOERS_PERM"] in baseline["risks"]:
							baseline["risks"][macro.BASELINE_ITEM["AU_SUDOERS_PERM"]]["handle_ts"] = time_op.now()
							baseline["risks"][macro.BASELINE_ITEM["AU_SUDOERS_PERM"]]["stage"] = macro.BASELINE_STAGE["VERIFIED"]
				elif permissions == "-rw-------" or permissions == "-rw-rw----":
					if macro.BASELINE_ITEM["AU_SUDOERS_PERM"] in baseline["risks"]:
						baseline["risks"][macro.BASELINE_ITEM["AU_SUDOERS_PERM"]]["last_ts"] = time_op.now()
						baseline["risks"][macro.BASELINE_ITEM["AU_SUDOERS_PERM"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
					else:
						baseline["risks"][macro.BASELINE_ITEM["AU_SUDOERS_PERM"]] = {
							"name": Klanguage().to_ts(1175),
							"level": macro.BASELINE_LEVEL["MEDIUM"],
							"stage": macro.BASELINE_STAGE["UNRESOLVED"],
							"kind": macro.BASELINE_KIND["AUTHENTICATION"],
							"extra": permissions,
							"ts": time_op.now(),
							"last_ts": time_op.now(),
							"handle_ts": None,
							"solution": Klanguage().to_ts(1182)
						}
				else:
					if macro.BASELINE_ITEM["AU_SUDOERS_PERM"] in baseline["risks"]:
						baseline["risks"][macro.BASELINE_ITEM["AU_SUDOERS_PERM"]]["last_ts"] = time_op.now()
						baseline["risks"][macro.BASELINE_ITEM["AU_SUDOERS_PERM"]]["stage"] = macro.BASELINE_STAGE["UNRESOLVED"]
					else:
						baseline["risks"][macro.BASELINE_ITEM["AU_SUDOERS_PERM"]] = {
							"name": Klanguage().to_ts(1175),
							"level": macro.BASELINE_LEVEL["MEDIUM"],
							"stage": macro.BASELINE_STAGE["UNRESOLVED"],
							"kind": macro.BASELINE_KIND["AUTHENTICATION"],
							"extra": permissions,
							"ts": time_op.now(),
							"last_ts": time_op.now(),
							"handle_ts": None,
							"solution": Klanguage().to_ts(1183)
						}
