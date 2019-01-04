from core.db import Kdatabase


def run(payload, socket):
    response = {
        'cmd_id': payload['cmd_id'],
        "session_id": payload["args"]["session_id"],
    }

    whitelist = Kdatabase().get_obj('virus_whitelist')
    response['whitelist'] = [(i, whitelist[i][0], whitelist[i][1])
                             for i in whitelist]

    if 'ticket' in payload['args']:
        response['ticket'] = payload['args']['ticket']

    socket.response(response)
