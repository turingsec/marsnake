from core.vuls import Kvuls
from core.db import Kdatabase
from core.event import Kevent
from utils import common, lib, time_op
import time

def run(payload, socket):
	if common.is_linux():
		vuls = Kdatabase().get_obj("vuls")

		while True:
			if Kevent().is_terminate():
				print("vulscan thread terminate")
				break

			now = time_op.now()
			settings = Kdatabase().get_obj('strategy')

			if settings:
				if now > vuls["lasttime"] + settings["vuls"]["period"]:
					with Kvuls().get_lock():
						Kvuls().vulscan()
						vuls["lasttime"] = now

						if settings["vuls"]["auto_repair"]:
								if common.is_program_running("apt-get") or common.is_program_running("yum"):
									pass
								else:
									if lib.check_root():
										for package in list(vuls["items"]):
											Kvuls().repair(package)

					Kdatabase().dump("vuls")

			time.sleep(5)
