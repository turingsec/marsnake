from utils import common
from core.db import Kdatabase

def cpu_usage(response, monitor_second):
    response["cpu"] = common.extend_at_front(monitor_second["cpu"], 10, 0)

def ram_usage(response, monitor_second):
    response["memory"] = common.extend_at_front(monitor_second["memory"], 10, 0)

def disk_usage(response, monitor_second):
    response["disk"]["read"] = common.extend_at_front(monitor_second["disk_io"]["read"], 10, 0)
    response["disk"]["write"] = common.extend_at_front(monitor_second["disk_io"]["write"], 10, 0)
    
def network_usage(response, monitor_second):
    response["network"]["tx"] = common.extend_at_front(monitor_second["net_io"]["tx"], 10, 0)
    response["network"]["rx"] = common.extend_at_front(monitor_second["net_io"]["rx"], 10, 0)
    
def run(payload, socket):
    
    response = {
        "cmd_id" : payload["cmd_id"],
        "session_id" : payload["args"]["session_id"],
        "cpu" : 0,
        "memory" : 0,
        "disk" : {
            "read" : 0,
            "write" : 0
        },
        "network" : {
            "tx" : 0,
            "rx" : 0
        },
        "error" : ""
    }
    
    monitor_second = Kdatabase().get_monitor_second()
    
    cpu_usage(response, monitor_second)
    ram_usage(response, monitor_second)
    disk_usage(response, monitor_second)
    network_usage(response, monitor_second)

    socket.response(response)