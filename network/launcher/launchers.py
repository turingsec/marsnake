import sys
from utils.singleton import singleton
from network.launcher.connect_launcher import connect_launcher

@singleton
class Klauncher():
	"class launcher"
	def __init__(self):
		self.launcher = None
		self.map = {
			"connect" : connect_launcher
		}
		
	def set_launcher(self, name):
		if not name in self.map.keys():
			assert 0, "bad launcher name"
			
		self.launcher = self.map[name]()
		
	def get_names(self):
		return self.map.keys()
		
	def start(self):
		if self.launcher:
			self.launcher.start()