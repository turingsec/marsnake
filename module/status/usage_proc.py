from utils import common
from datetime import datetime
from core.db import Kdatabase

def find_index_by_time(monitor, time):
    for i in range(monitor["minutes"]):
        if time == monitor["times"][i]:
            return i
            
    return -1
    
def get_usage_proc(point, granularity, response):
    monitor = Kdatabase().get_obj("monitor")
    valid = False
    
    if granularity == 0:
        index = find_index_by_time(monitor, point)
        
        if index != -1:
            procs = {
                "time" : [point],
                "value" : monitor["procs"][index]
            }
            
            valid = True
    else:
        if granularity == 1:
            begin = point - 10 * 60
        elif granularity == 2:
            begin = point - 60 * 60
        else:
            return
            
        tmp = {}
        procs = {
            "time" : [begin, point],
            "value" : {}
        }
        
        for i in range(begin, point, 60):
            index = find_index_by_time(monitor, i)
            
            if index != -1:
                procs_obj = monitor["procs"][index]
                
                for pid, proc_data in procs_obj.items():
                    if not pid in tmp:
                        tmp[pid] = {
                            "name" : proc_data[0],
                            "username" : proc_data[1],
                            "cpu" : proc_data[2],
                            "memory" : proc_data[3],
                            "io_read" : proc_data[4],
                            "io_write" : proc_data[5],
                            "count" : 1
                        }
                    else:
                        tmp[pid]["cpu"] += proc_data[2]
                        tmp[pid]["memory"] += proc_data[3]
                        tmp[pid]["io_read"] += proc_data[4]
                        tmp[pid]["io_write"] += proc_data[5]
                        tmp[pid]["count"] += 1
                        
                valid = True
                
        for pid, proc_data in tmp.items():
            procs["value"][pid] = [proc_data["name"],
                        proc_data["username"],
                        round(proc_data["cpu"] / proc_data["count"], 2),
                        round(proc_data["memory"] / proc_data["count"], 2),
                        round(proc_data["io_read"] / proc_data["count"], 2),
                        round(proc_data["io_write"] / proc_data["count"], 2),
                        0,
                        0]
                        
    if not valid:
        response["error"] = "No Data Found"
        return
        
    response["procs"] = procs
    
def run(payload, socket):
    
    response = {
        "cmd_id" : payload["cmd_id"],
        "session_id" : payload["args"]["session_id"],
        "procs" : {},
        "error" : ""
    }
    
    get_usage_proc(payload["args"]["point"], payload["args"]["granularity"], response)
    
    socket.response(response)