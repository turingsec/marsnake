from utils import common, time_op
from datetime import datetime
from core.db import Kdatabase
from core.language import Klanguage

def average(result, minutes):
    if minutes == 1:
        return result

    total = 0
    count = 0
    real_count = 0
    result2 = []

    for i in range(len(result)):
        total += result[i]["value"]
        count += 1

        if result[i]["real"]:
            real_count += 1

        if count == minutes:
            result2.append({
                "time" : result[i]["time"],
                "value" : round(total / count, 2),
                "real" : True if real_count > 0 else False
            })

            total = 0
            count = 0
            real_count = 0
        else:
            if (i + 1) == len(result):
                result2.append({
                    "time" : result[i]["time"],
                    "value" : round(total / count, 2),
                    "real" : True if real_count > 0 else False
                })

    return result2

def find_index_by_time(monitor, time, start):
    if start < 0:
        start = 0

    for i in range(start, monitor["minutes"]):
        if time == monitor["times"][i]:
            return i

    return -1

def get_usage(kind, begin, end, response):
    if not begin or not end:
        response["error"] = Klanguage().to_ts(4004)
        return

    if end <= begin:
        response["error"] = Klanguage().to_ts(4004)
        return

    monitor = Kdatabase().get_obj("monitor")
    obj = None

    if kind == "cpu":
        obj = monitor["cpu"]
    elif kind == "memory":
        obj = monitor["memory"]
    elif kind == "net_tx":
        obj = monitor["net_io"]["tx"]
    elif kind == "net_rx":
        obj = monitor["net_io"]["rx"]
    elif kind == "disk_read":
        obj = monitor["disk_io"]["read"]
    elif kind == "disk_write":
        obj = monitor["disk_io"]["write"]
    else:
        return

    result = []
    index = 0

    begin = time_op.get_last_min(begin)
    end = time_op.get_last_min(end)

    #print("begin {}".format(datetime.fromtimestamp(begin)))
    #print("end {}".format(datetime.fromtimestamp(end)))

    '''
        6hours      2day        7days
        min         10min       hour
    '''
    delta = end - begin

    if delta <= 6 * 3600:
        interval = 1
        response["granularity"] = 0
    elif delta <= 2 * 24 * 3600:
        begin -= 9 * 60
        interval = 10
        response["granularity"] = 1
    elif delta <= 7 * 24 * 3600:
        begin -= 59 * 60
        interval = 60
        response["granularity"] = 2
    else:
        response["error"] = Klanguage().to_ts(4004)
        return

    for i in range(begin, end, 60):
        index = find_index_by_time(monitor, i, index)

        if index != -1:
            result.append({
                "time" : i,
                "value" : obj[index],
                "real" : True
            })
        else:
            result.append({
                "time" : i,
                "value" : 0,
                "real" : False
            })

    #print("begin2 {}".format(datetime.fromtimestamp(result[0]["time"])))
    #print("end2 {}".format(datetime.fromtimestamp(result[len(result) - 1]["time"])))

    response["usage"] = average(result, interval)
    response["kind"] = kind

def run(payload, socket):

    response = {
        "cmd_id" : payload["cmd_id"],
        "session_id" : payload["args"]["session_id"],
        "usage" : [],
        "granularity" : None,
        "kind" : None,
        "error" : ""
    }

    get_usage(payload["args"]["kind"], payload["args"]["begin"], payload["args"]["end"], response)

    socket.response(response)
