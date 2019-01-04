from core.virusScan import KvirusScanner, OPERATION_MOVETO
import os


def run(payload, socket):
    filepath = payload['args']['filepath']
    response = {
        'cmd_id': payload['cmd_id'],
        "session_id": payload["args"]["session_id"],
        'filepath': filepath
    }
    newpath = payload['args']['topath']
    if newpath == 'desktop':
        newpath = os.path.join(os.path.expanduser('~'), 'Desktop')
    elif newpath == 'document':
        newpath = os.path.join(os.path.expanduser('~'), 'Documents')

    if not KvirusScanner().isFilepathLegal(filepath):
        response['error'] = "Illegal filepath:{}.".format(filepath)
    elif not KvirusScanner().isFilepathLegal(newpath):
        if not os.path.isdir(newpath) or os.path.exists(newpath):
            response['error'] = response['error'] + \
                " Illegal topath:{}.".format(newpath)
    else:
        ret = KvirusScanner().handleVirus(filepath,
                                          newpath=newpath,
                                          operation=OPERATION_MOVETO)
        if ret:
            response['error'] = ret

    if 'ticket' in payload['args']:
        response['ticket'] = payload['args']['ticket']
        
    socket.response(response)
