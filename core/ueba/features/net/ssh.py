from core.ueba.features.net import net_feature

class ssh_traffic(net_feature):
	def __init__(self):
		pass

	def on_match(self, packet):
		""" Check whether should take over the packet """
		pass