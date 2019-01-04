import os

class Magic(object):
    def __init__(self):
        pass

    def from_file(self,filepath):
        header = ''
        try:
            with open(filepath,'rb') as f:
                header = f.read(10)
        except Exception as e:
            pass

        if header:
            if header.startswith(b'MZ\x90\x00'):
                return 'PE32+ executable for Windows'
            elif header.startswith(b'\x7fELF'):
                return 'ELF LSB shared object for Linux'
            else:
                return ''
        return ''