from utils.singleton import singleton
from core.security import Ksecurity
from core.db import Kdatabase
from core.logger import Klogger
from core.ptys import Kptys
from core.ueba import KUEBA
from core.threads import Kthreads
from core.language import Klanguage
from core.baseline import Kbaseline
#from core.icloud import Kicloud
from module.factory_module import Kmodules
from network.launcher.launchers import Klauncher
from core.virusScan import KvirusScanner
import signal, sys, os

def signal_int_handler(signal, frame):
	print('You pressed Ctrl+C! I am {}'.format(Kthreads().get_name()))
	Klogger().info("INT receive pid:{}".format(os.getpid()))
	Kevent().set_terminate()
	sys.exit(2)

def signal_term_handler(signal, frame):
	print('signal terminate receive! I am {}'.format(Kthreads().get_name()))
	Klogger().info("terminate receive pid:{}".format(os.getpid()))
	Kevent().set_terminate()
	sys.exit(1)

@singleton
class Kevent():
	def __init__(self):
		self.members = [Klogger(), Kdatabase(), Klanguage(),
						Ksecurity(), Kmodules(), KUEBA(), Kptys(),
						KvirusScanner(), Kbaseline(), Klauncher()]
		self.terminate = False

	def init_signal(self):
		signal.signal(signal.SIGINT, signal_int_handler)
		signal.signal(signal.SIGTERM, signal_term_handler)

	def signup(self, target):
		self.members.append(target)

	def do_initializing(self, *args, **kwargs):
		for target in self.members:
			if not target.on_initializing(*args, **kwargs):
				return False

		return True

	def do_start(self, *args, **kwargs):
		Kthreads().set_name("Network-thread")

		for target in self.members:
			if hasattr(target, "on_start"):
				target.on_start(*args, **kwargs)

	def do_unpack(self, *args, **kwargs):
		for target in self.members:
			if hasattr(target, "on_unpack"):
				target.on_unpack(*args, **kwargs)

	def do_disconnected(self, *args, **kwargs):
		for target in self.members:
			if hasattr(target, "on_disconnected"):
				target.on_disconnected(*args, **kwargs)

	def set_terminate(self):
		self.terminate = True

	def is_terminate(self):
		return self.terminate
