from core.ueba.classifier import base_classifier
from core.ueba.timeline import KUEBA_timeline
from datetime import datetime
from core.ueba import macro, logic
from core.language import Klanguage
from utils import common, time_op
import platform, os

class proc_connect_malicious_ip(base_classifier):
	def __init__(self):
		pass

	def on_proc_connect_malicious_ip(self, pid, ip, ip_report):
		proc_info = logic.create_proc_info(pid)

		self.publish(proc_info, ip_report)

	def publish(self, *args, **kwargs):
		proc_info = args[0]
		ip_report = args[1]

		KUEBA_timeline().publish([
			{
				"kind" : macro.EVENTS["MALWARE_PROC_DETAIL"],
				"extra" : proc_info,
				"des" : Klanguage().encode_ts(5009),
				"time" : proc_info["create_time"],
				"title" : Klanguage().encode_ts(5010),
				"distro" : common.get_distribution(),
				"hostname" : platform.node(),
			},
			{
				"kind" : macro.EVENTS["MALICIOUS_IP_REPORT"],
				"extra" : ip_report,
				"des" : Klanguage().encode_ts(5011),
				"time" : time_op.now(),
				"title" : Klanguage().encode_ts(5012),
				"distro" : common.get_distribution(),
				"hostname" : platform.node(),
			}
		],
		macro.STORY_KIND["CC"],
		Klanguage().encode_ts(5013, str(datetime.fromtimestamp(proc_info["create_time"]))),
		Klanguage().encode_ts(5014, ip_report["ip"]),
		Klanguage().encode_ts(5015),
		[macro.ACTIVITY["10003"]],
		macro.SUB_STORY_KIND["1002"][0],
		[macro.SUB_STORY_KIND["1002"][1], proc_info["exe"], Klanguage().encode_ts(5014, ip_report["ip"])],
		macro.SCORE["VULNERABLE"])
