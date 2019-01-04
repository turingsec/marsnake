from core.db import Kdatabase
from utils.time_op import time2string


def run(payload, socket):
    response = {
        'cmd_id': payload['cmd_id'],
        "session_id": payload["args"]["session_id"],
    }

    virus = Kdatabase().get_obj('virus')
    response['isFinished'] = True if virus['finished'] else False
    response['lasttime'] = time2string(virus['lasttime'])
    response['lastpath'] = virus['lastScanedPath']
    response['searchedCount'] = virus['searchedCount']
    response['unHandledList'] = list(virus['isolateList'].values())

    if 'ticket' in payload['args']:
        response['ticket'] = payload['args']['ticket']

    socket.response(response)
