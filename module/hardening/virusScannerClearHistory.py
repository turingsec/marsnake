from core.virusScan import KvirusScanner


def run(payload, socket):
    response = {
        'cmd_id': payload['cmd_id'],
        "session_id": payload["args"]["session_id"],
    }
    ret = KvirusScanner().clearHistory()

    if ret:
        response['error'] = ret


    if 'ticket' in payload['args']:
        response['ticket'] = payload['args']['ticket']

    socket.response(response)
