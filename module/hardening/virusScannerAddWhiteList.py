from core.virusScan import KvirusScanner


def run(payload, socket):
    filepath = payload['args']['filepath']
    response = {
        'cmd_id': payload['cmd_id'],
        "session_id": payload["args"]["session_id"],
        'filepath': filepath
    }
    if not KvirusScanner().isFilepathLegal(filepath):
        response['error'] = "Illegal filepath!"
    else:
        ret = KvirusScanner().addWhiteList(filepath,
                                           payload['args']['isWhitelist'])
        if ret:
            response['error'] = ret

    if 'ticket' in payload['args']:
        response['ticket'] = payload['args']['ticket']

    socket.response(response)
