from utils import common
import os
import time

def dprint(msg):
	print(msg)

def stop_marsnake(proc):
	proc.terminate()

def check_and_update(proc):
	os.chdir(common.get_work_dir())
	
	data, success, retcode = common.exec_command(['git', 'pull', '-f'])
	if success and not 'up-to-date' in data.lower():
		print("go update")
		stop_marsnake(proc)
		return True
	else:
		print("no update " + str(data))
		return False

def initAll():
	common.set_work_dir()
	dprint('[Init Info] work dir set')

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

	waiting_proc_exit = False
	next_update_time = int(time.time()) + 30
	
	while True:
		if not main_proc.is_alive():
			dprint("[Init Info] marsnake terminated")
			break

		if not waiting_proc_exit and int(time.time()) > next_update_time:
			try:
				if check_and_update(main_proc):
					waiting_proc_exit = True
					continue

				next_update_time = int(time.time()) + 60 * 60 * 6 # wait for 6 hour
			except Exception as e:
				dprint("[Init Error]", str(e))

		time.sleep(10)

if __name__ == '__main__':
	initAll()