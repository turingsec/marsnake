from ctypes import *
from ctypes.wintypes import *

NOTIFYBUF_SZ = 2 * 1024 + 12

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
GENERIC_EXECUTE = 0x20000000
GENERIC_ALL = 0x10000000
FILE_LIST_DIRECTORY = 0x1
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
FILE_SHARE_DELETE = 4
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OVERLAPPED = 0x40000000
FILE_NOTIFY_CHANGE_FILE_NAME   = 0x00000001   
FILE_NOTIFY_CHANGE_DIR_NAME    = 0x00000002   
FILE_NOTIFY_CHANGE_ATTRIBUTES  = 0x00000004   
FILE_NOTIFY_CHANGE_SIZE        = 0x00000008   
FILE_NOTIFY_CHANGE_LAST_WRITE  = 0x00000010   
FILE_NOTIFY_CHANGE_LAST_ACCESS = 0x00000020   
FILE_NOTIFY_CHANGE_CREATION    = 0x00000040   
FILE_NOTIFY_CHANGE_SECURITY    = 0x00000100
FILE_ACTION_ADDED = 0x1
FILE_ACTION_REMOVED = 0x2
FILE_ACTION_MODIFIED = 0x3
FILE_ACTION_RENAMED_OLD_NAME = 0x4
FILE_ACTION_RENAMED_NEW_NAME = 0x5

class FILE_NOTIFY_INFORMATION(Structure):
	_fields_ = [('NextEntryOffset', DWORD),\
				('Action', DWORD),\
				('FileNameLength', DWORD),\
				('FileName', (c_wchar * 1024))]#LPCWSTR)]

def OutputResult(ResStr):
	print ResStr
	
class filesystem_change():
	def __init__(self, file_created_captured, file_modified_captured):
		self.WATCHDIR = u'C:\\Users'#u'F:\\'

		self.file_created_captured = file_created_captured
		self.file_modified_captured = file_modified_captured

	def do(self):
		while True:
			self.GetFileChanges()

	def GetResult(self, notify):
		pnotify = pointer(notify)

		while True:
			if pnotify.contents.FileNameLength != 0:
				fLength = pnotify.contents.FileNameLength
				FileNameStr = u''

				for i in pnotify.contents.FileName:
					if fLength <= 0:
						break

					fLength -= 1
					FileNameStr += i
			else:
				FileNameStr = u''

			if pnotify.contents.Action == FILE_ACTION_ADDED:
				OutputResult("[*]Detect Added File! File Name is %s" % FileNameStr)
				self.file_created_captured(FileNameStr)

			elif pnotify.contents.Action == FILE_ACTION_REMOVED:
				OutputResult("[*]Detect File Removed! File Name is %s" % FileNameStr)

			elif pnotify.contents.Action == FILE_ACTION_MODIFIED:
				OutputResult("[*]Detect File Modified! File Name is %s" % FileNameStr)
				self.file_modified_captured(FileNameStr)

			elif pnotify.contents.Action == FILE_ACTION_RENAMED_OLD_NAME:
				OutputResult("[*]Detect File Rename Operation! File Oldname is %s" % FileNameStr)

			elif pnotify.contents.Action == FILE_ACTION_RENAMED_NEW_NAME:
				OutputResult("[*]Detect File Rename Operation! File Newname is %s" % FileNameStr)

			else:
				OutputResult("[!]Return Wrong Action Type!")

			if pnotify.contents.NextEntryOffset == 0:
				break
			else:
				pp = cast(pnotify, c_voidp).value + pnotify.contents.NextEntryOffset
				pnotify = cast(pp, POINTER(FILE_NOTIFY_INFORMATION))

	def GetFileChanges(self):
		CreateFileW = windll.kernel32.CreateFileW
		CreateFileW.argtypes = [LPCWSTR ,DWORD ,DWORD ,c_void_p ,DWORD ,DWORD ,HANDLE]
		CreateFileW.restype = HANDLE

		ReadDirectoryChangesW = windll.kernel32.ReadDirectoryChangesW
		ReadDirectoryChangesW.argtypes = [HANDLE ,LPVOID ,DWORD ,BOOL ,DWORD ,POINTER(DWORD) ,c_void_p ,c_void_p]
		ReadDirectoryChangesW.restype = BOOL

		hMonFile = CreateFileW(self.WATCHDIR ,\
							GENERIC_READ|GENERIC_WRITE|FILE_LIST_DIRECTORY ,\
							FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE ,\
							None ,\
							OPEN_EXISTING ,\
							FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OVERLAPPED ,\
							None)

		if hMonFile == -1:
			OutputResult("[!]CreateFile Failed")
			return 0

		#notify = (BYTE * NOTIFYBUF_SZ)()
		notify = FILE_NOTIFY_INFORMATION()
		pnotify = pointer(notify)
		RetBytes = DWORD(0)
		RetDirChangs = ReadDirectoryChangesW(hMonFile,\
							pnotify,\
							NOTIFYBUF_SZ,\
							True,\
							FILE_NOTIFY_CHANGE_FILE_NAME|FILE_NOTIFY_CHANGE_LAST_WRITE|\
							FILE_NOTIFY_CHANGE_DIR_NAME|FILE_NOTIFY_CHANGE_ATTRIBUTES|\
							FILE_NOTIFY_CHANGE_SIZE|FILE_NOTIFY_CHANGE_LAST_ACCESS|\
							FILE_NOTIFY_CHANGE_CREATION|FILE_NOTIFY_CHANGE_SECURITY,\
							byref(RetBytes),\
							None,\
							None)

		if not RetDirChangs:
			OutputResult("[!]ReadDirectoryChanges Failed!Error Code:%d."%windll.kernel32.GetLastError())
			return 0

		if RetBytes == 0:
			OutputResult("[!]Read Changes Return Null!")
			return 0

		self.GetResult(notify)