import random

def colorize(s, color):
    if s is None:
        return ""

    if type(s) not in (str, unicode):
        s = str(s)

    res = s
    COLOR_STOP = "\033[0m"

    if color.lower() == "random":
        color = random.choice(["blue","red","green","yellow"])

    if color.lower() == "blue":
        res = "\033[34m" + s + COLOR_STOP
    elif color.lower() == "red":
        res = "\033[31m" + s + COLOR_STOP
    elif color.lower() == "lightred":
        res = "\033[31;1m" + s + COLOR_STOP
    elif color.lower() == "green":
        res = "\033[32m" + s + COLOR_STOP
    elif color.lower() == "lightgreen":
        res = "\033[32;1m" + s + COLOR_STOP
    elif color.lower() == "yellow":
        res = "\033[33m" + s + COLOR_STOP
    elif color.lower() == "lightyellow":
        res = "\033[1;33m" + s + COLOR_STOP
    elif color.lower() == "magenta":
        res = "\033[35m" + s + COLOR_STOP
    elif color.lower() == "cyan":
        res = "\033[36m" + s + COLOR_STOP
    elif color.lower() == "grey":
        res = "\033[37m" + s + COLOR_STOP
    elif color.lower() == "darkgrey":
        res = "\033[1;30m" + s + COLOR_STOP

    return res