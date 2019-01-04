from utils import common
from core.icloud import Kicloud

def run(payload, socket):

	Kicloud().init(payload["args"]["pair_id"], payload["args"]["device_id"],
		payload["args"]["server_ip"], payload["args"]["server_port"])
