import psutil
from utils import common

def disk_status(response):
    #name    STATS   USED    MOUNT   FILESYSTEM
    for item in psutil.disk_partitions():
        device, mountpoint, fstype, opts = item
        
        try:
            total, used, free, percent = psutil.disk_usage(mountpoint)
            
            response["disk"][device] = {
                "fstype" : fstype,
                "total" : common.size_human_readable(total),
                "percent" : percent,
                "mountpoint" : mountpoint,
                "opts" : opts
            }
        except Exception:
            pass
            
def run(payload, socket):
    
    response = {
        "cmd_id" : payload["cmd_id"],
        "session_id" : payload["args"]["session_id"],
        "disk" : {},
        "error" : ""
    }
    
    disk_status(response)
    
    socket.response(response)