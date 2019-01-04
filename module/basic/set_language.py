from core.language import Klanguage

def run(payload, socket):
	Klanguage().set_lang(payload["args"]["lang"]);