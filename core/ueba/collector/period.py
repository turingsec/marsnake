from utils import common, time_op, net_op, file_op
from datetime import datetime
from core.ueba import macro
import time, os, re, psutil

class period():
	def __init__(self, ssh_login_failed, ssh_login_success, remote_ip_detect, backdoor_detect):
		self.name = "Period"

		if common.is_linux():
			self.ssh_lasttime_scan = time_op.now()
			self.backdoor_lasttime_scan = time_op.now()

			self.ssh_login_failed = ssh_login_failed
			self.ssh_login_success = ssh_login_success
			self.backdoor_detect = backdoor_detect

		self.ip_lasttime_scan = time_op.now()
		self.remote_ip_detect = remote_ip_detect
		self.ip_detected = []

	def init(self):
		return True

	def do(self):
		while(True):
			now = time_op.now()

			if common.is_linux():
				if now >= self.ssh_lasttime_scan + macro.PERIOD_SSH_SCAN:
					self.ssh_detect()
					self.ssh_lasttime_scan = now

				if now >= self.backdoor_lasttime_scan + macro.PERIOD_BACKDOOR_SCAN:
					self.malicious_backdoor_detect()
					self.backdoor_lasttime_scan = now;

			if now >= self.ip_lasttime_scan + macro.PERIOD_IP_SCAN:
				self.malicious_ip_detect()
				self.ip_lasttime_scan = now

			time.sleep(10)

	def ssh_detect(self):
		lines = []
		logfile = None

		if os.path.exists(macro.AUTH_LOG):
			logfile = macro.AUTH_LOG
		elif os.path.exists(macro.SECURE_LOG):
			logfile = macro.SECURE_LOG

		if logfile:
			lines = file_op.cat_lines(logfile, "r")
		else:
			if common.check_programs_installed("journalctl"):
				data, success, retcode = common.exec_command(['journalctl', '_COMM=sshd', '-n', '50'])

				if success:
					lines = data.split("\n")
				else:
					data, success, retcode = common.exec_command(['journalctl', '_COMM=ssh', '-n', '50'])

					if success:
						lines = data.split("\n")

		for line in lines:
			#Feb 1 16:07:41 iZj6cd9xxma2xamt72ui3qZ sshd[19864]: Failed password for root from 182.100.67.252 port 57888 ssh2
			#Feb 1 16:07:41 iZj6cd9xxma2xamt72ui3qZ sshd[19864]: Accepted password for root from 100.129.58.124 port 61745 ssh2
			s = re.search("(^.*\d+:\d+:\d+).*sshd.*Accepted password for (.*) from (.*) port.*$", line, re.I | re.M)
			f = re.search("(^.*\d+:\d+:\d+).*sshd.*Failed password for (.*) from (.*) port.*$", line, re.I | re.M)
			b = re.search("(^.*\d+:\d+:\d+).*sshguard.*Blocking (.*) for.*$", line, re.I | re.M)

			if s:
				dt = datetime.strptime(s.group(1), '%b %d %X')
				new_dt = datetime(datetime.now().year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
				ts = time_op.to_timestamp(new_dt)

				if ts > self.ssh_lasttime_scan and not net_op.is_private_ip(s.group(3)):
					self.ssh_login_success(s.group(2), s.group(3), ts)

			if f:
				dt = datetime.strptime(f.group(1), '%b %d %X')
				new_dt = datetime(datetime.now().year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
				ts = time_op.to_timestamp(new_dt)

				if ts > self.ssh_lasttime_scan and not net_op.is_private_ip(f.group(3)):
					self.ssh_login_failed(f.group(2), f.group(3), ts)

	def malicious_ip_detect(self):
		for proc in psutil.process_iter():
			try:
				connections = proc.connections(kind = "inet")
			except Exception as e:
				connections = []

			for conn in connections:
				if conn.raddr:
					remote_ip = conn.raddr[0]

					if not net_op.is_private_ip(remote_ip):
						self.remote_ip_detect(proc.pid, remote_ip)

					#if remote_ip not in self.ip_detected:
					#	self.ip_detected.append(remote_ip)

	def malicious_backdoor_detect(self):
		for proc in psutil.process_iter():
			try:
				cmdline = proc.cmdline()
				exe = proc.exe()

				if common.contain_in_string('/bin/sh', cmdline[0]) or common.contain_in_string('bash', cmdline[0]) or common.contain_in_string('/bin/bash', exe):
					parent = proc.parent()

					while parent:
						if common.contain_in_string('java', parent.cmdline()[0]):
							self.backdoor_detect(proc.pid, parent.pid)
							break

						parent = parent.parent()
			except Exception as e:
				pass
