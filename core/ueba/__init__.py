# -- coding: utf-8 --
from utils.singleton import singleton
from utils import file_op, common
from utils.randomize import Krandom
from core.logger import Klogger
from core.configuration import Kconfig
from core.ueba.collector import KUEBA_collector
from core.event.base_event import base_event

@singleton
class KUEBA(base_event):
    def __init__(self):
        #collector -> features (AI models)-> events -> classifier -> timeline
        #SSH扫描 -> SSH登录 -> 异常Bash		**
        #插U盘 -> 检测到恶意软件			**
        #恶意软件执行 -> 检测到注入			*
        #恶意软件执行 -> 访问恶意URL(Malware, Phishing, Malicious)
        self.models = {}

    def on_initializing(self, *args, **kwargs):
        return True

    def on_start(self, *args, **kwargs):
        KUEBA_collector().start()

    def download(self):
        status, data = net_op.create_http_request(Kconfig().cybertek_server, 
            "POST",
            "/download",
            urllib.urlencode({'@sha256': sha256}))

        return data
