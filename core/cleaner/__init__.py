from utils.singleton import singleton
from utils import file_op, common
from config import constant
from core.logger import Klogger
import os, stat, sys, json
import action, functions

class clean_item():
    """Create a cleaner from CleanerML"""

    def __init__(self, pathname):
        self.id = None
        self.description = None
        self.usable = False

        with open(pathname, "r") as f:
            self.conf = json.load(f)

        self.handle_json()

    def handle_json(self):
        self.id = self.conf["id"]
        self.description = self.conf["description"]

        if self.os_match(self.conf["os"] if self.conf.has_key("os") else ""):
            self.usable = True

    def os_match(self, os_str):
        """Return boolean whether operating system matches"""
        # If blank or if in .pot-creation-mode, return true.
        if len(os_str) == 0:
            return True

        # Otherwise, check platform.
        if os_str == 'linux' and common.is_linux():
            return True

        if os_str == 'windows' and common.is_windows():
            return True

        return False

    def is_usable(self):
        return self.usable

@singleton
class Kcleaner():
    def __init__(self):
        self.holder = {}
        self.jsons = os.path.join(common.get_work_dir(), constant.CLEANER_CONF)
        self.action_maps = {
            "apt.autoclean" : action.AptAutoclean,
            "apt.autoremove" : action.AptAutoremove,
            "apt.clean" : action.AptClean,
            "chrome.autofill" : action.ChromeAutofill,
            "chrome.databases_db" : action.ChromeDatabases,
            "chrome.favicons" : action.ChromeFavicons,
            "chrome.history" : action.ChromeHistory,
            "chrome.keywords" : action.ChromeKeywords,
            "delete" : action.Delete,
            "ini" : action.Ini,
            "journald.clean" : action.Journald,
            "json" : action.Json,
            "mozilla_url_history" : action.MozillaUrlHistory,
            "office_registrymodifications" : action.OfficeRegistryModifications,
            "shred" : action.Shred,
            "sqlite.vacuum" : action.SqliteVacuum,
            "truncate" : action.Truncate,
            "win.shell.change.notify" : action.WinShellChangeNotify,
            "winreg" : action.Winreg,
            "yum.clean_all" : action.YumCleanAll
        }

        # set up environment variables
        if 'nt' == os.name:
            import windows
            windows.setup_environment()

        if 'posix' == os.name:
            # XDG base directory specification
            envs = {
                'XDG_DATA_HOME': os.path.expanduser('~/.local/share'),
                'XDG_CONFIG_HOME': os.path.expanduser('~/.config'),
                'XDG_CACHE_HOME': os.path.expanduser('~/.cache')
            }

            for varname, value in envs.iteritems():
                if not os.getenv(varname):
                    os.environ[varname] = value

    def list_cleaner_jsons(self):
        for pathname in file_op.listdir(self.jsons):
            if not pathname.lower().endswith('.json'):
                continue

            st = os.stat(pathname)

            if sys.platform != 'win32' and stat.S_IMODE(st[stat.ST_MODE]) & 2:
                Klogger().warn("ignoring cleaner because it is world writable: %s", pathname)
                continue

            yield pathname

    def load_jsons(self):
        """Scan for CleanerML and load them"""
        for pathname in self.list_cleaner_jsons():
            try:
                item = clean_item(pathname)
            except Exception as e:
                Klogger().warn('error reading item: %s %s', pathname, e)
                continue

            if item.is_usable():
                self.holder[item.id] = item
            else:
                Klogger().warn('item is not usable on this OS because it has no actions: %s', pathname)
                
    def scan(self):
        for i, item in self.holder.items():
            options = item.conf["option"]
            size = 0

            for option in options:
                for element in option["action"]:
                    #if self.action_maps.has_key(element["command"]):
                    c = self.action_maps[element["command"]](element)
                    size += c.scan()
                    
            print(i, size)