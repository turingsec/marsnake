# -*- coding: utf-8 -*-
import os
import stat
import subprocess
import time
import re
import socket
import psutil
import struct
from datetime import datetime
from utils import common

def get_boot_time():
    if check_programs_installed("systemd-analyze"):
        data, success, retcode = exec_command(['systemd-analyze', 'time'])
        
        if success:
            pattern = re.compile(r"^Startup finished in (.+s) \(kernel\) \+ (.+s) \(initrd\) \+ (.+s) \(userspace\) \= (.+s)")
            match = pattern.match(data)
            
            if match:
                groups = match.groups()
                
                if len(groups) == 4:
                    return groups
                
            pattern = re.compile(r"^Startup finished in (.+s) \(kernel\) \+ (.+s) \(userspace\) \= (.+s)")
            match = pattern.match(data)
            
            if match:
                groups = match.groups()
                
                if len(groups) == 3:
                    return groups

    return None

# @kind : 0 for systemd, 1 for upstart, 2 for SysV
def get_description_by_name(service, kind):
    if kind == 0:
        systemd_path = ["/lib/systemd/system/", "/etc/systemd/system"]
        pattern = re.compile(r"^Description=(.+)")

        for path in systemd_path:
            unit_path = os.path.join(path, service)

            if os.path.exists(unit_path):
                data = common.cat(unit_path)

                if data:
                    lines = data.split("\n")
                    
                    for line in lines:
                        if line:
                            match = pattern.match(line)

                            if match and len(match.groups()):
                                return match.groups()[0]

    if kind == 2:
        des_pattern = re.compile(r"# Description:\s+(.+)")
        short_pattern = re.compile(r"# Short-Description:\s+(.+)")
        initscript_path = os.path.join("/etc/init.d", service)

        if os.path.exists(initscript_path):
                data = common.cat(initscript_path)

                if data:
                    lines = data.split("\n")
                    
                    for line in lines:
                        if line:
                            match = short_pattern.match(line)

                            if match and len(match.groups()):
                                return match.groups()[0]

                            match = des_pattern.match(line)

                            if match and len(match.groups()):
                                return match.groups()[0]

    return ""

def check_programs_installed(program):
    paths = os.environ["PATH"].split(":")

    for path in paths:
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

def get_ip_gateway():
    route = "/proc/net/route"
    ipv4 = ""
    ipv6 = ""
    gateway = ""
    nic = ""
    RTF_GATEWAY = 0x2

    if os.path.exists(route):
        with open(route, "r") as f:
            
            for line in f.readlines():
                route_line = line.split()

                flags = route_line[3]

                if flags.isdigit():
                    flags = int(flags)

                    if flags & RTF_GATEWAY:
                        nic = route_line[0]

                        gateway = route_line[2]
                        gateway = int(gateway, 16)
                        gateway = socket.inet_ntoa(struct.pack("<I", gateway))

    if nic != "":
        interfaces = psutil.net_if_addrs()

        for name, addrs in interfaces.items():
            if name == nic:
                for addr in addrs:
                    if addr[0] == 2:
                        ipv4 = addr[1]

                    if addr[0] == 10:
                        ipv6 = addr[1]

    return nic, ipv4, ipv6, gateway
    
def find_useradd_users():
    uid_min = 1000
    uid_max = 60000

    data = common.cat("/etc/login.defs")

    if data:
        lines = data.split("\n")
                
        for line in lines:
            if line:
                tmp, num = common.grep(line, r"^UID_MIN\s*(\d+)")
                if num:            
                    uid_min = tmp
                    continue

                tmp, num = common.grep(line, r"^UID_MAX\s*(\d+)")
                if num:
                    uid_max = tmp
                    continue

    data = common.cat("/etc/passwd")
    usernames = []

    if data:
        lines = data.split("\n")

        for line in lines:
            if line:
                username, password, uid, gid, comment, home, shell = line.split(":")

                if uid_min != None and uid_max != None:
                    if int(uid) >= int(uid_min) and int(uid) <= int(uid_max):
                        usernames.append(username)

    return usernames

def exec_command(cmd):
    cmdstr = ' '.join(cmd)
    process = subprocess.Popen(cmdstr, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return str(stdout).strip(), True, process.returncode
    else:
        return str(stdout).strip(), False, process.returncode
        #raise Exception("stderr: %s" % str(stderr))

def timestamp2count(tickcount):
    s = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tickcount))
    new_s = "%04d-%02d-%02d %02d:%02d:%02d" % (int(s[:4]) - 1970, 
                                            int(s[5:7]) - 1, int(s[8:10]) - 1,
                                            int(s[11:13]) - 8, int(s[14:16]), int(s[17:]))
    return new_s

def time_duration(start_timestamp, end_timestamp):
    start = datetime.fromtimestamp(start_timestamp)
    end = datetime.fromtimestamp(end_timestamp)

    return end - start
    
