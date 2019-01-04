from core.ueba.events import KUEBA_event
from core.ueba.features.filesystem import filesystem_feature

class usb_monitor(filesystem_feature):
	def __init__(self):
		pass

	def on_usb_plugged(self, info):
		KUEBA_event().on_usb_plugged(info)

	def on_usb_unplugged(self, info):
		KUEBA_event().on_usb_unplugged(info)