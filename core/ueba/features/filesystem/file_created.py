from core.ueba.features.filesystem import filesystem_feature

class file_created(filesystem_feature):
	def __init__(self):
		pass
		
	def on_file_created_captured(self, file):
		""" Check whether should take over the content """
		pass