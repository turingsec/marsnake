import sys, socket, os, platform, time, locale, shutil, re, stat, psutil, glob, subprocess
from datetime import datetime

system = sys.platform
os_encoding = locale.getpreferredencoding() or "utf8"
work_dir = ""

def check_obj_is_string(s):
    if is_python2x():
        return isinstance(s, basestring)
    else:
        return isinstance(s, str)
        
def decode2utf8(data):
    return data.decode(os_encoding)

def print_obj(obj):
    print '\n'.join(['%s:%s' % item for item in obj.__dict__.items()])

def add_module_path(path):
    sys.path.append(os.path.join(get_work_dir(), path))
    
def print2hex(s):
    print(":".join("{:02x}".format(ord(c)) for c in s))

def is_python2x():
    return sys.version_info  < (3, 0)
    
def setdefaultencoding(coding):
    if sys.version_info  < (3, 0):
        reload(sys)
        sys.setdefaultencoding(coding)

def python_version(version):
    return sys.version_info.major == version

def measuring_latency(ip):
    return "60ms"

def to_ts(value):
    return "#{}#".format(value)

def set_work_dir():
    global work_dir
    work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
def get_work_dir():
    global work_dir
    return work_dir

def is_linux():
	global system
	return system == "linux2"

def is_windows():
	global system
	return system == "win32"
    
def is_darwin():
	global system
	return system == "darwin"
    
def extend_at_front(array_src, maxi, cons):
    array_dst = array_src[-maxi : len(array_src)]
    diff = maxi - len(array_dst)
    
    if diff:
        tmp = [ cons for x in range(diff) ]
        tmp.extend(array_dst)
        array_dst = tmp
        
    return array_dst

def boolstr_to_bool(value):
    """Convert a string boolean to a Python boolean"""
    if 'true' == value.lower():
        return True
        
    if 'false' == value.lower():
        return False

    raise RuntimeError("Invalid boolean: '%s'" % value)

def do_get_ip_gateway():
    ip = '127.0.0.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(0)
    
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        pass
    finally:
        s.close()
        
    return ip
    
def get_ip_gateway():

	if is_windows():
		return do_get_ip_gateway()
	elif is_linux():
		from utils import lib
		return lib.get_ip_gateway()[1] or do_get_ip_gateway()
	elif is_darwin():
		return do_get_ip_gateway()
        
	return ""

def get_distribution():

	if is_windows():
		import _winreg

		reg_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion")
		info = _winreg.QueryValueEx(reg_key, "ProductName")[0]

		if info:
			return info
		else:
			return "Windows {}".format(platform.win32_ver()[0])

	elif is_linux():
		from utils import lib
		return "{} {}".format(*(lib.detect_distribution()))

	elif is_darwin():
		return "MacOS X {}".format(platform.mac_ver()[0])

	return ""

def grep(line, pattern):
    sub = re.findall(pattern, line)
    
    if len(sub) != 0:
        return sub[0], len(sub)
    else:
        return "", 0
        
def size_human_readable(num, suffix = 'B'):
    try:
        num = int(num)
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, 'Yi', suffix)
    except:
        return '0.00 B'

def try_unicode(path):
    if type(path) != unicode:
        try:
            return path.decode(os_encoding)
        except UnicodeDecodeError:
            pass

    return path

def timestamp2string(timestamp, dateandtime = False):
	global os_encoding

	try:
		d = datetime.fromtimestamp(timestamp)
		#return str(d.strftime("%y/%m/%d %H:%M:%S"))

		if dateandtime:
			return "{} {}".format(d.strftime("%c"), time.strftime('%Z', time.localtime()).decode(os_encoding))
		else:
			return str(d.strftime("%Y-%m-%d %H:%M:%S"))
	except Exception as e:
		return '00/00/00'
        
def localtime2string():
    return "{}{}{}{}{}{}".format(*(time.localtime()[0:6]))

