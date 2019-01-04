from utils.singleton import singleton
from utils import common, file_op, time_op
from core.ueba.classifier.malware_from_usb2drive import malware_from_usb2drive
from core.ueba.classifier.malware_detect import malware_detect
from core.ueba.classifier.ssh_attempts import ssh_attempts
from core.ueba.classifier.proc_connect_malicious_ip import proc_connect_malicious_ip
from core.ueba.classifier.backdoor_detect import backdoor_detect
from core.ueba import macro
import psutil

@singleton
class KUEBA_event():
	def __init__(self):
		self.events = {
			macro.EVENTS["USB_PLUGGED"] : [],
			macro.EVENTS["SSH_FAILED"] : [],
			macro.EVENTS["BACKDOOR"] : []
		}

		self.classifiers = [malware_from_usb2drive(),
							malware_detect(),
							ssh_attempts(),
							proc_connect_malicious_ip(),
							backdoor_detect()]

	def on_usb_plugged(self, kind, info):
		self.events[macro.EVENTS["USB_PLUGGED"]].append({
			"now" : time_op.now(),
			"info" : info
		})

	def on_usb_unplugged(self, info):
		pass

	def on_malware_detect(self, pathname, report):
		usb_plugged = self.events[macro.EVENTS["USB_PLUGGED"]]
		sha256 = file_op.sha256_checksum(pathname)
		#mnt = file_op.find_mount_point(pathname)

		for value in usb_plugged:
			mnt = value["info"]["mnt"]

			for classifier in self.classifiers:
				classifier.on_usb_malware_detect(pathname, report)

	def ssh_login_failed(self, account, ip, ts):
		ssh_failed = self.events[macro.EVENTS["SSH_FAILED"]]
		found = False

		for info in ssh_failed:
			if info["ip"] == ip:
				info["count"] += 1
				info["last_ts"] = ts
				if account not in info["account"]:
					info["account"].append(account)
				found = True
				break

		if not found:
			ssh_failed.append({
				"ip" : ip,
				"account" : [account],
				"count" : 1,
				"first_ts" : ts,
				"last_ts" : ts
			})

	def ssh_login_success(self, account, ip, ts):
		ssh_failed = self.events[macro.EVENTS["SSH_FAILED"]]
		last_24hour_ts = time_op.get_last_n_hour(24)
		failed_info = []

		for info in ssh_failed:
			if info["last_ts"] >= last_24hour_ts:
				failed_info.append(info)

		if len(failed_info) > 0:
			for info in ssh_failed:
				if info["ip"] == ip and account in info["account"]:
					for classifier in self.classifiers:
						classifier.on_ssh_attempts(failed_info, info, account, ts)

					break

	def malicious_ip_detect(self, pid, ip, ip_report):
		for classifier in self.classifiers:
			classifier.on_proc_connect_malicious_ip(pid, ip, ip_report)

	def backdoor_detect(self, pid, ppid):
		record = self.events[macro.EVENTS["BACKDOOR"]]

		if pid in record and ppid in record:
			return

		record.extend([pid, ppid])

		for classifier in self.classifiers:
			classifier.on_backdoor_detect(pid, ppid)
