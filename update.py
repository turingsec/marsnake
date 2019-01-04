import urllib.request
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

CHECK_UPDATE_ADDRESS = "/client/check_update"

Update_file_path = None
__debug = False

def dprint(msg):
	global __debug
	if __debug:
		print(msg)

#.Marsnake
#	db
#	logs
#	info.conf
#	update
#		update.zip
# Marsnake
#	baselib.zip
#	winpty-agent.exe
#	resource1
#		config
#		library.zip
#		lib
#			misc.dll
#	resource2

def check_if_has_update():
	global CHECK_UPDATE_ADDRESS

	now_version = '0'

	try:
		with open(os.path.join(common.get_work_dir(), "config", "version"), "r") as f:
			now_version = f.read().strip('\n')

	except Exception as e:
		dprint("[Updater Error] read version failed: " + str(e))
		now_version = '0'

	dprint("[Updater Info] now version: " + str(now_version))

	req = None
	dprint("[Updater Info] {}".format(KProfile().read_key("update_server") + CHECK_UPDATE_ADDRESS))
	for i in range(3):
		try:
			req = urllib.request.urlopen(KProfile().read_key("update_server") + CHECK_UPDATE_ADDRESS,
					data = b"os=" + platform.system().encode('ascii')
							+ b"&version=" + now_version.encode("ascii")
							+ b"&arch=" + platform.machine().encode('ascii'),
						timeout = 3)
		except Exception as e:
			dprint("[Updater Info] check new version failed: " + str(e))
		else:
			break

	if not req or req.getcode() != 200:
		dprint("[Updater Info] get version failed")
		return None

	dprint("[Updater Info] check new version request done")

	try:
		data = json.loads(req.read())
	except Exception as e:
		dprint("[Updater Error] json loads failed: " + str(e))
		return None

	dprint("[Updater Info] check new version info: " + str(data))

	return data

def get_update_file_online(update_json):
	global Update_file_path
	dprint("[Updater Info] download new version file")

	new_version = None

	for i in range(3):
		try:
			new_version = urllib.request.urlopen(KProfile().read_key("update_server") + update_json['url'], timeout = 3)
		except Exception as e:
			dprint("[Updater Error] get update file failed: " + str(e))
		else:
			break

	if not new_version or new_version.getcode() != 200:
		dprint("[Updater Error] update file download failed")
		return None

	dprint("[Updater Info] download new version file done")

	new_version_data = new_version.read()
	if len(new_version_data) == 0:
		dprint("[Updater Error] update file empty data")
		return None

	try:
		with open(Update_file_path, 'wb') as fp:
			fp.write(new_version_data)

	except Exception as e:
		dprint("[Updater Error] can't store update file")
		return None
		
	dprint("[Updater Info] save update file done!")
	return True

def update_now():
	global Update_file_path
	if os.name == 'nt':
		subprocess.Popen([Update_file_path, '/S'])
	else:
		st = os.stat(Update_file_path)
		os.chmod(Update_file_path, st.st_mode | 64)
		subprocess.Popen([Update_file_path, '-s', '-p', str(os.getpid())])

def stop_marsnake(proc):
	dprint("[Updater Info] stop marsnake")

	proc.terminate()

def check_and_update(proc):
	global Update_file_path
	dprint('[Updater Info] updater start')
	if not Update_file_path:
		if os.name == 'nt':
			Update_file_path = os.path.join(common.get_data_location(),
				"update.exe")
		else:
			Update_file_path = os.path.join(common.get_data_location(),
				"updater")

	update_json = check_if_has_update()
	if update_json and 'updatable' in update_json and update_json['updatable'] == True:
		ret = get_update_file_online(update_json)
		if ret:
			stop_marsnake(proc)
			return 1
	return 0
