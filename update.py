import json
import tempfile
import os
import sys
import platform
import subprocess
import time
import shutil
from utils import common
from core.profile_reader import KProfile

__debug = False

def dprint(msg):
	global __debug
	if __debug:
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

