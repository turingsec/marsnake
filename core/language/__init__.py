from utils.singleton import singleton
from config import constant
from core.event.base_event import base_event
from utils import common, file_op
import os, json, re

@singleton
class Klanguage(base_event):
	def __init__(self):
		self.lang = "zh-CN"
		self.jsons = os.path.join(common.get_work_dir(), constant.LANGUAGE_CONF)
		self.conf = {}

	def on_initializing(self, *args, **kwargs):
		for pathname in self.list_jsons():
			if common.is_python2x():
				with open(pathname, "r") as f:
					self.conf[os.path.splitext(os.path.basename(pathname))[0]] = json.load(f)
			else:
				with open(pathname, "r", encoding = "utf-8") as f:
					self.conf[os.path.splitext(os.path.basename(pathname))[0]] = json.load(f)

		if self.lang in self.conf:
			return True

		return False

	def list_jsons(self):
		for pathname in file_op.listdir(self.jsons):
			if not pathname.lower().endswith('.json'):
				continue

			yield pathname

	def to_ts(self, code):
		return self.conf[self.lang][str(code)]

	def encode_ts(self, code, *args):
		data = ["#{}#".format(code)]

		for i in args:
			data.append(str(i))

		return '@@'.join(data)

	def decode_ts(self, data):
		pattern = re.compile(r'^#(\d+)#')
		match = pattern.match(data)

		if match:
			code = match.groups()[0]

			if len(data) != match.end():
				data = self.to_ts(code).format(*(data[match.end():].split("@@")[1:]))
			else:
				data = self.to_ts(code)

		return data

	def get_lang(self):
		return self.lang

	def set_lang(self, lang):
		if lang in ["en-US", "zh-CN"]:
			self.lang = lang
