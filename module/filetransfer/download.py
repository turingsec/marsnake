from core.icloud import Kicloud

def run(payload, socket):
	Kicloud().download(payload, socket)
