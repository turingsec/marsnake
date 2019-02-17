from utils import common
from core.db import Kdatabase
from utils.singleton import singleton
from config import constant
import platform, uuid, getpass

@singleton
class KInformation():
	def __init__(self):
		pass
		
	def get_info(self):
		macaddr = uuid.getnode()
		macaddr = ':'.join(("%012X" % macaddr)[i : i + 2] for i in range(0, 12, 2))
		
		fingerprint = Kdatabase().get_obj("fingerprint")

		return {
			"user_id" : Kdatabase().get_obj("setting")["username"],
			"fullname" : Kdatabase().get_obj("setting")["username"],
			"distro" : common.get_distribution(),
			"os_name" : platform.system(),
			"macaddr" : macaddr,
			"user" : getpass.getuser(),
			"localip" : common.get_ip_gateway(),
			"hostname" : platform.node(),
			"platform" : platform.platform(),
			"version" : constant.VERSION,
			"open_ports" : len(fingerprint["port"]["current"]),
			"accounts" : len(fingerprint["account"]["current"]),
			"uuid" : Kdatabase().get_obj("basic")["uuid"],
			"startup_counts": Kdatabase().get_obj("basic")["startup_counts"]
		}
