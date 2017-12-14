from utils.singleton import singleton

class event():
	def __init__(self):
		Kevent().signup(self)

	def on_initializing(self, *args, **kwargs):
		raise NotImplementedError("class %s's on_disconnected method needs to be implemented" % 
						self.__class__)

	def on_disconnected(self, *args, **kwargs):
		raise NotImplementedError("class %s's on_disconnected method needs to be implemented" % 
						self.__class__)

@singleton
class Kevent():
	
	def __init__(self):
		self.members = []
		
	def signup(self, target):
		self.members.append(target)
		
	def do_initializing(self, *args, **kwargs):
		for target in self.members:
			target.on_initializing(*args, **kwargs)
			
	def do_disconnected(self, *args, **kwargs):
		for target in self.members:
			target.on_disconnected(*args, **kwargs)
			