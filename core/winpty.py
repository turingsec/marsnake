import threading
from subprocess import Popen, STDOUT, CREATE_NEW_CONSOLE, STARTUPINFO, STARTF_USESHOWWINDOW, SW_HIDE, CREATE_NEW_PROCESS_GROUP
from time import sleep
import win32process
import win32con
import win32gui
import win32api
import psutil
import win32pipe
import win32security
import win32file

def DebugOutput(x):
    win32api.OutputDebugString(x)

def get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        # if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
        # print hwnd
        if found_pid == pid:
            hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


class PtyProcess():

    def __init__(self):
        self.writelock = 0
        self.Console_hwnd = []
        self.dwProcessID=0
        self.hProcess=0
        self.write_handle=0
        self.read_handle=0
        self.stdin_write=0
        self.ascii = """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789
        ,./;'[]\\`-=<>?:\"{}|!@#$%^&*()_+~ \x09"""
        self.keyboardMap = {
            '\x1b\x5b\x33\x7e': self.keyDelete,
            '\x1b\x5b\x32\x7e': self.keyInset,
            '\x1b\x5b\x36\x7e': self.keyPageDown,
            '\x1b\x5b\x35\x7e': self.keyPageUp,
            '\x1b\x4f\x48': self.keyHome,
            '\x1b\x4f\x46': self.keyEnd,
            '\x1b\x5b\x44': self.keyLeft,
            '\x1b\x5b\x43': self.keyRight,
            '\x1b\x5b\x41': self.keyUP,
            '\x1b\x5b\x42': self.keyDown,
            '\x7f': self.keyBacksapce,
            '\x03': self.keyCtrlC}
        self.pipein = None
        self.pipeout = None
        self.lastline = ''
        self.writeline = ''
        self.curpoint = 0
        self.insertflag = 0
        self.writeBuffer = []
        self.writeBufferMaxLen = 50
        self.writeBufferIndexDefault = -1
        self.writeBufferIndex = self.writeBufferIndexDefault
        self.isInsertCurrentUnfinishedLine = 0
        self.tempUnfinishedLine = None

    def keyCtrlC(self):
        pids = psutil.pids()
        childpid = []
        try:
            for i in pids:
                p = psutil.Process(i)
                if p.ppid() == self.dwProcessID:
                    if p.name() == "conhost.exe":
                        continue
                    childpid.append(i)

            for i in childpid:
                Popen("taskkill /F /T /PID %i" % i, shell=True)
        except:
            pass

    def keyPageUp(self):
        pass

    def keyPageDown(self):
        pass

    def keyLeft(self):
        if self.curpoint == 0:
            pass
        else:
            offset = str(len(self.lastline)+self.curpoint-1+1)
            self.write_pipe("\x1b\x5b{}\x47".format(
                offset))  # relocate point
            self.curpoint -= 1

    def keyRight(self):
        if self.curpoint == len(self.writeline):
            pass
        else:
            offset = str(len(self.lastline)+self.curpoint+1+1)
            self.write_pipe("\x1b\x5b{}\x47".format(
                offset))  # relocate point
            self.curpoint += 1

    def keyBacksapce(self):
        if self.curpoint:
            self.clearLine()
            self.writeline = self.writeline[
                :self.curpoint-1]+self.writeline[self.curpoint:]
            self.write_pipe('\r'+self.lastline+self.writeline)
            self.curpoint -= 1
            offset = str(len(self.lastline)+1+self.curpoint)
            self.write_pipe("\x1b\x5b{}\x47".format(
                offset))  # relocate point

    def keyHome(self):
        if self.curpoint:
            offset = str(len(self.lastline)+1)
            self.write_pipe("\x1b\x5b{}\x47".format(
                offset))  # relocate point
            self.curpoint = 0

    def keyDelete(self):
        if self.curpoint == len(self.writeline):
            pass
        else:
            self.clearLine()
            self.writeline = '{}{}'.format(self.writeline[:self.curpoint],
                                           self.writeline[self.curpoint+1:])
            self.write_pipe('\r'+self.lastline+self.writeline)
            offset = str(len(self.lastline)+self.curpoint+1)
            self.write_pipe("\x1b\x5b{}\x47".format(
                offset))  # relocate point

    def keyInset(self):
        if self.insertflag:
            self.insertflag = 0
        else:
            self.insertflag = 1

    def keyEnd(self):
        offset = len(self.writeline)+len(self.lastline)+1
        self.write_pipe("\x1b\x5b{}\x47".format(offset))
        self.curpoint = len(self.writeline)

    def keyUP(self):
        content = self.PopWriteBufferContent(up=True)
        if not content == None:
            self.clearLine()
            self.writeline = content
            self.write_pipe('\r'+self.lastline+self.writeline)
            self.keyEnd()

    def keyDown(self):
        content = self.PopWriteBufferContent(up=False)
        if not content == None:
            self.clearLine()
            self.writeline = content
            self.write_pipe('\r'+self.lastline+self.writeline)
            self.keyEnd()

    def clearLine(self):
        # overflow old output with blank
        length = len(self.writeline)+len(self.lastline)+1
        self.write_pipe('\r{}'.format(' '*length))

    def InsertWriteBuffer(self):
        if len(self.writeline):
            if len(self.writeBuffer) < self.writeBufferMaxLen:
                self.writeBuffer.insert(0, self.writeline)
            else:
                self.writeBuffer.pop()
                self.writeBuffer.insert(0, self.writeline)
            self.writeBufferIndex = self.writeBufferIndexDefault

    def PopWriteBufferContent(self, up=True):
        DebugOutput(self.writeBuffer)
        length = len(self.writeBuffer)
        content = None
        if 0 == length:
            return None
        if up:
            if self.isInsertCurrentUnfinishedLine == 0:
                self.tempUnfinishedLine = self.writeline
                self.isInsertCurrentUnfinishedLine = 1
                # print "is inserted"

            self.writeBufferIndex += 1
            if self.writeBufferIndex >= length:
                self.writeBufferIndex = length-1
                return None
            content = self.writeBuffer[self.writeBufferIndex]
        else:
            if self.isInsertCurrentUnfinishedLine == 0:
                return None
            self.writeBufferIndex -= 1
            if self.writeBufferIndex == -1:
                content = self.tempUnfinishedLine
            elif self.writeBufferIndex <= -2:
                self.writeBufferIndex = -1
                return None
            else:
                content = self.writeBuffer[self.writeBufferIndex]
        return content

    def sendkey(self, char):
        win32file.WriteFile(self.stdin_write, char, None)
        # hwnd = self.Console_hwnd[0]
        # code = ord(char)

        # win32api.SendMessage(hwnd, win32con.WM_CHAR, code, 0)

    def sendkeypress(self, key):
        hwnd = self.Console_hwnd[0]

        # win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, key, 0)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, key, 0)

    def start(self, cmd):
        sAttr = win32security.SECURITY_ATTRIBUTES()
        sAttr.bInheritHandle = True

        stdout_r, stdout_w = win32pipe.CreatePipe(sAttr,0)
        stdin_r, stdin_w = win32pipe.CreatePipe(sAttr,0)
        self.read_handle=stdout_r
        self.write_handle=stdout_w
        self.stdin_write=stdin_w

        si = win32process.STARTUPINFO()
        si.dwFlags = win32process.STARTF_USESHOWWINDOW | win32process.STARTF_USESTDHANDLES
        si.wShowWindow = win32con.SW_HIDE
        si.hStdInput = stdin_r            # file descriptor of origin stdin
        si.hStdOutput = stdout_w
        si.hStdError = stdout_w
        hProcess, hThread, dwProcessID, dwThreadID = win32process.CreateProcess(None,"cmd", None, None, True, win32process.CREATE_NEW_CONSOLE, None, None, si)
        self.dwProcessID=dwProcessID
        self.hProcess=hProcess
        sleep(0.5)
        if self.hProcess == 0:
            DebugOutput("Start Process Fail:{:d}".format(win32api.GetLastError()))
        DebugOutput('[*] pid: {:x}'.format(self.dwProcessID))
        self.Console_hwnd = get_hwnds_for_pid(self.dwProcessID)
        if len(self.Console_hwnd)==0:
            raise Exception("Fail to run,No Process!")
        DebugOutput('[*] hwnd:{:x}'.format(self.Console_hwnd[0]))

    def isalive(self):
        return win32process.GetExitCodeProcess(self.hProcess) == win32con.STILL_ACTIVE

    def read_pipe(self,size):
        return win32file.ReadFile(self.read_handle, size, None)[1]

    def write_pipe(self,data):
        return win32file.WriteFile(self.write_handle, data, None)

    @classmethod
    def spawn(self, argv, env=None, cwd=None):
        myself = self()
        DebugOutput(str(argv))
        try:
            myself.start(argv[0])
        except Exception as e:
            DebugOutput("Create Error:")
            DebugOutput(str(e))
            DebugOutput(self.read_pipe(1024))
            DebugOutput("finish")

        return myself

    def kill(self, sig):
        Popen("taskkill /F /T /PID %i" % self.dwProcessID, shell=True)
        win32api.CloseHandle(self.stdin_write)
        win32api.CloseHandle(self.write_handle)

    def close(self):
        pass

    def write(self, cmd):
        i = cmd[0]
        if i == '\x0d':
            self.InsertWriteBuffer()
            for char in self.writeline:
                self.sendkey(char)

            self.write_pipe('\x0d\x0a')
            self.sendkey('\x0d')
            self.sendkey('\x0a')
            self.writeline = ''
            self.curpoint = 0
            self.writelock = 0
            self.isInsertCurrentUnfinishedLine = 0

        elif i in self.ascii:
            if i == '\x09':  # replace tab as 2 space
                i = '  '
            self.writelock = 1
            if self.insertflag:
                self.writeline = '{}{}{}'.format(self.writeline[:self.curpoint],
                                                 i, self.writeline[self.curpoint+1:])
            else:
                self.writeline = '{}{}{}'.format(self.writeline[:self.curpoint],
                                                 i, self.writeline[self.curpoint:])
            if i == '\x09':
                self.curpoint += 2
            else:
                self.curpoint += 1
            self.write_pipe('\r'+self.lastline+self.writeline)
            offset = str(len(self.lastline)+self.curpoint+1)
            self.write_pipe("\x1b\x5b{}\x47".format(offset))

	elif cmd in self.keyboardMap:
            self.writelock = 1
            self.keyboardMap[cmd]()

        else:
            DebugOutput('drop: '+cmd.encode('hex'))

    def read(self, size):
        if not self.isalive():
            raise Exception
        line = self.read_pipe(size)
        if not self.writelock:
            self.lastline = line.split('\n')[-1]
            # print "\nLAST:"+self.lastline+'\n'
        return line

    def getwinsize(self):
        return (10001, 10001)

    def setwinsize(self, row, col):
        pass
