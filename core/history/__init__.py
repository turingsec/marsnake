from utils.singleton import singleton
from core.event.base_event import base_event
from core.logger import Klogger
from core.threads import Kthreads
from core.history.process import process

def run_thread(start_func, name):
	try:
		Kthreads().set_name("History-{}".format(name))
		start_func()
	except:
		Klogger().exception()

@singleton
class Khistory(base_event):
	def __init__(self):
		self.modules = (process(), )
		pass

	def on_initializing(self, *args, **kwargs):
		return True

	def on_start(self, *args, **kwargs):
		for module in self.modules:
			if module.init():
				Kthreads().apply_async(module.start, module.name)
			else:
				Klogger().error("History-{} init failed".format(module.name))
