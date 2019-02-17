import os,sys
import update
import time
from utils import common
import multiprocessing

RESTART = 1
EXIT = 0

debug = False

def dprint(msg):
	global debug
	if debug:
		print(msg)

def initAll():
	common.set_work_dir()
	dprint('[Init Info] work dir set')

	try:
		if common.is_windows() or common.is_darwin():
			import start_with_ui

			dprint("[Init Info] starting marsnake ui..")
			main_proc = common.fork_process(start_with_ui.ui_main, ())
			main_proc.start()

		elif common.is_linux():
			import start_without_ui

			dprint("[Init Info] starting marsnake without ui..")
			main_proc = common.fork_process(start_without_ui.without_ui_main, ())
			main_proc.start()

		update_now = False
		next_update_time = int(time.time()) + 30

		while True:
			if not main_proc.is_alive():
				dprint("[Init Info] marsnake terminated")
				break

			if not update_now and int(time.time()) > next_update_time:
				try:
					if update.check_and_update(main_proc):
						update_now = True
						continue

					next_update_time = int(time.time()) + 60 * 60 * 6 # wait for 6 hour
				except Exception as e:
					dprint("[Init Error]", str(e))

			time.sleep(10)

	except Exception as e:
		dprint('[Init Info] start marsnake failed with ' + str(e))

	return 0

if __name__ == '__main__':
	initAll()
