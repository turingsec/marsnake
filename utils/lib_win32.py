from ctypes import windll, WinError, create_string_buffer, byref, c_uint32, GetLastError
import locale

os_encoding = locale.getpreferredencoding() or "utf8"

def get_user_name():
    global os_encoding

    DWORD = c_uint32
    nSize = DWORD(0)
    windll.advapi32.GetUserNameA(None, byref(nSize))
    error = GetLastError()

    ERROR_INSUFFICIENT_BUFFER = 122
    if error != ERROR_INSUFFICIENT_BUFFER:
        raise WinError(error)

    lpBuffer = create_string_buffer('', nSize.value + 1)
    success = windll.advapi32.GetUserNameA(lpBuffer, byref(nSize))

    if not success:
        raise WinError()

    return lpBuffer.value.decode(encoding = os_encoding).encode("utf8")