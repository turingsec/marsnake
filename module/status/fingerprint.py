from core.fingerprint import Kfingerprint
from core.db import Kdatabase
from core.event import Kevent
from core.profile_reader import KProfile
from utils import time_op
import time

def run(payload, socket):
	fingerprint = Kdatabase().get_obj("fingerprint")

	while True:
		if Kevent().is_terminate():
			print("fingerprint thread terminate")
			break

		now = time_op.now()
		settings = KProfile().get_web_strategy()
		
		if settings:
			if now > fingerprint["port"]["lasttime"] + settings["asset"]["port_scan"]:
				Kfingerprint().record_listening_port()

			if now > fingerprint["account"]["lasttime"] + settings["asset"]["account_scan"]:
				Kfingerprint().record_account()

		time.sleep(5)
