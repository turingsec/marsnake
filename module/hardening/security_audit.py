from core.language import Klanguage
from core.db import Kdatabase

def run(payload, socket):
	response = {
		'cmd_id' : payload['cmd_id'],
		"session_id" : payload["args"]["session_id"],
		"name" : [Klanguage().to_ts(1114), Klanguage().to_ts(1115), Klanguage().to_ts(1116)],
	}

	audit = Kdatabase().get_obj('audit')
	response['feature'] = audit['feature']
	response['authentication'] = audit['authentication']
	response['kernel'] = audit['kernel']

	socket.response(response)
