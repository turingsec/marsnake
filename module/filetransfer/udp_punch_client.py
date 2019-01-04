from utils import common
from core.icloud import Kicloud
from utils.randomize import Krandom

def run(payload, socket):
	Kicloud().punch_as_client(payload["args"]["pair_id"],
		payload["args"]["target_ip"],
		payload["args"]["target_port"],
		payload["args"]["random_code"])
