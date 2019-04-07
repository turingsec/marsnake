from utils import common, file_op, time_op
from utils.magic import Magic
from core.db import Kdatabase
from core.cybertek import KCybertek
from core.threads import Kthreads
from core.logger import Klogger
from config.constant import ISOLATION_PATH
import re
import shutil
import hashlib
import os
import psutil
import datetime
import json
import time
import stat

# Notice: if you need to change these flags,
# you need to synchronize with web front end.
OPERATION_ISOLATE = 0
OPERATION_TRUST = 1
OPERATION_UNTRUST = 2
OPERATION_DELETE = 3
OPERATION_MOVETO = 4

RESERVERED_WHEN_CLEARED_HISTORY = -1

class KvirusScanner():
	# a static dict for whitelist.used for addWhiteList funtion.
	white_list = {}

	def __init__(self):
		self.isolation_path = os.path.join(common.get_data_location(),
											   ISOLATION_PATH)
		self.searched_count = 0  # used to count
		self.current_path = ''  # used to record path where we are scanning.
		self.white_list = {}  # this dict for web front end
		self.avoid_list = []  # this list for mine.changed by scanner type.LowerCASE
		self.isNeedIgnore = False

	def detachExecutableType(self, filepath):
		""" detach file types which need to be checked \
		args:
						filepath: str
		ret :
						True or False
		"""
		ret = Magic().from_file(filepath)
		if ret[:4] == 'PE32':
			return True
		elif ret[:3] == 'ELF':
			return True
		else:
			return False

	def needAvoid(self, path):
		for avoidpath in self.avoid_list:
			if path.lower().startswith(avoidpath.lower()):
				return True

		return False

	def synchronizeProcessing(self):
		virus = Kdatabase().get_obj('virus')
		virus['lasttime'] = time_op.now()

		if self.current_path:
			virus['lastScanedPath'] = self.current_path

		if self.searched_count:
			virus['searchedCount'] = self.searched_count

		Kdatabase().dump('virus')

	def resetScanConfiguration(self):
		if not os.path.exists(self.isolation_path):
			os.mkdir(self.isolation_path)

		whitelist = Kdatabase().get_obj('virus_whitelist')
		virus = Kdatabase().get_obj('virus')

		self.white_list = whitelist
		self.avoid_list.append(self.isolation_path)

		if virus['finished']:
			self.current_path = ''
			self.searched_count = 0

			virus['lastScanedPath'] = self.current_path
			virus['searchedCount'] = self.searched_count
		else:
			self.current_path = virus['lastScanedPath']
			self.searched_count = virus['searchedCount']

			if self.current_path:
				self.isNeedIgnore = True

		virus['finished'] = 0
		virus['lasttime'] = time_op.now()

		Kdatabase().dump('virus')

	def retrieveFiles(self, root_paths):
		""" retrieve files from root_paths
		args:
						root_paths: [(path,isNeedSearchSubdir),...]
		ret:
						yield a path not in whitelist and is detachExecutableType()
		"""
		for root_path, isSearchSubdir in root_paths:
			if not os.path.exists(root_path):
				continue

			try:
				# I'm not sure which error will happend,use a try to catch.I hope to remove this try.
				# avoid link,whitelist,avoidlist
				for path, dir_list, file_list in os.walk(root_path):
					# ignore until previous path
					if self.isNeedIgnore and self.current_path:
						while not os.path.exists(self.current_path):
							self.current_path = os.path.split(self.current_path)[0]
							# os.path.split won't split root path.
							# if root path don't exist.this will loop forever.
							# it should break and start a new scan.#like "AF:\\"
							if (not os.path.exists(self.current_path) and
								self.current_path[-2:] == ':\\'):
									self.isNeedIgnore = False
									break

						if path.startswith(self.current_path):
							self.isNeedIgnore = False
						else:
							continue

					if self.needAvoid(path) or os.path.islink(path) or (path in self.white_list):
						continue

					self.current_path = path

					for filename in file_list:
						abs_path = os.path.join(path, filename)

						if abs_path in self.white_list:
							continue
						# avoid file doesn't exist after walk
						if os.path.exists(abs_path):
							if os.path.islink(abs_path) or not stat.S_ISREG(os.stat(abs_path).st_mode):
								continue
						else:
							continue

						if self.detachExecutableType(abs_path):
							yield abs_path

						self.searched_count += 1

						if self.searched_count/128 and not self.searched_count%128:
							self.synchronizeProcessing()

					# we don't need walk subdirectory
					if not isSearchSubdir:
						break
			except:
				Klogger().exception()

	def handleVirus(self, filepath, virusType=None, level=None,sha256 = None,
					newpath=None, operation=OPERATION_ISOLATE):
		"""This function is public,need to strict with args.
		args:
			filepath str  :filepath need to be handled.
			virusType=None:only for scanner.
			level=None	:only for scanner.
			sha256=None   :only for scanner.
			newpath=None  :only for moveto cmd.
			operation=OPERATION_ISOLATE :operation to do.

		return:
			if no error,return None,else,return error string.
		"""
		virus = Kdatabase().get_obj('virus')
		md5 = hashlib.md5()
		md5.update(filepath.encode('utf-8'))
		filename = md5.hexdigest()
		opsTime = '{0:%Y-%m-%d %H:%M:%S}'.format(
			datetime.datetime.now())

		if operation == OPERATION_ISOLATE:
			# check before isolate
			if not os.path.exists(filepath):
				return "handle:No such file #{}#.".format(filepath)

			description = [os.path.split(filepath)[1], file_op.md5(filepath),
						   file_op.sha1(filepath), sha256,
						   Magic().from_file(filepath), file_op.getsize(filepath)]

			ret = self.tryIsolateVirus(filepath, filename)

			if ret:
				return ret

			virus['lasttime'] = time_op.now()
			virus['isolateList'][filename] = [
				filepath, virusType, level, description, opsTime, OPERATION_ISOLATE]
			virus['allHistory'].append([opsTime, filepath, sha256])

		elif operation == OPERATION_TRUST:
			self.addWhiteList(filepath, False)
			ret = self.moveFromIsolation(filepath, filename)
			if ret:
				return ret

			path, virusType, level, description, x, y = virus['isolateList'].pop(
				filename)
			virus['handledList'][filename] = [
				filepath, virusType, level, description, opsTime, OPERATION_TRUST]

		elif operation == OPERATION_UNTRUST:
			self.delWhiteList(filepath)
			path, virusType, level, description, x, y = virus['handledList'][filename]
			virus['untrustList'][filename] = [
				filepath, virusType, level, description, opsTime, OPERATION_UNTRUST]

		elif operation == OPERATION_DELETE:
			# if file don't exist,ignore it,so no other errors.
			self.deleteFromIsolation(filepath, filename)
			path, virusType, level, description, x, y = virus['isolateList'].pop(
				filename)
			virus['handledList'][filename] = [
				filepath, virusType, level, description, opsTime, OPERATION_DELETE]

		elif operation == OPERATION_MOVETO:
			x, name = os.path.split(filepath)
			ret = self.moveFromIsolation(os.path.join(newpath, name), filename)
			if ret:
				return ret

			self.addWhiteList(filepath, False)
			path, virusType, level, description, x, y = virus['isolateList'].pop(
				filename)
			virus['handledList'][filename] = [
				filepath, virusType, level, description, opsTime, OPERATION_MOVETO]

		else:
			Klogger().warn("VirusScanner get unknow operation.")
			return "handleVirus:Unknow command."

		Kdatabase().dump('virus')

	def runVirusScan(self, root_paths):
		retry_list = []

		self.resetScanConfiguration()

		for filepath in self.retrieveFiles(root_paths):
			sha256 = file_op.sha256_checksum(filepath)
			ret = KCybertek().detect_file_sha256(sha256)

			if not ret:
				continue

			ret = json.loads(ret)
			data = ret["data"]

			if data:
				if data['isVirus']:
					self.handleVirus(filepath, data['virusType'], data['level'], sha256)

					if data['isNeedUpload']:
						self.uploadFile(filepath)
	
	  	# when we finish scan,set "finished" and "lastScanedPath"
		self.current_path = ''

		virus = Kdatabase().get_obj('virus')
		virus['finished'] = 1
		virus['lastScanedPath'] = self.current_path
		virus['searchedCount'] = self.searched_count
		virus['lasttime'] = time_op.now()

		Kdatabase().dump('virus')

	def runDeepScan(self):
		root_paths = []

		if common.is_linux() or common.is_darwin():
			root_paths.append(("/", True))
			self.avoid_list = ['/proc', '/dev', '/sys']

		if common.is_windows():
			for item in psutil.disk_partitions():
				device, mountpoint, fstype, opts = item
				if fstype:
					root_paths.append((mountpoint, True))
					self.avoid_list.append(os.path.join(
						mountpoint, '$Recycle.Bin').lower())

		self.runVirusScan(root_paths)

	def runQuickScan(self):
		root_paths = []

		if common.is_linux():
			root_paths = [("/root", True), ('/bin', True), ('/sbin',True),
						  ('/usr/bin', True), ('/usr/local/bin', True)]

		if common.is_darwin():
			root_paths.append(('/users', True))
		else:
			root_paths.append(('/home', True))

		if common.is_windows():
			# root_paths = [('D:\\test\\木马\\',True)]
			root = os.getenv('systemroot')[:1]
			root_paths = [(root+':\\users', True)]
			# root_paths = [  (root+":\\Documents and Settings", True),
			# 				(root+":\\windows", False),
			# 				(root+":\\windows\\system32", True),
			# 				(root+":\\windows\\syswow64\\system32", True),
			# 				(root+":\\program files", True),
			# 				(root+":\\Program Files (x86)", True)]

			self.avoid_list.append((root + ':\\$Recycle.Bin').lower())

		self.runVirusScan(root_paths)

	def runScannerCron(self):
		while True:
			virus = Kdatabase().get_obj('virus')
			settings = Kdatabase().get_obj('strategy')

			if settings:
				if virus['finished']:
					if not len(virus['isolateList']):
						if time_op.now() >= (virus['lasttime'] + settings["virus"]["period"]):
							self.runDeepScan()
				else:
					self.runDeepScan()

			time.sleep(60 * 60)  # wait for 1 hour to ask

	def clearHistory(self):
		virus = Kdatabase().get_obj('virus')
		for key in virus['handledList']:
			if virus['handledList'][key][-1] == OPERATION_TRUST:
				virus['handledList'][key][-1] = RESERVERED_WHEN_CLEARED_HISTORY
			else:
				virus['handledList'].pop(key)
		virus['untrustList'] = {}

		Kdatabase().dump('virus')

	def tryIsolateVirus(self, filepath, filename):
		path = os.path.join(self.isolation_path, filename)

		# TODO remove inusing file.
		try:
			shutil.move(filepath, path)
		except Exception as e:
			Klogger().exception()

			if os.path.exists(path):
				return None
			else:
				return "Isolate virus #{}# fail.".format(filepath)

		return None

	def moveFromIsolation(self, newpath, filename):
		path = os.path.join(self.isolation_path, filename)

		try:
			if not os.path.exists(path):
				return "original file is already being deleted."
			shutil.move(path, newpath)
		except:
			Klogger().exception()
			return "move to #{}# fail.".format(newpath)

	def deleteFromIsolation(self, filepath, filename):
		path = os.path.join(self.isolation_path, filename)
		try:
			if not os.path.exists(path):
				return
			os.remove(path)
		except:
			Klogger().exception()
			# don't know why this happened.shouldn't be no permission
			return "delete #{}# fail,an error happend.".format(filepath)

	def uploadFile(self, filepath):
		md5 = hashlib.md5()
		md5.update(filepath.encode('utf-8'))
		path = os.path.join(self.isolation_path, md5.hexdigest())
		x, originname = os.path.split(filepath)
		KCybertek().upload_virus(path, originname)

	def addWhiteList(self, filepath, isFromWhiteList):
		md5 = hashlib.md5()
		md5.update(filepath.encode('utf-8'))
		path = os.path.join(self.isolation_path, md5.hexdigest())
		whitelist = Kdatabase().get_obj('virus_whitelist')
		opsTime = '{0:%Y-%m-%d %H:%M:%S}'.format(
			datetime.datetime.now())

		if filepath not in whitelist:
			whitelist[filepath] = (opsTime, isFromWhiteList)
			self.white_list = whitelist

		Kdatabase().dump('virus_whitelist')

	def delWhiteList(self, filepath):
		md5 = hashlib.md5()
		md5.update(filepath.encode('utf-8'))
		path = os.path.join(self.isolation_path, md5.hexdigest())
		whitelist = Kdatabase().get_obj('virus_whitelist')
		opsTime = '{0:%Y-%m-%d %H:%M:%S}'.format(
			datetime.datetime.now())

		if filepath in whitelist:
			whitelist.pop(filepath)
			self.white_list = whitelist

		Kdatabase().dump('virus_whitelist')

	def isFilepathLegal(self, filepath):
		if filepath.startswith("../"):
			return False
		if filepath.startswith("..\\"):
			return False
		if '\\../' in filepath:
			return False
		if '\\..\\' in filepath:
			return False
		if '/../' in filepath:
			return False
		if '/..\\' in filepath:
			return False
		if "\\\\" in filepath:
			return False
		if "//" in filepath:
			return False
		if '\\/' in filepath:
			return False
		if '\\//' in filepath:
			return False
		return True

	def on_initializing(self, *args, **kwargs):
		return True

	def run_mod(self, mod_run):
		try:
			Kthreads().set_name("module-{}".format(mod_run.__module__))
			mod_run()
		except Exception as e:
			Klogger().exception()

	def on_start(self, *args, **kwargs):
		Kthreads().apply_async(self.run_mod, (self.runScannerCron,))
