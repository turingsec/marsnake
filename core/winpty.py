import threading
from subprocess import Popen, STDOUT, CREATE_NEW_CONSOLE, STARTUPINFO, STARTF_USESHOWWINDOW, SW_HIDE, CREATE_NEW_PROCESS_GROUP
import os
from time import sleep
import win32process
import win32con
import win32gui
import win32api
import psutil


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
        self.proc = None
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
                if p.ppid() == self.proc.pid:
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
            os.write(self.pipein, "\x1b\x5b{}\x47".format(
                offset))  # relocate point
            self.curpoint -= 1

    def keyRight(self):
        if self.curpoint == len(self.writeline):
            pass
        else:
            offset = str(len(self.lastline)+self.curpoint+1+1)
            os.write(self.pipein, "\x1b\x5b{}\x47".format(
                offset))  # relocate point
            self.curpoint += 1

    def keyBacksapce(self):
        if self.curpoint:
            self.clearLine()
            self.writeline = self.writeline[
                :self.curpoint-1]+self.writeline[self.curpoint:]
            os.write(self.pipein, '\r'+self.lastline+self.writeline)
            self.curpoint -= 1
            offset = str(len(self.lastline)+1+self.curpoint)
            os.write(self.pipein, "\x1b\x5b{}\x47".format(
                offset))  # relocate point

    def keyHome(self):
        if self.curpoint:
            offset = str(len(self.lastline)+1)
            os.write(self.pipein, "\x1b\x5b{}\x47".format(
                offset))  # relocate point
            self.curpoint = 0

    def keyDelete(self):
        if self.curpoint == len(self.writeline):
            pass
        else:
            self.clearLine()
            self.writeline = '{}{}'.format(self.writeline[:self.curpoint],
                                           self.writeline[self.curpoint+1:])
            os.write(self.pipein, '\r'+self.lastline+self.writeline)
            offset = str(len(self.lastline)+self.curpoint+1)
            os.write(self.pipein, "\x1b\x5b{}\x47".format(
                offset))  # relocate point

    def keyInset(self):
        if self.insertflag:
            self.insertflag = 0
        else:
            self.insertflag = 1

    def keyEnd(self):
        offset = len(self.writeline)+len(self.lastline)+1
        os.write(self.pipein, "\x1b\x5b{}\x47".format(offset))
        self.curpoint = len(self.writeline)

    def keyUP(self):
        content = self.PopWriteBufferContent(up=True)
        if not content == None:
            self.clearLine()
            self.writeline = content
            os.write(self.pipein, '\r'+self.lastline+self.writeline)
            self.keyEnd()

    def keyDown(self):
        content = self.PopWriteBufferContent(up=False)
        if not content == None:
            self.clearLine()
            self.writeline = content
            os.write(self.pipein, '\r'+self.lastline+self.writeline)
            self.keyEnd()

    def clearLine(self):
        # overflow old output with blank
        length = len(self.writeline)+len(self.lastline)+1
        os.write(self.pipein, '\r{}'.format(' '*length))

    def InsertWriteBuffer(self):
        if len(self.writeline):
            if len(self.writeBuffer) < self.writeBufferMaxLen:
                self.writeBuffer.insert(0, self.writeline)
            else:
                self.writeBuffer.pop()
                self.writeBuffer.insert(0, self.writeline)
            self.writeBufferIndex = self.writeBufferIndexDefault

    def PopWriteBufferContent(self, up=True):
        print self.writeBuffer
        length = len(self.writeBuffer)
        content = None
        if 0 == length:
            return None
        if up:
            if self.isInsertCurrentUnfinishedLine == 0:
                self.tempUnfinishedLine = self.writeline
                self.isInsertCurrentUnfinishedLine = 1
                print "is inserted"

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
        hwnd = self.Console_hwnd[0]
        code = ord(char)

        win32api.SendMessage(hwnd, win32con.WM_CHAR, code, 0)

    def sendkeypress(self, key):
        hwnd = self.Console_hwnd[0]

        # win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, key, 0)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, key, 0)

    def start(self, cmd):
        si = STARTUPINFO()
        si.dwFlags |= STARTF_USESHOWWINDOW
        si.wShowWindow = SW_HIDE
        r, w = os.pipe()
        self.pipeout = r
        self.pipein = w

        self.proc = Popen(cmd, stdout=w, stderr=w,
                          creationflags=CREATE_NEW_CONSOLE, startupinfo=si)
        sleep(0.5)
        print '[*] pid: ', hex(self.proc.pid)

        self.Console_hwnd = get_hwnds_for_pid(self.proc.pid)
        print '[*] hwnd:', self.Console_hwnd[0]

    @classmethod
    def spawn(self, argv, env=None, cwd=None):
        myself = self()
        myself.start(argv[0])

        return myself

    def kill(self, sig):
        Popen("taskkill /F /T /PID %i" % self.proc.pid, shell=True)

    def close(self):
        pass

    def isalive(self):
        r = self.proc.poll()

        if r == None:
            return True

        return False

    def write(self, cmd):
        i = cmd[0]
        if i == '\x0d':
            self.InsertWriteBuffer()
            for char in self.writeline:
                self.sendkey(char)

            os.write(self.pipein, '\x0d\x0a')
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
            os.write(self.pipein, '\r'+self.lastline+self.writeline)
            offset = str(len(self.lastline)+self.curpoint+1)
            os.write(self.pipein, "\x1b\x5b{}\x47".format(offset))

        elif self.keyboardMap.has_key(cmd):
            self.writelock = 1
            self.keyboardMap[cmd]()

        else:
            print 'drop: '+cmd.encode('hex')

    def read(self, size):
        if not self.isalive():
            raise Exception
        line = os.read(self.pipeout, size)
        if not self.writelock:
            self.lastline = line.split('\n')[-1]
            # print "\nLAST:"+self.lastline+'\n'
        return line

    def getwinsize(self):
        return (10001, 10001)

    def setwinsize(self, row, col):
        pass
