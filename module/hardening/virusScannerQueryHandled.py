from core.db import Kdatabase
from core.virusScan import RESERVERED_WHEN_CLEARED_HISTORY


def run(payload, socket):
    response = {
        'cmd_id': payload['cmd_id'],
        "session_id": payload["args"]["session_id"],
    }

    virus = Kdatabase().get_obj('virus')
    handledList = list(virus['untrustList'].values())
    # ignore reserved items.
    for key in virus['handledList']:
        if virus['handledList'][key][-1] != RESERVERED_WHEN_CLEARED_HISTORY:
            handledList.append(virus['handledList'][key])

    response['handledList'] = handledList

    if 'ticket' in payload['args']:
        response['ticket'] = payload['args']['ticket']

    socket.response(response)