def td_format(td_object):
    seconds = int(td_object.total_seconds())
    periods = [
                ('year',    60 * 60 * 24 * 365),
                ('month',   60 * 60 * 24 * 30),
                ('day',     60 * 60 * 24),
                ('hour',    60 * 60),
                ('minute',  60),
                ('second',  1)
            ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value , seconds = divmod(seconds, period_seconds)
            
            if period_value == 1:
                strings.append("%s %s" % (period_value, period_name))
            else:
                strings.append("%s %ss" % (period_value, period_name))

    return ", ".join(strings)

def special_to_letter(mode):
    l = ''
    
    ALL_R = (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    ALL_W = (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)

    if mode & stat.S_ISGID:
        l += 'G'
    if mode & stat.S_ISUID:
        l += 'U'
    if mode & stat.S_ISVTX:
        l += 'T'
    if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        l += 'E'
    if ( mode & ALL_R ) == ALL_R:
        l += 'R'
    if ( mode & ALL_W ) == ALL_W:
        l += 'W'

    return l

def permissions_to_unix_name(mode):
    is_dir = 'd' if stat.S_ISDIR(mode) else '-'
    dic = {'7':'rwx', '6' :'rw-', '5' : 'r-x', '4':'r--', '3':'-wx', '2':'-w-', '1':'--x', '0': '---'}
    perm = str(oct(mode)[-3 : ])
    
    return is_dir + ''.join(dic.get(x, x) for x in perm)

#/etc/os-release -> ../usr/lib/os-release
#/usr/lib/os-release -> ./os.release.d/os-release-workstation
def readlink(path, depth):
    result = ""
    
    while True:
        if not os.path.exists(path):
            path = ""
            break
            
        _stat = os.lstat(path)
            
        if stat.S_ISLNK(_stat.st_mode):
            result = os.readlink(path)
        else:
            break
            
        if not os.path.isabs(result):
            path = os.path.join(os.path.dirname(path), result)  #/etc/../usr/lib/os-release
        else:
            path = result
        
        depth -= 1

        if depth == 0:
            break

    return path

def check_world_writable(path):
    try:
        _stat = os.stat(path)
        
        if _stat.st_mode & stat.S_IWOTH:
            return True
            
    except Exception as e:
        pass

    return False

def check_access_writable(path):
    return os.access(path, os.W_OK)

#https://unix.stackexchange.com/questions/139764/what-are-the-world-writable-directories-by-default
def find_writable_dir():
    writable_path = ["/tmp", "/var/tmp", "/dev/shm"]
    path = ""

    for tmp in writable_path:
        if check_access_writable(tmp):
            path = tmp
            break

    return path

def detect_debian_like_os():
     #debian
    data, success, retcode = exec_command(['ls', '/etc/debian_version'])
    if success:
        return True

    return False

def detect_distribution():

    distro = ""
    distro_release = ""

    #os-release
    #https://www.freedesktop.org/software/systemd/man/os-release.html
    #NAME="Ubuntu"
    #VERSION="16.04.2 LTS (Xenial Xerus)"
    items = {"NAME" : None, "VERSION" : None}
    data = common.cat('/etc/os-release')

    if data:
        lines = data.split("\n")

        for line in lines:
            if line:
                k, v = line.split("=")

                if items.has_key(k):
                    items[k] = v.lstrip('"').rstrip('"')

        distro = items["NAME"]
        distro_release = items["VERSION"]

        if distro and distro_release:
            return distro, distro_release

    #fedora, oracle, centos, amazon
    #https://www.rackaid.com/blog/how-to-determine-centos-or-red-hat-version/
    #Fedora release 26 (Twenty Six)
    #CentOS Linux release 7.3.1611 (Core)
    #Amazon Linux AMI release 2017.03
    identification = ["/etc/fedora-release", "/etc/oracle-release", "/etc/redhat-release", "/etc/system-release"]

    for i in identification:
        if os.path.exists(i):
            data = common.cat(i)

            if data:
                pattern = re.compile(r'(.*) release (\d[\d.]*)')
                match = pattern.match(data)

                if len(match.groups()) == 2:
                    distro = match.groups()[0]
                    distro_release = match.groups()[1]
                    
                    if distro and distro_release:
                        return distro, distro_release
        
    data = common.cat('/etc/issue')
    
    #raspbian
    if success:
        result = data.split()
        
        if len(result) > 2 and result[0] == "Raspbian":
            distro = "raspbian"
            return True
            
    data, success, retcode = exec_command(['lsb_release', '-ir'])
    
    #Distributor ID: Ubuntu
    #Release:        16.04
    if success:
        pattern = re.compile(r'(?s)^Distributor ID:\s*(.+?)\n*Release:\s*(.+?)$')
        match = pattern.match(data)
        
        if len(match.groups()) == 2:
            distro = match.groups()[0]
            distro_release = match.groups()[1]

            if distro and distro_release:
                return distro, distro_release
            
    data = common.cat('/etc/lsb-release')
    
    #DISTRIB_ID=Ubuntu
    #DISTRIB_RELEASE=16.04
    #DISTRIB_CODENAME=xenial
    #DISTRIB_DESCRIPTION="Ubuntu 16.04.2 LTS"
    if success:
        pattern = re.compile(r'(?s)^DISTRIB_ID=(.+?)\n*DISTRIB_RELEASE=(.+?)\n.*$')
        match = pattern.match(data)

        if len(match.groups()) == 2:
            distro = match.groups()[0]
            distro_release = match.groups()[1]
            
            if distro and distro_release:
                return distro, distro_release

    distro = platform.linux_distribution()[0]
    distro_release = platform.linux_distribution()[1]

    return distro, distro_release

