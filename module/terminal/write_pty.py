from core.ptys import Kptys

def run(payload, socket):
    
    args = payload["args"]
    data = args["data"]
    
    if len(data) == 2 and data[0] == "stdin":
        Kptys().write(data[1])
