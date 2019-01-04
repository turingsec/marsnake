class base_classifier():
	def __init__(self):
		pass

	def on_usb_malware_detect(self, info):
		pass

	def on_ssh_attempts(self, failed_info, info, account, ts):
		pass

	def on_proc_connect_malicious_ip(self, pid, ip, ip_report):
		pass

	def on_backdoor_detect(self, pid, ppid):
		pass
		
	def publish(self, *args, **kwargs):
		pass