def is_program_running(program):
    program = program.lower()

    if is_linux():
        """Check whether program is running"""
        for filename in glob.iglob("/proc/*/exe"):
            try:
                target = os.path.realpath(filename)
            except TypeError:
                # happens, for example, when link points to
                # '/etc/password\x00 (deleted)'
                continue
            except OSError:
                # 13 = permission denied
                continue

            if program == os.path.basename(target):
                return True

        return False
        
    elif is_darwin():
        def run_ps():
            subprocess.check_output(["ps", "aux", "-c"])

        try:
            processess = (re.split(r"\s+", p, 10)[10] for p in run_ps().split("\n") if p != "")
            next(processess)  # drop the header
            return program in processess
        except IndexError:
            pass

        return False

    else:
        for proc in psutil.process_iter():
            try:
                if proc.name().lower() == program:
                    return True
            except psutil.NoSuchProcess:
                pass

        return False

def get_listen_port(ports):
    conns = psutil.net_connections(kind = "inet")
    ret = []
    
    for conn in conns:
        fd, family, _type, laddr, raddr, status, pid = conn
        
        if status == "LISTEN":
            port = laddr[1]
            
            if port in ports:
                ret.append(port)
                
    return list(set(ret))

def is_kernel_thread(proc):
    if is_linux():
        """Return True if proc is a kernel thread, False instead."""
        try:
            return os.getpgid(proc.pid) == 0
        # Python >= 3.3 raises ProcessLookupError, which inherits OSError
        except OSError:
            # return False is process is dead
            return False
            
    return False

def get_last_min(t):
    if not t:
        t = time.time()
        
    a = int(t)
    b = a % 60
    
    return a - b

#5.2 M
def sizestring2int(sstr):
    pattern = re.compile(r"(\S+)\s(\w)")
    match = pattern.match(sstr.strip())
    size = 0
    
    if match and len(match.groups()) == 2:
        size = float(match.groups()[0])
        unit = match.groups()[1].lower()
        
        if unit == 'm':
            size *= 1024 * 1024
        elif unit == 'k':
            size *= 1024
            
    return int(size)
    
# os.path.expandvars does not work well with non-ascii Windows paths.
# This is a unicode-compatible reimplementation of that function.
def expandvars(var):
    """Expand environment variables.

    Return the argument with environment variables expanded. Substrings of the
    form $name or ${name} or %name% are replaced by the value of environment
    variable name."""
    if isinstance(var, str):
        final = var.decode('utf-8')
    else:
        final = var

    if 'posix' == os.name:
        final = os.path.expandvars(final)
    elif 'nt' == os.name:
        import _winreg
        if final.startswith('${'):
            final = re.sub(r'\$\{(.*?)\}(?=$|\\)',
                           lambda x: '%%%s%%' % x.group(1),
                           final)
        elif final.startswith('$'):
            final = re.sub(r'\$(.*?)(?=$|\\)',
                           lambda x: '%%%s%%' % x.group(1),
                           final)
        final = _winreg.ExpandEnvironmentStrings(final)
    return final

def path_translate(path):
    path = try_unicode(path)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    
    return path

# Windows paths have to be unicode, but os.path.expanduser does not support it.
# This is a unicode-compatible reimplementation of that function.
def expanduser(path):
    """Expand the path with the home directory.
    
    Return the argument with an initial component of "~" replaced by
    that user's home directory.
    """
    if isinstance(path, str):
        final = path.decode('utf-8')
    else:
        final = path

    # If does not begin with tilde, do not alter.
    if len(path) == 0 or not '~' == path[0]:
        return final

    if 'posix' == os.name:
        final = os.path.expanduser(final)
    elif 'nt' == os.name:
        found = False
        for env in [u'%USERPROFILE%', u'%HOME%']:
            if env in os.environ:
                home = expandvars(env)
                found = True
                break
        if not found:
            h_drive = expandvars(u'%HOMEDRIVE%')
            h_path = expandvars(u'%HOMEPATH%')
            home = os.path.join(h_drive, h_path)
        final = final.replace('~user/', '')
        final = final.replace('~/', '')
        final = final.replace('~', '')
        final = os.path.join(home, final)
    return final

def check_programs_installed(program):
    delimiter = ':'

    if 'nt' == os.name:
        delimiter = ';'

    for path in os.environ["PATH"].split(delimiter):
        if os.path.exists(path):
            try:
                for x in os.listdir(path):
                    item = os.path.join(path, x)

                    if os.path.isfile(item):
                        if x == program:
                            return True
            except Exception as e:
                pass

    return False