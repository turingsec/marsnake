from utils import common

class usb_detect():
    def __init__(self, usb_plugged, usb_unplugged):
        if common.is_windows():
            from . import usb_detect_win as usb_detect_proxy
        elif common.is_linux():
            from . import usb_detect_linux as usb_detect_proxy
        else:
            raise "No support os " + __NAME__
        
        self.name = "USB detector"
        self.proxy = usb_detect_proxy
        self.usb_plugged = usb_plugged
        self.usb_unplugged = usb_unplugged

    def init(self):
        try:
            self.obj = self.proxy.usb_detect(self.usb_plugged, self.usb_unplugged)
        except Exception as e:
            return False

        return True

    def do(self):
        self.obj.do()
