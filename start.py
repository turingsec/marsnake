import sys, traceback
from network.launcher.launchers import Klauncher
from module.factory_module import Kmodules
from core.threads import Kthreads
from core.security import Ksecurity
from core.db import Kdatabase
from core.logger import Klogger
from utils import common
from core.configuration import Kconfig

LAUNCHER = "connect"

def init_config():
	common.setdefaultencoding("utf8")
	common.set_work_dir()
	common.add_module_path("lib")
	
	if not Kconfig().init():
		sys.exit(1)
		
	Klogger().init()

	Kdatabase().init()
	Ksecurity().init()
	Kmodules().init()
	
def init_network():
	Klauncher().set_launcher(LAUNCHER)

if __name__ == '__main__':
	try:
		init_config()
		init_network()
		
		Klauncher().start()
		#Kthreads().apply_async(Klauncher().start, ())
		#Kthreads().join()

	except Exception as e:
		traceback.print_exc()
		Klogger().error(e)
