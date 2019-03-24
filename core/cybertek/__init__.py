from utils.singleton import singleton
from core.threads import Kthreads
from core.information import KInformation
from core.computer_score import KScore
from utils import net_op, file_op
from config import constant
import urllib.parse, json
import os, struct

@singleton
class KCybertek():
	def __init__(self):
		pass

	def upload_virus(self, pathname, oldname, block = False):
		if not block:
			Kthreads().apply_async(self.do_upload_virus, (pathname, oldname))
		else:
			self.do_upload_virus(pathname, oldname)

	def do_upload_virus(self, pathname, oldname):
		if file_op.getsize(pathname) <= constant.MALWARE_FILE_MAX_SIZE:
			sha256 = file_op.sha256_checksum(pathname)
			content = file_op.cat(pathname)

			if sha256 and content:
				sha256 = struct.pack("{}s".format(len(sha256)), sha256.encode("ascii"))
				oldname_len = struct.pack("<I", len(oldname))
				oldname = struct.pack("{}s".format(len(oldname)), oldname.encode("ascii"))

				status, data = net_op.create_http_request(constant.SERVER_URL,
					"POST",
					"/client/virus_upload",
					sha256 + oldname_len + oldname + content)

				return data

		return None

	def detect_file_sha256(self, sha256):
		if sha256:
			status, data = net_op.create_http_request(constant.SERVER_URL,
				"POST",
				"/client/virus_report",
				urllib.parse.urlencode({'sha256': sha256}),
				{"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"})

			#if isinstance(data, bytes):
			#	data = data.decode()

			return data

		return None
		
	def get_ip_report(self, ip):
		status, data = net_op.create_http_request(constant.SERVER_URL,
			"POST",
			"/client/ip_report",
			urllib.parse.urlencode({'ip': ip}),
			{"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"})

		return data

	def get_ip_geo(self, ip):
		status, data = net_op.create_http_request(constant.SERVER_URL,
			"POST",
			"/client/ip_geo",
			urllib.parse.urlencode({'ip': ip}),
			{"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"})

		return data

	def publish_threat(self, threat_id, threat):
		warning, score = KScore().get_status()
		status, data = net_op.create_http_request(constant.SERVER_URL,
			"POST",
			"/client/publish_threat",
			urllib.parse.urlencode({'score': score,
							'threat_id': threat_id,
							'threat': json.dumps(threat).encode("ascii"),
							'info': json.dumps(KInformation().get_info()).encode("ascii")}),
			{"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"})
