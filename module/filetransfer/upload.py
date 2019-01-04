from core.icloud import Kicloud

def run(payload, socket):
	Kicloud().uploading(payload["args"], socket)
