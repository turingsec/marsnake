from core.ptys import Kptys

def run(payload, socket):
    
    args = payload["args"]
    size = args["data"]
    
    if len(size) == 5 and size[0] == "set_size":
        Kptys().resize(size[1], size[2], size[3], size[4])
