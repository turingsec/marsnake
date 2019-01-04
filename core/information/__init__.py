from utils import common
from core.configuration import Kconfig
from core.db import Kdatabase
from core.profile_reader import KProfile
from utils.singleton import singleton
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
			"user_id" : KProfile().read_key("username"),
			"fullname" : KProfile().read_key("fullname"),
			"distro" : common.get_distribution(),
			"os_name" : platform.system(),
			"macaddr" : macaddr,
			"user" : getpass.getuser(),
			"localip" : common.get_ip_gateway(),
			"hostname" : platform.node(),
			"platform" : platform.platform(),
			"version" : Kconfig().read_version(),
			"open_ports" : len(fingerprint["port"]["current"]),
			"accounts" : len(fingerprint["account"]["current"]),
			"uuid" : Kdatabase().get_obj("basic")["uuid"]
		}
