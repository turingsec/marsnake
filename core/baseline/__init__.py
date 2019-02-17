# -- coding: utf-8 --
from utils.singleton import singleton
from utils import time_op
from core.logger import Klogger
from core.threads import Kthreads
from core.db import Kdatabase
from core.profile_reader import KProfile
from core.baseline.authentication import authentication
from core.baseline.database import database
from core.baseline.normal import normal
from core.baseline.system import system
from core.baseline.weak_pwd import weak_pwd
import time

@singleton
class Kbaseline():
	def __init__(self):
		self.maps = {
			"authentication": authentication(),
			"database": database(),
			"normal": normal(),
			"system": system(),
			"weak_pwd": weak_pwd(),
		}

	def verify_all(self, target_risk_id):
		for i in self.maps:
			self.maps[i].do(target_risk_id)

	def on_initializing(self, *args, **kwargs):
		return True

	def run_mod(self, mod_run):
		try:
			Kthreads().set_name("module-{}".format(mod_run.__module__))
			mod_run()
		except Exception as e:
			Klogger().exception()

	def on_start(self, *args, **kwargs):
		Kthreads().apply_async(self.run_mod, (self.check_loop, ))

	def check_loop(self):
		while True:
			baseline = Kdatabase().get_obj('baseline')
			settings = KProfile().get_web_strategy()
			now = time_op.now()
			
			if settings:
				if now > (baseline['lasttime'] + settings["audit"]["period"]):
					items = settings["audit"]["items"]

					for i in items:
						if items[i] == True and i in self.maps:
							self.maps[i].do(None)

					baseline["lasttime"] = now
					Kdatabase().dump('baseline')

			time.sleep(5)
