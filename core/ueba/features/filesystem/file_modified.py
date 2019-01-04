from utils import file_op, common
from core.ueba.events import KUEBA_event
from core.cybertek import KCybertek
from core.ueba.features.filesystem import filesystem_feature
import core.ueba.macro
import re, os

class file_modified(filesystem_feature):
	def __init__(self):
		pass

	def on_file_modified_captured(self, pathname):
		if os.path.exists(pathname) and common.is_linux():
			import magic
			with magic.Magic() as m:
				kind = m.id_filename(pathname)

				if kind:
					pattern = re.compile(r"^(ELF|PE)\S+")
					m = pattern.search(kind)

					if m is None:
						return
				else:
					return

			result = KCybertek().detect_file_sha256(pathname)

			if result:
				KUEBA_event().on_malware_detect(pathname, result)
