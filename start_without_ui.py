from core.profile_reader import KProfile
from utils import common, net_op
import sys, os
import json
import time
import urllib.parse, getpass
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

	try:
		if not KProfile().read_key("username") or not KProfile().read_key("password"):
			credential = os.path.join(common.get_data_location(), ".CREDENTIALS")

			with open(credential, "rb") as f:
				username = f.readline().strip().decode()
				password = f.readline().strip().decode()

			KProfile().write_username_fullname(username, "")
			KProfile().write_password(password)

		start_python_main()
	except Exception as e:
		print("Read Credential error:", e)

if __name__ == '__main__':
	without_ui_main()