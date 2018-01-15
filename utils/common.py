import sys, socket, os, platform, time, locale, shutil, re, stat, psutil
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

def mode_to_letter(mode):
    if stat.S_ISDIR(mode):
        return 'DIR'
    elif stat.S_ISBLK(mode):
        return 'BLK'
    elif stat.S_ISCHR(mode):
        return 'CHR'
    elif stat.S_ISFIFO(mode):
        return 'FIFO'
    elif stat.S_ISSOCK(mode):
        return 'SOCK'
    elif stat.S_ISLNK(mode):
        return 'LNK'
    else:
        return ''

def identifytype(path):
    mine = "Dir"

    if os.path.isfile(path):
        try:
            import magic
            mine = magic.from_file(path, mime = True)
            mine = mine if mine else "Unknown"
        except Exception as e:
            mine = "File"
        
    return mine

def try_unicode(path):
    if type(path) != unicode:
        try:
            return path.decode(os_encoding)
        except UnicodeDecodeError:
            pass

    return path

def path_translate(path):
    path = try_unicode(path)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    
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
    
def check_abspath_writable(path):
    if not os.access(path, os.W_OK):
        return False
        
    return True
    
def check_abspath_readable(path, recursive = False):
    if recursive and os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for item in dirs:
                item = os.path.join(root, item)
                
                if not os.access(item, os.R_OK):
                    return False, item
                    
            for item in files:
                item = os.path.join(root, item)
                
                if not os.access(item, os.R_OK):
                    return False, item
                    
        return True, ""
        
    if not os.access(path, os.R_OK):
        return False, path
        
    return True, ""
    
def check_file_exists(path):
    for i in path:
        if os.path.exists(i):
            return True
            
    return False

def get_directory_size(start_path = '.'):
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    return total_size

def grep(line, pattern):
    sub = re.findall(pattern, line)
    
    if len(sub) != 0:
        return sub[0], len(sub)
    else:
        return "", 0
        
def cat(path):
    data = ""
    
    try:
        if os.path.exists(path):
            with open(path, "rb") as fin:
                data = fin.read()
    except Exception as e:
        pass
        
    return data
    
def rm(path):
	try:
		if os.path.isdir(path):
			shutil.rmtree(path)
		else:
			os.remove(path)

		return ""
	except Exception as e:
		return to_ts(str(e))

def enum_file_path(path, result):
	if os.path.isdir(path):
		
		try:
			files = os.listdir(path)
			result.append(path)
		except Exception as e:
			files = []
			
		for file in files:
			abspath = os.sep.join([path, file])

			if os.path.isdir(abspath):
				enum_file_path(abspath, result)
			else:
				result.append(abspath)
	else:
		result.append(path)

def is_program_running(program):
    for proc in psutil.process_iter():
        try:
            if proc.name() == program:
                return True
        except Exception as e:
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
