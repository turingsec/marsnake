from utils import common, file_op
from core import logger

if 'win32' == sys.platform:
    import _winreg
    import pywintypes
    import win32api
    import win32con
    import win32file
    import win32gui
    import win32process

    from ctypes import windll, c_ulong, c_buffer, byref, sizeof
    from win32com.shell import shell, shellcon

    psapi = windll.psapi
    kernel = windll.kernel32

def setup_environment():
    """Define any extra environment variables for use in CleanerML and Winapp2.ini"""
    csidl_to_environ('commonappdata', shellcon.CSIDL_COMMON_APPDATA)
    csidl_to_environ('documents', shellcon.CSIDL_PERSONAL)
    # Windows XP does not define localappdata, but Windows Vista and 7 do
    csidl_to_environ('localappdata', shellcon.CSIDL_LOCAL_APPDATA)
    csidl_to_environ('music', shellcon.CSIDL_MYMUSIC)
    csidl_to_environ('pictures', shellcon.CSIDL_MYPICTURES)
    csidl_to_environ('video', shellcon.CSIDL_MYVIDEO)
    # LocalLowAppData does not have a CSIDL for use with
    # SHGetSpecialFolderPath. Instead, it is identified using
    # SHGetKnownFolderPath in Windows Vista and later
    try:
        path = get_known_folder_path('LocalAppDataLow')
    except:
        logger().error('exception identifying LocalAppDataLow')
    else:
        set_environ('LocalAppDataLow', path)


def csidl_to_environ(varname, csidl):
    """Define an environment variable from a CSIDL for use in CleanerML and Winapp2.ini"""
    try:
        sppath = shell.SHGetSpecialFolderPath(None, csidl)
    except:
        logger().error('exception when getting special folder path for %s', varname)
        return

    # there is exception handling in set_environ()
    set_environ(varname, sppath)

def set_environ(varname, path):
    """Define an environment variable for use in CleanerML and Winapp2.ini"""
    if not path:
        return

    if varname in os.environ:
        #logger.debug('set_environ(%s, %s): skipping because environment variable is already defined', varname, path)
        if 'nt' == os.name:
            os.environ[varname] = common.expandvars(u'%%%s%%' % varname).encode('utf-8')
        # Do not redefine the environment variable when it already exists
        # But re-encode them with utf-8 instead of mbcs
        return
    try:
        if not os.path.exists(path):
            raise RuntimeError('Variable %s points to a non-existent path %s' % (varname, path))
        os.environ[varname] = path.encode('utf8')
    except:
        logger().error('set_environ(%s, %s): exception when setting environment variable', varname, path)

def get_known_folder_path(folder_name):
    """Return the path of a folder by its Folder ID
    
    Requires Windows Vista, Server 2008, or later
    
    Based on the code Michael Kropat (mkropat) from
    <https://gist.github.com/mkropat/7550097>
    licensed  under the GNU GPL"""
    import ctypes
    from ctypes import wintypes
    from uuid import UUID

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", wintypes.BYTE * 8)
        ]

        def __init__(self, uuid_):
            ctypes.Structure.__init__(self)
            self.Data1, self.Data2, self.Data3, self.Data4[
                0], self.Data4[1], rest = uuid_.fields
            for i in range(2, 8):
                self.Data4[i] = rest >> (8 - i - 1) * 8 & 0xff

    class FOLDERID:
        LocalAppDataLow = UUID(
            '{A520A1A4-1780-4FF6-BD18-167343C5AF16}')

    class UserHandle:
        current = wintypes.HANDLE(0)

    _CoTaskMemFree = windll.ole32.CoTaskMemFree
    _CoTaskMemFree.restype = None
    _CoTaskMemFree.argtypes = [ctypes.c_void_p]

    try:
        _SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
    except AttributeError:
        # Not supported on Windows XP
        return None
    _SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(
            ctypes.c_wchar_p)
    ]

    class PathNotFoundException(Exception):
        pass

    folderid = getattr(FOLDERID, folder_name)
    fid = GUID(folderid)
    pPath = ctypes.c_wchar_p()
    S_OK = 0

    if _SHGetKnownFolderPath(ctypes.byref(fid), 0, UserHandle.current, ctypes.byref(pPath)) != S_OK:
        raise PathNotFoundException(folder_name)

    path = pPath.value
    _CoTaskMemFree(pPath)

    return path

def get_recycle_bin():
    """Yield a list of files in the recycle bin"""
    pidl = shell.SHGetSpecialFolderLocation(0, shellcon.CSIDL_BITBUCKET)
    desktop = shell.SHGetDesktopFolder()
    h = desktop.BindToObject(pidl, None, shell.IID_IShellFolder)
    for item in h:
        path = h.GetDisplayNameOf(item, shellcon.SHGDN_FORPARSING)
        if os.path.isdir(path):
            for child in file_op.children_in_directory(path, True):
                yield child
            yield path
        else:
            yield path