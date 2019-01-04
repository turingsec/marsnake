from core.virusScan import KvirusScanner, OPERATION_UNTRUST


def run(payload, socket):
    filepath = payload['args']['filepath']
    response = {
        'cmd_id': payload['cmd_id'],
        "session_id": payload["args"]["session_id"],
        'filepath': filepath
    }

    if not KvirusScanner().isFilepathLegal(filepath):
        response['error'] = "Illegal filepath!"
    elif payload['args']['isWhitelist']:
        ret = KvirusScanner().delWhiteList(filepath)
        if ret:
            response['error'] = ret
    else:
        KvirusScanner().handleVirus(filepath, operation = OPERATION_UNTRUST)

    if 'ticket' in payload['args']:
        response['ticket'] = payload['args']['ticket']

    socket.response(response)
