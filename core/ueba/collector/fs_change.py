from utils import common

class fs_change():
    def __init__(self, file_created_captured, file_modified_captured):
        if common.is_windows():
            from . import fs_change_win as fs_change_proxy
        elif common.is_linux():
            from . import fs_change_linux as fs_change_proxy
        else:
            raise "No support os " + __NAME__

        self.name = "Filesystem monitor"
        self.proxy = fs_change_proxy
        self.file_created_captured = file_created_captured
        self.file_modified_captured = file_modified_captured

    def init(self):
        try:
            self.obj = self.proxy.filesystem_change(self.file_created_captured, self.file_modified_captured)
        except Exception as e:
            print(e)
            return False
            
        return True

    def do(self):
        self.obj.do()
