from core.cleaner import Kcleaner
from core.db import Kdatabase
from core.event import Kevent
from core.profile_reader import KProfile
from utils import time_op
import time

def run(payload, socket):
	cleaner = Kdatabase().get_obj("cleaner")
	Kcleaner().load_jsons()
	
	while True:
		if Kevent().is_terminate():
			print("cleaner thread terminate")
			break

		now = time_op.now()
		settings = KProfile().get_web_strategy()

		if settings:
			if now > cleaner["lasttime"] + settings["garbage"]["period"]:
				with Kcleaner().get_lock():
					cleaner["kinds"] = Kcleaner().scan()
					cleaner["lasttime"] = now
					
					if settings["garbage"]["auto_clean"]:
						for kind, info in cleaner["kinds"].items():
							if "autoclean" in info and info["autoclean"]:
								for i in list(info["items"].keys()):
									Kcleaner().clean_option(info, i, cleaner["record"])

				Kdatabase().dump("cleaner")

		time.sleep(5)
