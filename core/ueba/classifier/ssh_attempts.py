from core.ueba.classifier import base_classifier
from core.ueba.timeline import KUEBA_timeline
from datetime import datetime
from core.ueba import macro
from core.language import Klanguage
from utils import common
import platform

class ssh_attempts(base_classifier):
	def __init__(self):
		pass

	def on_ssh_attempts(self, failed_info, info, account, ts):
		self.publish(failed_info, info, account, ts)

	def publish(self, *args, **kwargs):
		failed_info = args[0]
		info = args[1]
		account = args[2]
		ts = args[3]

		KUEBA_timeline().publish([
			{
				"kind" : macro.EVENTS["SSH_FAILED"],
				"extra" : failed_info,
				"des" : Klanguage().encode_ts(5001, account),
				"time" : info["first_ts"],
				"title" : Klanguage().encode_ts(5002),
				"distro" : common.get_distribution(),
				"hostname" : platform.node(),
			},
			{
				"kind" : macro.EVENTS["SSH_SUCCESS"],
				"extra" : {
					"account" : account,
					"ip" : info["ip"],
					"login_ts" : ts
				},
				"des" : Klanguage().encode_ts(5003, account),
				"time" : ts,
				"title" : Klanguage().encode_ts(5004),
				"distro" : common.get_distribution(),
				"hostname" : platform.node(),
			}
		],
		macro.STORY_KIND["INSTRUSION"],
		Klanguage().encode_ts(5005, str(datetime.fromtimestamp(ts))),
		Klanguage().encode_ts(5006, account),
		Klanguage().encode_ts(5007),
		[macro.ACTIVITY["10000"]],
		macro.SUB_STORY_KIND["1000"][0],
		[macro.SUB_STORY_KIND["1000"][1], account, Klanguage().encode_ts(5008)],
		macro.SCORE["VULNERABLE"])
