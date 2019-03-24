from utils.singleton import singleton
from core.db import Kdatabase
from core.ueba import macro
from core.baseline import macro as baseline_macro
import math

def lost_score_correction(score, coefficient):
	temp = score / 100

	if temp > 1:
		temp = 1

	return math.ceil(100 * coefficient * temp)

class KcleanerScore(object):
	"""used for kcleaner"""
	def __init__(self):
		self.coefficient = 0.1

	def get_history(self):
		cleaner = Kdatabase().get_obj("cleaner")
		record = cleaner["record"]
		total_size = 0

		for i in record:
			total_size += i["size"]

		return total_size

	def get_warning_and_score(self):
		cleaner = Kdatabase().get_obj("cleaner")
		kinds_db = cleaner['kinds']
		totalsize = 0

		for i,item in kinds_db.items():
			totalsize += item['size']

		garbage_128M = (totalsize >> 27)
		lost_score = lost_score_correction(garbage_128M * 5, self.coefficient)

		return "cleaner", totalsize, lost_score, cleaner["lasttime"]

class KuebaScore(object):
	"""used for vuls"""
	def __init__(self):
		self.coefficient = 0.3

	def get_history(self):
		ueba = Kdatabase().get_obj("ueba")
		count = 0

		for key, story in ueba["storys"].items():
			if story["resolved"]:
				count += 1

		return count

	def get_warning_and_score(self):
		ueba = Kdatabase().get_obj("ueba")
		kind = [0 for x in range(macro.STORY_KIND["MAX"])]
		lost_score = 0

		for key, story in ueba["storys"].items():
			if not story["resolved"]:
				kind[story["kind"]] += 1
				lost_score += story["score"]

		lost_score = lost_score_correction(lost_score, self.coefficient)

		return "ueba", kind, lost_score, ueba["lasttime"]

class KvulsScore(object):
	"""used for vuls"""
	def __init__(self):
		self.coefficient = 0.2

	def get_history(self):
		vuls = Kdatabase().get_obj("vuls")
		return len(vuls['repaired_packages'])

	def get_warning_and_score(self):
		vuls = Kdatabase().get_obj("vuls")
		result = len(vuls['items'])
		lost_score = lost_score_correction(result * 5, self.coefficient)

		return "vuls", len(vuls['items']), lost_score, vuls["lasttime"]

class KvirusScore(object):
	"""used for virus"""
	def __init__(self):
		self.coefficient = 0.2

	def get_history(self):
		virus = Kdatabase().get_obj('virus')
		return len(virus['allHistory'])

	def get_warning_and_score(self):
		virus = Kdatabase().get_obj('virus')
		result = len(virus['isolateList'])
		lost_score = lost_score_correction(result * 20, self.coefficient)

		return "virus", len(virus['isolateList']), lost_score, virus["lasttime"]

class KbaselineScore(object):
	"""used for baseline"""
	def __init__(self):
		self.coefficient = 0.1

	def calculate(self):
		baseline = Kdatabase().get_obj('baseline')
		high = 0
		medium = 0
		low = 0

		for i in baseline["risks"]:
			tmp = baseline["risks"][i]

			if tmp["stage"] == baseline_macro.BASELINE_STAGE["UNRESOLVED"]:
				if tmp["level"] == baseline_macro.BASELINE_LEVEL["LOW"]:
					low += 1

				if tmp["level"] == baseline_macro.BASELINE_LEVEL["MEDIUM"]:
					medium += 1

				if tmp["level"] == baseline_macro.BASELINE_LEVEL["HIGH"]:
					high += 1

		return high, medium, low, baseline["lasttime"]

	def get_warning_and_score(self):
		high, medium, low, lasttime = self.calculate()

		lost_score = high * 10 + medium * 5 + low * 2

		if medium > 5:
			lost_score += 10

		lost_score = lost_score_correction(lost_score, self.coefficient)

		return "baseline", {"high": high, "medium": medium, "low": low}, lost_score, lasttime

class KmonitorScore(object):
	"""used for monitor"""
	def __init__(self):
		self.coefficient = 0.1

	def get_warning_and_score(self):
		monitor = Kdatabase().get_obj('monitor')
		fingerprint = Kdatabase().get_obj('fingerprint')
		warnings = monitor["warnings"]

		cpu = len(warnings["cpu"])
		mem = len(warnings["memory"])
		disk = len(warnings["disk_io"])
		network = len(warnings["net_io"])
		port_change = len(fingerprint["port"]["change"])
		account_change = len(fingerprint["account"]["change"])

		lost_score = cpu * 30 + mem * 30 + disk * 10 + network * 10 + port_change * 20 + account_change * 20
		lost_score = lost_score_correction(lost_score, self.coefficient)

		return "monitor", {"cpu": cpu,
						"mem": mem,
						"disk": disk,
						"network": network,
						"port_change": port_change,
						"account_change": account_change}, lost_score, 0

@singleton
class KScore():
	def __init__(self):
		pass

	def get_status(self):
		lost_score = 0
		warning = {}
		maps = [KvirusScore(), KvulsScore(),
						KuebaScore(), KbaselineScore(), KmonitorScore()]

		for i in maps:
			key, value, temp_score, last_time = i.get_warning_and_score()
			lost_score += temp_score

			warning[key] = {
				"detail" : value,
				"last_time" : last_time
			}

		score = 100 - math.ceil(lost_score)

		if score < 0:
			score = 0

		return warning, score
