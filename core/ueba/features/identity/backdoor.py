from core.ueba.events import KUEBA_event
from core.ueba.features.identity import identity_feature

class backdoor(identity_feature):
	def __init__(self):
		pass

	def backdoor_detect(self, pid, ppid):
		KUEBA_event().backdoor_detect(pid, ppid)
