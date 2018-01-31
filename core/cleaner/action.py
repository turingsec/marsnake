from utils import common, file_op
import functions, command, glob
import re
import types
import os

if 'posix' == os.name:
    re_flags = 0
else:
    re_flags = re.IGNORECASE

class action_base:

	def __init__(self, action_node):
		"""Create ActionProvider from CleanerML <action>"""
		pass

	def get_deep_scan(self):
		"""Return a dictionary used to construct a deep scan"""
		raise StopIteration

	@staticmethod
	def do(action_useful):
		"""Yield each command (which can be previewed or executed)"""
		pass

	def scan(self):
		"""Scan size to delete"""
		return None, 0

	def show(self):
		"""Show items which will be delete to client"""
		return 0
#
# file base class
#
class file_action_base(action_base):

    """Base class for providers which work on individual files"""
    action_key = '_file'

    def __init__(self, element):
        """Initialize file search"""
        self.regex = element["regex"] if element.has_key("regex") else ""
        assert(isinstance(self.regex, (str, unicode, types.NoneType)))

        self.nregex = element["nregex"] if element.has_key("nregex") else ""
        assert(isinstance(self.nregex, (str, unicode, types.NoneType)))

        self.wholeregex = element["wholeregex"] if element.has_key("wholeregex") else ""
        assert(isinstance(self.wholeregex, (str, unicode, types.NoneType)))

        self.nwholeregex = element["nwholeregex"] if element.has_key("nwholeregex") else ""
        assert(isinstance(self.nwholeregex, (str, unicode, types.NoneType)))

        self.search = element["search"] if element.has_key("search") else ""
        self.object_type = element["type"] if element.has_key("type") else ""
        self.path = common.expanduser(common.expandvars(element["path"] if element.has_key("path") else ""))

        if 'nt' == os.name and self.path:
            # convert forward slash to backslash for compatibility with getsize()
            # and for display.  Do not convert an empty path, or it will become
            # the current directory (.).
            self.path = os.path.normpath(self.path)

        self.ds = {}

        if 'deep' == self.search:
            self.ds['regex'] = self.regex
            self.ds['nregex'] = self.nregex
            self.ds['cache'] = common.boolstr_to_bool(element["cache"])
            self.ds['command'] = element["command"]
            self.ds['path'] = self.path

        if not any([self.object_type, self.regex, self.nregex,
                    self.wholeregex, self.nwholeregex]):
            # If the filter is not needed, bypass it for speed.
            self.get_paths = self._get_paths

    def get_deep_scan(self):
        if 0 == len(self.ds):
            raise StopIteration
        yield self.ds

    def path_filter(self, path):
        """Process the filters: regex, nregex, type
		
        If a filter is defined and it fails to match, this function
        returns False. Otherwise, this function returns True."""

        if self.regex:
            if not self.regex_c.search(os.path.basename(path)):
                return False

        if self.nregex:
            if self.nregex_c.search(os.path.basename(path)):
                return False

        if self.wholeregex:
            if not self.wholeregex_c.search(path):
                return False

        if self.nwholeregex:
            if self.nwholeregex_c.search(path):
                return False

        if self.object_type:
            if 'f' == self.object_type and not os.path.isfile(path):
                return False
            elif 'd' == self.object_type and not os.path.isdir(path):
                return False

        return True

    def get_paths(self):
        import itertools
        for f in itertools.ifilter(self.path_filter, self._get_paths()):
            yield f

    def _get_paths(self):
        """Return a filtered list of files"""

        def get_file(path):
            if os.path.lexists(path):
                yield path

        def get_walk_all(top):
            for expanded in glob.iglob(top):
                for path in file_op.children_in_directory(expanded, True):
                    yield path

        def get_walk_files(top):
            for expanded in glob.iglob(top):
                for path in file_op.children_in_directory(expanded, False):
                    yield path

        if 'deep' == self.search:
            raise StopIteration
        elif 'file' == self.search:
            func = get_file
        elif 'glob' == self.search:
            func = glob.iglob
        elif 'walk.all' == self.search:
            func = get_walk_all
        elif 'walk.files' == self.search:
            func = get_walk_files
        else:
            raise RuntimeError("invalid search='%s'" % self.search)

        if self.regex:
            self.regex_c = re.compile(self.regex, re_flags)

        if self.nregex:
            self.nregex_c = re.compile(self.nregex, re_flags)

        if self.wholeregex:
            self.wholeregex_c = re.compile(self.wholeregex, re_flags)

        if self.nwholeregex:
            self.nwholeregex_c = re.compile(self.nwholeregex, re_flags)

        for path in func(self.path):
            yield path

	@staticmethod
	def do(action_useful):
		raise NotImplementedError('not implemented')

class AptAutoclean(action_base):

	"""Action to run 'apt-get autoclean'"""
	action_key = 'apt.autoclean'

	def __init__(self, action_element):
		pass

	@staticmethod
	def do(action_useful):
		# Checking executable allows auto-hide to work for non-APT systems
		if common.check_programs_installed('apt-get'):
			yield command.Function(None,
									functions.apt_autoclean,
									'apt-get autoclean').execute()

class AptAutoremove(action_base):

	"""Action to run 'apt-get autoremove'"""
	action_key = 'apt.autoremove'

	def __init__(self, action_element):
		pass

	@staticmethod
	def do(action_useful):
		# Checking executable allows auto-hide to work for non-APT systems
		if common.check_programs_installed('apt-get'):
			yield command.Function(None,
									functions.apt_autoremove,
									'apt-get autoremove').execute()

