class base_feature():
	def __init__(self):
		pass

	def on_pe_captured(self, pe):
		pass

	def on_elf_captured(self, elf):
		pass

	def on_http_captured(self, http):
		pass

	def on_dns_captured(self, dns):
		pass

	def on_file_created_captured(self, pathname):
		pass

	def on_file_modified_captured(self, pathname):
		pass

	def on_usb_plugged(self, info):
		pass

	def on_usb_unplugged(self, info):
		pass

	def ssh_login_failed(self, account, ip, ts):
		pass

	def ssh_login_success(self, account, ip, ts):
		pass

	def remote_ip_detect(self, pid, ip):
		pass

	def backdoor_detect(self, pid, ppid):
		pass
