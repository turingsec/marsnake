from core.ueba.classifier import base_classifier
from core.ueba.timeline import KUEBA_timeline
from datetime import datetime
from core.ueba import macro, logic
from core.language import Klanguage
from utils import common, time_op
import platform, os

class backdoor_detect(base_classifier):
	def __init__(self):
		pass

	def on_backdoor_detect(self, pid, ppid):
		proc_info = logic.create_proc_info(pid)
		pproc_info = logic.create_proc_info(ppid)

		self.publish(proc_info, pproc_info)

	def publish(self, *args, **kwargs):
		proc_info = args[0]
		pproc_info = args[1]

		KUEBA_timeline().publish([
			{
				"kind" : macro.EVENTS["MALWARE_PROC_DETAIL"],
				"extra" : proc_info,
				"des" : Klanguage().encode_ts(5016),
				"time" : proc_info["create_time"],
				"title" : Klanguage().encode_ts(5017),
				"distro" : common.get_distribution(),
				"hostname" : platform.node(),
			},
			{
				"kind" : macro.EVENTS["MALWARE_PROC_DETAIL"],
				"extra" : pproc_info,
				"des" : Klanguage().encode_ts(5018),
				"time" : pproc_info["create_time"],
				"title" : Klanguage().encode_ts(5019),
				"distro" : common.get_distribution(),
				"hostname" : platform.node(),
			}
		],
		macro.STORY_KIND["INSTRUSION"],
		Klanguage().encode_ts(5020, str(datetime.fromtimestamp(proc_info["create_time"]))),
		Klanguage().encode_ts(5021, proc_info["pid"]),
		Klanguage().encode_ts(5022),
		[macro.ACTIVITY["10005"]],
		macro.SUB_STORY_KIND["1005"][0],
		[macro.SUB_STORY_KIND["1005"][1], proc_info["exe"], Klanguage().encode_ts(5021, proc_info["pid"])],
		macro.SCORE["VULNERABLE"])
