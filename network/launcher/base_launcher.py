class base_launcher(object):
	def __init__(self):
		pass
		
	def init_argparse(self, args):
		raise NotImplementedError("init_argparse launcher's method needs to be implemented")
		
	def print_argparser(self):
		self.parser.print_help()
		
	def start(self):
		raise NotImplementedError("start launcher's method needs to be implemented")