from utils.singleton import singleton
from core.threads import Kthreads
from core.computer_score import KScore
import time

@singleton
class KPipe():
	def __init__(self):
		pass

	def start(self, child_end):
		while True:
			msg_from_parent = child_end.recv()

			if msg_from_parent:
				if msg_from_parent["code"] == 1:
					child_end.send(KScore().get_status())
