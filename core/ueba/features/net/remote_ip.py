from core.ueba.features.net import net_feature
from core.ueba.events import KUEBA_event
from core.cybertek import KCybertek
import json

class remote_ip(net_feature):
	def __init__(self):
		self.maliciou_ip_map = {}

	def remote_ip_detect(self, pid, ip):
		if ip not in self.maliciou_ip_map:
			ip_report = KCybertek().get_ip_report(ip)

			if ip_report:
				ip_report = json.loads(ip_report)
				print(ip_report)
				detected_downloaded_samples = ip_report["detected_downloaded_samples"]
				positives = 0
				total = 0

				for url in detected_downloaded_samples:
					positives += url["positives"]
					total += url["total"]

				if len(ip_report["resolutions"]) > 0:
					ip_report["resolutions"].sort(key = lambda t : t["last_resolved"], reverse = True)
					ip_report["resolutions"] = ip_report["resolutions"][:10]
					date = ip_report["resolutions"][0]["last_resolved"]
				else:
					date = "Unknown"

				self.maliciou_ip_map[ip] = {
					"resolutions" : ip_report["resolutions"],
					"date" : date,
					"ip" : ip,
					"positives" : positives,
					"total" : total
				}
				
				if total > 0 and (positives / total) > 0.4:
					KUEBA_event().malicious_ip_detect(pid, ip, self.maliciou_ip_map[ip])
