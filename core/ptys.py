import os, time, signal, json
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from utils.singleton import singleton
from core.logger import Klogger
from core.event import event
from utils import common

try:
    from ptyprocess import PtyProcessUnicode
except ImportError:
    from winpty import PtyProcess as PtyProcessUnicode
    
ENV_PREFIX = "PYXTERM_"         # Environment variable prefix
DEFAULT_TERM_TYPE = "xterm"

#Once web opened, data will sent
def terminal_reading(term, socket, session_id):
    try:
        while(True):
            data = term.proc.read(65536)
            data = common.decode2utf8(data)
            
            socket.response({
                "cmd_id" : "1034",
                "session_id" : session_id,
                "data" : data,
                "error" : ""
            });
            
            time.sleep(0.01)
    except Exception as e:
        Klogger().error("read from pty error:{}".format(e))
        term.on_eof()

        socket.response({
            "cmd_id" : "1036",
            "session_id" : session_id,
            "data" : "Terminal closed",
            "error" : ""
        })
        
@singleton
class Kptys(event):
    
    def __init__(self):
        self.pty = None
        self.executor = ThreadPoolExecutor(max_workers = 1)
        
        event.__init__(self)

    def on_initializing(self):
        pass
        
    def on_disconnected(self):
        """Override this to e.g. kill terminals on client disconnection.
        """
        Klogger().debug("on_disconnected trigger!!")
        #self.terminate()
        
    def new_terminal(self, session_id, socket):
        
        command = "cmd"
        
        if common.is_linux():
            command = "bash"
            
        if self.pty:
            self.terminate();
            Klogger().info("Terminate old terminal for session {}".format(session_id))

        term = terminal(shell_command=[command]).new_one()

        self.pty = {
            "terminal" : term,
            "future" : self.executor.submit(terminal_reading, term, socket, session_id)
        }
        
        Klogger().info("Create new terminal for session {}".format(session_id))
        
    def write(self, data):
        if self.pty:
            self.pty["terminal"].write(data)
            
    def resize(self, rows, cols, innerHeight, innerWidth):
        if self.pty:
            self.pty["terminal"].resize(rows, cols)
            
    def terminate(self):
        if self.pty:
            term = self.pty["terminal"]
            future = self.pty["future"]
            
            self.pty = None
            
            term.terminate()
            time.sleep(1)

            if not future.done():
                future.cancel()

class terminal(object):
    """Base class for a terminal"""
    def __init__(self, shell_command):
        self.proc = None
        self.shell_command = shell_command

        # Store the last few things read, so when a new client connects,
        # it can show e.g. the most recent prompt, rather than absolutely
        # nothing.
        self.read_buffer = deque([], maxlen=10)

    def new_one(self, **kwargs):
        """Make a new terminal, return a :class:`PtyWithClients` instance."""
        
        options = {}
        options['shell_command'] = self.shell_command
        options.update(kwargs)
        argv = options['shell_command']
        env = self.make_term_env(**options)
        
        self.proc = PtyProcessUnicode.spawn(argv, env = env, cwd = options.get('cwd', None))
        
        return self
        
    def make_term_env(self, height=25, width=80, winheight=0, winwidth=0, **kwargs):
        """Build the environment variables for the process in the terminal."""
        env = os.environ.copy()
        env["TERM"] = DEFAULT_TERM_TYPE
        dimensions = "%dx%d" % (width, height)
        
        if winwidth and winheight:
            dimensions += ";%dx%d" % (winwidth, winheight)
            
        env[ENV_PREFIX+"DIMENSIONS"] = dimensions
        env["COLUMNS"] = str(width)
        env["LINES"] = str(height)
        
        '''
        if self.server_url:
            env[ENV_PREFIX+"URL"] = self.server_url
        '''
        return env
        
    def write(self, data):
        self.proc.write(data)
        
    def resize(self, rows, cols):
        """Set the terminal size to that of the smallest client dimensions.
        
        A terminal not using the full space available is much nicer than a
        terminal trying to use more than the available space, so we keep it 
        sized to the smallest client.
        """
        minrows = mincols = 10001

        if rows is not None and rows < minrows:
            minrows = rows
        if cols is not None and cols < mincols:
            mincols = cols

        if minrows == 10001 or mincols == 10001:
            return
            
        rows, cols = self.proc.getwinsize()

        if (rows, cols) != (minrows, mincols):
            self.proc.setwinsize(minrows, mincols)

    def on_eof(self):
        """Called when the pty has closed."""
        # Stop trying to read from that terminal
        try:
            if self.proc.isalive():
                Klogger().debug("pty eof still alived")
                self.proc.close()
            else:
                Klogger().info("pty eof closed")

        except Exception as e:
            Klogger().error(e)

    def terminate(self, force = True):
        """Send a signal to the process in the pty"""
        if self.proc.isalive():

            if os.name == 'nt':
                signals = [signal.SIGINT, signal.SIGTERM]
            else:
                signals = [signal.SIGHUP, signal.SIGCONT, signal.SIGINT,
                           signal.SIGTERM]

            try:      
                for sig in signals:
                    self.proc.kill(sig)

                    if not self.proc.isalive():
                        return True

                if force:
                    self.proc.kill(signal.SIGKILL)
                    
                    if not self.proc.isalive():
                        return True

                return False

            except Exception as e:
                if self.proc.isalive():
                    return False

        return True

    def killpg(self, sig = signal.SIGTERM):
        """Send a signal to the process group of the process in the pty"""
        if os.name == 'nt':
            return self.proc.kill(sig)
            
        pgid = os.getpgid(self.proc.pid)
        os.killpg(pgid, sig)