from core.ueba.events import KUEBA_event
from core.ueba.features.identity import identity_feature

class ssh_logon(identity_feature):
	def __init__(self):
		pass

	def ssh_login_failed(self, account, ip, ts):
		KUEBA_event().ssh_login_failed(account, ip, ts)

	def ssh_login_success(self, account, ip, ts):
		KUEBA_event().ssh_login_success(account, ip, ts)