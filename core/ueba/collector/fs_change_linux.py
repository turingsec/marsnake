import pyinotify

class filesystem_change(pyinotify.ProcessEvent):
	def __init__(self, file_created_captured, file_modified_captured):
		self.WATCHDIR = u'/tmp'
		
		self.file_created_captured = file_created_captured
		self.file_modified_captured = file_modified_captured
		
		self.wm = pyinotify.WatchManager()  # Watch Manager
		self.mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE  | pyinotify.IN_MODIFY # watched events
		
		self.notifier = pyinotify.Notifier(self.wm, self)
		self.wdd = self.wm.add_watch(self.WATCHDIR, self.mask, rec = True)
		
	def do(self):
		self.notifier.loop()

	def process_IN_CREATE(self, event):
		print "Creating:", event.pathname
		self.file_created_captured(event.pathname)

	def process_IN_MODIFY(self, event):
		print "modify:", event.pathname
		
	def process_IN_DELETE(self, event):
		print "Removing:", event.pathname
		pass

	def process_IN_CLOSE_WRITE(self, event):
		print("Close and write", event.pathname)
		self.file_modified_captured(event.pathname)