class AptClean(action_base):

	"""Action to run 'apt-get clean'"""
	action_key = 'apt.clean'

	def __init__(self, action_element):
		pass

	@staticmethod
	def do(action_useful):
		# Checking executable allows auto-hide to work for non-APT systems
		if common.check_programs_installed('apt-get'):
			yield command.Function(None,
									functions.apt_clean,
									'apt-get clean').execute()

class ChromeAutofill(file_action_base):

	"""Action to clean 'autofill' table in Google Chrome/Chromium"""
	action_key = 'chrome.autofill'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Function(
								path,
								functions.delete_chrome_autofill,
								_('Clean file')).execute()

class ChromeDatabases(file_action_base):

	"""Action to clean Databases.db in Google Chrome/Chromium"""
	action_key = 'chrome.databases_db'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Function(
								path,
								functions.delete_chrome_databases_db,
								_('Clean file')).execute()

class ChromeFavicons(file_action_base):

	"""Action to clean 'Favicons' file in Google Chrome/Chromium"""
	action_key = 'chrome.favicons'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Function(
								path,
								functions.delete_chrome_favicons,
								_('Clean file')).execute()

class ChromeHistory(file_action_base):

	"""Action to clean 'History' file in Google Chrome/Chromium"""
	action_key = 'chrome.history'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Function(
								path,
								functions.delete_chrome_history,
								_('Clean file')).execute()

class ChromeKeywords(file_action_base):
	
	"""Action to clean 'keywords' table in Google Chrome/Chromium"""
	action_key = 'chrome.keywords'
	
	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Function(
								path,
								functions.delete_chrome_keywords,
								_('Clean file')).execute()
			
class Delete(file_action_base):
	
	"""Action to delete files"""
	action_key = 'delete'
	
	def scan(self):
		total_size = 0
		action_useful = {
			"paths" : [],
			"action_key" : self.action_key
		}

		for path in self.get_paths():
			size = file_op.getsize(path)

			action_useful["paths"].append(path)
			total_size += size

		return action_useful, total_size
	
	@staticmethod
	def do(action_useful):
		for path in action_useful["paths"]:
			print(path)
			command.Delete(path).execute()

class Ini(file_action_base):

	"""Action to clean .ini configuration files"""
	action_key = 'ini'

	def __init__(self, action_element):
		file_action_base.__init__(self, action_element)

		self.section = action_element["section"] if action_element.has_key("section") else ""
		self.parameter = action_element["parameter"] if action_element.has_key("parameter") else ""

		if self.parameter == "":
			self.parameter = None

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Ini(path, self.section, self.parameter).execute()

class Journald(action_base):
	"""Action to run 'journalctl --vacuum-time=1'"""
	action_key = 'journald.clean'

	def __init__(self, action_element):
		pass

	@staticmethod
	def do(action_useful):
		if common.check_programs_installed('journalctl'):
			yield command.Function(None, functions.journald_clean, 'journalctl --vacuum-time=1').execute()

class Json(file_action_base):

	"""Action to clean JSON configuration files"""
	action_key = 'json'

	def __init__(self, action_element):
		file_action_base.__init__(self, action_element)

		self.address = action_element["address"] if action_element.has_key("address") else ""

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Json(path, self.address).execute()

class MozillaUrlHistory(file_action_base):

	"""Action to clean Mozilla (Firefox) URL history in places.sqlite"""
	action_key = 'mozilla_url_history'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield functions.delete_mozilla_url_history(path)

class OfficeRegistryModifications(file_action_base):

	"""Action to delete LibreOffice history"""
	action_key = 'office_registrymodifications'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Function(
								path,
								functions.delete_office_registrymodifications,
								_('Clean')).execute()

class Shred(file_action_base):

	"""Action to shred files (override preference)"""
	action_key = 'shred'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Shred(path).execute()

class SqliteVacuum(file_action_base):

	"""Action to vacuum SQLite databases"""
	action_key = 'sqlite.vacuum'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Function(
								path,
								file_op.vacuum_sqlite3,
								# TRANSLATORS: Vacuum is a verb.  The term is jargon
								# from the SQLite database.  Microsoft Access uses
								# the term 'Compact Database' (which you may translate
								# instead).  Another synonym is 'defragment.'
								_('Vacuum')).execute()

class Truncate(file_action_base):

	"""Action to truncate files"""
	action_key = 'truncate'

	@staticmethod
	def do(action_useful):
		for path in self.get_paths():
			yield command.Truncate(path).execute()

class WinShellChangeNotify(action_base):

	"""Action to clean the Windows Registry"""
	action_key = 'win.shell.change.notify'

	@staticmethod
	def do(action_useful):
		from bleachbit import Windows
		yield command.Function(
							None,
							Windows.shell_change_notify,
							None).execute()

class Winreg(action_base):

	"""Action to clean the Windows Registry"""
	action_key = 'winreg'

	def __init__(self, action_element):
		self.keyname = action_element["path"] if action_element.has_key("path") else ""
		self.name = action_element["name"] if action_element.has_key("name") else ""

	@staticmethod
	def do(action_useful):
		yield command.Winreg(self.keyname, self.name).execute()

class YumCleanAll(action_base):

	"""Action to run 'yum clean all'"""
	action_key = 'yum.clean_all'

	def __init__(self, action_element):
		pass

	#def scan(self):
	#	return file_op.getsizedir('/var/cache/yum')
	@staticmethod
	def do(action_useful):
		# Checking allows auto-hide to work for non-APT systems
		if not common.check_programs_installed('yum'):
			raise StopIteration

		yield command.Function(
			None,
			functions.yum_clean,
			'yum clean all').execute()