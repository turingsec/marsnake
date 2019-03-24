from utils import common
import os
import time
import start
import signal

main_proc = None

def start_python_main():
	global main_proc

	signal.signal(signal.SIGTERM, signal_term_handler)

	main_proc = common.fork_process(start.python_main, (None, ))
	main_proc.daemon = True
	main_proc.start()
	#main_proc.join()

def signal_term_handler(signal, frame):
	global main_proc
	
	if main_proc:
		while main_proc.is_alive():
			main_proc.terminate()
			time.sleep(1)
			
	os._exit(1)

def dprint(msg):
	print(msg)

def check_and_update():
	os.chdir(common.get_work_dir())
	
	data, success, retcode = common.exec_command(['git', 'pull', '-f'])

	if success and not 'up-to-date' in data.lower():
		dprint("[Init Info] go update")
		return True
	else:
		dprint("[Init Info] no update " + str(data))
		return False

def initAll():
	global main_proc

	common.set_work_dir()
	dprint('[Init Info] work dir set')

	if common.is_linux():
		start_python_main()

	waiting_proc_exit = False
	next_update_time = int(time.time()) + 30
	
	while True:
		if not main_proc.is_alive():
			dprint("[Init Info] marsnake terminated")
			break

		if not waiting_proc_exit and int(time.time()) > next_update_time:
			try:
				if check_and_update():
					main_proc.terminate()
					waiting_proc_exit = True
					continue

				next_update_time = int(time.time()) + 60 * 60 * 3 # wait for 3 hour
			except Exception as e:
				dprint("[Init Error]", str(e))

		time.sleep(10)

if __name__ == '__main__':
	initAll()