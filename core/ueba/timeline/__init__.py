from core.db import Kdatabase
from core.cybertek import KCybertek
from core.language import Klanguage
from utils.randomize import Krandom
from utils.singleton import singleton
from utils import common, time_op

@singleton
class KUEBA_timeline():
	def __init__(self):
		pass

	def publish(self, timeline, kind, des, root_cause, suggestion, activities, icon, introduction, score):
		ueba = Kdatabase().get_obj("ueba")
		threat_id = Krandom().purely(16)
		threat = {
			"kind" : kind,
			"timeline" : timeline,
			"resolved" : False,
			"resolved_ts" : -1,
			"unread" : True,
			"read_ts" : -1,
			"description" : des,
			"root_cause" : root_cause,
			"suggestion" : suggestion,
			"activities" : activities,
			"icon" : icon,
			"introduction" : introduction,
			"ts" : time_op.now(),
			"score" : score
		}

		ueba["lasttime"] = time_op.now()
		ueba["storys"][threat_id] = threat

		Kdatabase().dump("ueba")

		threat["description"] = Klanguage().decode_ts(threat["description"])
		threat["root_cause"] = Klanguage().decode_ts(threat["root_cause"])
		threat["suggestion"] = Klanguage().decode_ts(threat["suggestion"])

		KCybertek().publish_threat(threat_id, threat)
		
		print(threat)
		print("KUEBA timeline add one!")
