from utils import common
import os
import time
import start

main_proc = None

def start_python_main():
	global main_proc

	main_proc = common.fork_process(start.python_main, (None, ))
	main_proc.daemon = True
	main_proc.start()
	main_proc.join()

def terminate_main():
	global main_proc
	
	if main_proc:
		while main_proc.is_alive():
			main_proc.terminate()
			time.sleep(1)

def signal_term_handler(signal, frame):
	terminate_main()
	os._exit(1)

def without_ui_main():
	import signal
	signal.signal(signal.SIGTERM, signal_term_handler)

	start_python_main()

if __name__ == '__main__':
	without_ui_main()