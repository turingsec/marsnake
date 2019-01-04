import os,sys
import update
import time
from utils import common
import multiprocessing

RESTART = 1
EXIT = 0

if os.name == 'nt':
	debug = True
else:
	debug = False

def dprint(msg):
	global debug
	if debug:
		print(msg)

def load_extra_library():
	pass

def initAll(test = True):
	common.set_work_dir()
	dprint('[Init Info] work dir set')
	try:
		# if you want to start this py python.exe,set module to None.
		if not test: 
			load_extra_library()
			dprint('[Init Info] extra libraries loaded')

	except Exception as e:
		dprint('[Init Error] set path failed: ' + str(e))
		return -1

	if common.is_windows():
		multiprocessing.freeze_support()

	try:
		if common.is_windows() or common.is_darwin():
			import start_with_ui

			dprint("[Init Info] starting marsnake ui..")
			main_proc = common.fork_process(start_with_ui.ui_main, ())
			main_proc.start()

		elif common.is_linux():
			import start_without_ui

			if hasattr(sys, "argv"):
				for each in sys.argv:
					if each == "--no-updater":
						start_without_ui.login()
						return 0

			dprint("[Init Info] starting marsnake without ui..")
			main_proc = common.fork_process(start_without_ui.without_ui_main, ())
			main_proc.start()

		update_now = False
		next_update_time = int(time.time()) + 5

		while True:
			if not main_proc.is_alive():
				dprint("[Init Info] marsnake terminated")
				break

			if not update_now and int(time.time()) > next_update_time:
				try:
					if update.check_and_update(main_proc):
						update_now = True
						continue

					next_update_time = int(time.time()) + 30 * 60 # wait for 1 hour
				except Exception as e:
					dprint("[Init Error]", str(e))

			time.sleep(1)

		# update_now will force kill us.
		# if you need to do other things,
		# Do it before this function !!!
		if update_now:
			update.update_now()
	except Exception as e:
		dprint('[Init Info] start marsnake failed with ' + str(e))

	return 0

if __name__ == '__main__':
	initAll()
