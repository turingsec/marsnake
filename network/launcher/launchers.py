import sys
from utils.singleton import singleton
from core.event.base_event import base_event

@singleton
class Klauncher(base_event):
	"class launcher"
	def __init__(self):
		from network.launcher.connect_launcher import connect_launcher
		
		self.launcher = None
		self.map = {
			"connect" : connect_launcher
		}
	
	def on_initializing(self, *args, **kwargs):
		name = "connect"

		if not name in self.map.keys():
			return False				#assert 0, "bad launcher name"
			
		self.launcher = self.map[name]()
		
		return True
		
	def on_start(self, *args, **kwargs):
		if self.launcher:
			self.launcher.start()

	def get_names(self):
		return self.map.keys()