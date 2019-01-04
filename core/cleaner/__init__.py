from utils.singleton import singleton
from utils import file_op, common, time_op
from utils.randomize import Krandom
from config import constant
from core.logger import Klogger
import os, stat, sys, json, threading
from . import action, functions

class clean_item():
    def __init__(self, pathname):
        self.id = None
        self.usable = False

        with open(pathname, "r") as f:
            self.conf = json.load(f)

        self.handle_json()

    def handle_json(self):
        self.id = self.conf["id"]

@singleton
class Kcleaner():
    def __init__(self):
        self.kinds = {}
        self.apps_list = {}
        self.json_path = os.path.join(common.get_work_dir(), constant.CLEANER_CONF)
        self.json_files = ('application_cache.json', 'cookies.json', 'crashes.json',                'history.json', 'logs.json', 'recently_used.json', 'temp.json', 'trash.json')
        self.lock = threading.Lock()
        self.action_maps = {
            #"apt.autoclean" : action.AptAutoclean,
            #"apt.autoremove" : action.AptAutoremove,
            #"apt.clean" : action.AptClean,
            #"chrome.autofill" : action.ChromeAutofill,
            #"chrome.databases_db" : action.ChromeDatabases,
            #"chrome.favicons" : action.ChromeFavicons,
            #"chrome.history" : action.ChromeHistory,
            #"chrome.keywords" : action.ChromeKeywords,
            "delete" : action.Delete,
            #"ini" : action.Ini,
            #"journald.clean" : action.Journald,
            #"json" : action.Json,
            #"mozilla_url_history" : action.MozillaUrlHistory,
            #"office_registrymodifications" : action.OfficeRegistryModifications,
            #"shred" : action.Shred,
            #"sqlite.vacuum" : action.SqliteVacuum,
            #"truncate" : action.Truncate,
            #"win.shell.change.notify" : action.WinShellChangeNotify,
            #"winreg" : action.Winreg,
            #"yum.clean_all" : action.YumCleanAll
        }

        # set up environment variables
        if 'nt' == os.name:
            from . import windows
            windows.setup_environment()

        if 'posix' == os.name:
            # XDG base directory specification
            envs = {
                'XDG_DATA_HOME': os.path.expanduser('~/.local/share'),
                'XDG_CONFIG_HOME': os.path.expanduser('~/.config'),
                'XDG_CACHE_HOME': os.path.expanduser('~/.cache')
            }

            for varname, value in envs.items():
                if not os.getenv(varname):
                    os.environ[varname] = value

    def get_lock(self):
        return self.lock

    def load_jsons(self):
        apps_path = os.path.join(self.json_path, "apps.json")
        if not os.path.exists(apps_path):
            Klogger().debug("apps.json does not exist")
            raise Exception

        try:
            with open(apps_path, "r") as f:
                raw_apps_list = json.load(f)
        except Exception as e:
            Klogger().debug("read apps.json fails with %s" % (str(e)))
            raise

        for each in raw_apps_list:
            if (not 'id' in each or not 'label' in each or not 'description' in each or not 'icon' in each):
                Klogger().debug("Corrupted item in apps.json")
                continue

            if 'os' in each:
                if each['os'] == "windows":
                    if not common.is_windows():
                        continue
                elif each['os'] == "linux":
                    if not common.is_linux():
                        continue
                else:
                    Klogger().debug("Unknown os in apps.json, id %s" % (each['id']))
                    continue

            item = {"label": each['label'],
                    "description": each['description'],
                    "icon": each['icon']}
            
            if 'running' in each:
                item['running'] = each['running']

            self.apps_list[each['id']] = item

        for pathname in self.json_files:
            try:
                item = clean_item(os.path.join(self.json_path, pathname))
            except Exception as e:
                Klogger().warn('error reading item: %s %s', pathname, e)
                continue

            self.kinds[item.id] = item

    def scan(self):
        kinds = {}

        for i, item in self.kinds.items():
            options = item.conf["option"]
            autoclean = False if not "autoclean" in item.conf else item.conf["autoclean"]
            items = {}
            total_size = 0

            for option in options:
                if not option['app'] in self.apps_list:
                    continue

                option_useful = []
                option_size = 0
                icon = self.apps_list[option["app"]]["icon"]

                for element in option["action"]:
                    if element["command"] in self.action_maps:
                        c = self.action_maps[element["command"]](element)
                        action_useful, action_size = c.scan()

                        if action_size > 0:
                            option_useful.append(action_useful)
                            option_size += action_size

                if option_size > 0:
                    label = self.apps_list[option['app']]["label"]
                    icon = self.apps_list[option['app']]['icon']
                    items[Krandom().purely(16)] = [label, icon, option_size, option_useful]
                    total_size += option_size

            kinds[i] = {
                "name" : item.conf["label"],
                "des" : item.conf["description"],
                "autoclean" : autoclean, 
                "size" : total_size,
                "items" : items
            }

        return kinds

    def do(self, action_useful):
        action_key = action_useful["action_key"]

        if action_key in self.action_maps:
            return self.action_maps[action_key].do(action_useful)

        print("clean file: No action")
        return 0

    def clean_option(self, info, option_id, record):
        option = info["items"][option_id]
        option_size, option_useful = option[2 : 4]
        failed_count = 0
        total_size = 0

        for action_useful in option_useful:
            failed_count += self.do(action_useful)

        total_size = option_size
        info["size"] -= option_size
        del info["items"][option_id]

        self.update_record(record, total_size)

        return total_size, failed_count

    def update_record(self, record, total_size):
        today = time_op.get_last_day()

        if len(record) > 0:
            last_record = record[-1]
            lastday = time_op.get_last_day(last_record["time"])

            if today == lastday:
                last_record["size"] += total_size
            else:
                record.append({
                    "time" : today,
                    "size" : total_size
                })
        else:
            record.append({
                "time" : today,
                "size" : total_size
            })
