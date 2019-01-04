from utils.singleton import singleton
#from . import tcp_traffic, udp_traffic, fs_change, usb_detect, period
from . import fs_change, usb_detect, period
from core.logger import Klogger
from core.ueba.features.net.ftp import ftp_traffic
from core.ueba.features.net.http import http_traffic
from core.ueba.features.net.ssh import ssh_traffic
from core.ueba.features.net.remote_ip import remote_ip
from core.ueba.features.identity.ssh_logon import ssh_logon
from core.ueba.features.identity.backdoor import backdoor
from core.ueba.features.filesystem.file_created import file_created
from core.ueba.features.filesystem.file_modified import file_modified
from core.ueba.features.filesystem.usb_monitor import usb_monitor
from core.threads import Kthreads

def run_collector(collector_do, name):
    try:
        Kthreads().set_name("UEBA-{}".format(name))
        collector_do()
    except Exception as e:
        Klogger().exception()

@singleton
class KUEBA_collector():
    features = [ftp_traffic(), ssh_traffic(), http_traffic(), remote_ip(),
                ssh_logon(), backdoor(),
                file_created(), file_modified(), usb_monitor()]

    def __init__(self):
        self.collectors = [#tcp_traffic.tcp_traffic(self.pe_captured, self.elf_captured, self.http_captured),
                #udp_traffic.udp_traffic(self.dns_captured),
                #fs_change.fs_change(self.file_created_captured, self.file_modified_captured),
                #usb_detect.usb_detect(self.usb_plugged, self.usb_unplugged),
                period.period(self.ssh_login_failed, self.ssh_login_success,
							self.remote_ip_detect,
							self.backdoor_detect)]

    def start(self):
        for c in self.collectors:
            if c.init():
                Kthreads().apply_async(run_collector, (c.do, c.name))
            else:
                Klogger().error("UEBA - {} init failed".format(c.name))

    @classmethod
    def pe_captured(cls, pe):
        Klogger().info("UEBA - PE captured")
        for feature in cls.features:
            feature.on_pe_captured(pe)

    @classmethod
    def elf_captured(cls, elf):
        Klogger().info("UEBA - ELF captured")
        for feature in cls.features:
            feature.on_elf_captured(elf)

    @classmethod
    def http_captured(cls, http):
        Klogger().info("UEBA - HTTP captured")
        for feature in cls.features:
            feature.on_http_captured(http)

    @classmethod
    def dns_captured(cls, dns):
        Klogger().info("UEBA - DNS captured")
        for feature in cls.features:
            feature.on_dns_captured(dns)

    @classmethod
    def file_created_captured(cls, pathname):
        Klogger().info("UEBA - File created captured {}".format(pathname))
        for feature in cls.features:
            feature.on_file_created_captured(pathname)

    @classmethod
    def file_modified_captured(cls, pathname):
        Klogger().info("UEBA - file modified captured {}".format(pathname))
        for feature in cls.features:
            feature.on_file_modified_captured(pathname)

    @classmethod
    def usb_plugged(cls, info):
        Klogger().info("UEBA - USB plugged captured")
        for feature in cls.features:
            feature.on_usb_plugged(info)

    @classmethod
    def usb_unplugged(cls, info):
        Klogger().info("UEBA - USB unplugged captured")
        for feature in cls.features:
            feature.on_usb_unplugged(info)

    @classmethod
    def ssh_login_failed(cls, account, ip, ts):
        Klogger().info("UEBA - SSH login failed captured")
        for feature in cls.features:
            feature.ssh_login_failed(account, ip, ts)

    @classmethod
    def ssh_login_success(cls, account, ip, ts):
        Klogger().info("UEBA - SSH login success captured")
        for feature in cls.features:
            feature.ssh_login_success(account, ip, ts)

    @classmethod
    def remote_ip_detect(cls, pid, ip):
        #Klogger().info("UEBA - ip captured")
        for feature in cls.features:
            feature.remote_ip_detect(pid, ip)

    @classmethod
    def backdoor_detect(cls, pid, ppid):
        for feature in cls.features:
            feature.backdoor_detect(pid, ppid)
