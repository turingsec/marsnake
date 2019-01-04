class base_event():
	def __init__(self):
		pass

	def on_initializing(self, *args, **kwargs):
		raise NotImplementedError("class %s's on_initializing method needs to be implemented" % 
						self.__class__)

	def on_start(self, *args, **kwargs):
		pass

	def on_disconnected(self, *args, **kwargs):
		pass

	def on_unpack(self, *args, **kwargs):
		pass