import core.security_audit_implement as audit_implement
from core.event import Kevent
from core.db import Kdatabase
from config import constant
from utils import common, time_op
import time

def run(payload, socket):
	if common.is_linux():
		data = {
			"kernel" : [],
			"authentication" : [],
			"feature" : [],
		}

		audit = Kdatabase().get_obj('audit')

		while True:
			if Kevent().is_terminate():
				print("security audit thread terminate")
				break

			# reset data
			data['kernel'] = []
			data['authentication'] = []
			data['feature'] = []
			data['statistic'] = {
				"critical": 0,
				"warning": 0
			}

			now = time_op.now()

			if now > audit["lasttime"] + constant.AUDIT_SCAN_PERIOD:

				#check_upgradable_packages(data)
				audit_implement.kernel_available_version(data)
				audit_implement.enum_kernel_modules(data)
				audit_implement.check_magickey_configuration(data)
				audit_implement.check_need_reboot(data)
				audit_implement.check_coredump_config(data)
				#check_kdump_config(data)
				#kernel_default_limits(data)

				audit_implement.security_info(data)

				audit_implement.get_useradd_list(data)
				audit_implement.logged_user(data)
				audit_implement.check_sudoers_file(data)
				audit_implement.login_defs_policy(data)

				audit['feature'] = data['feature']
				audit['authentication'] = data['authentication']
				audit['kernel'] = data['kernel']
				audit['statistic'] = data['statistic']
				audit["lasttime"] = now

				Kdatabase().dump('audit')

			time.sleep(5)
