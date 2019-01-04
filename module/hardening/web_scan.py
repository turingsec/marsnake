import os
import hashlib
import json
import re
import time
from utils.harden_mgr import Kharden
from utils import common
from core.logger import Klogger

webfiles = []
percent = 0.0

def add_percent(delta, finished = False):
	global percent

	percent += delta

	if not finished:
		percent = percent if percent < 0.99 else 0.99
	else:
		percent = 1.0

	return percent

def get_percent():
	global percent
	return percent

def detect_cms(socket, session_id, existports, response):
	rules = {}

	with open(os.path.join(common.get_work_dir(), "config/cms_rules.lst"), "r") as f:
		rules = json.load(f)

	for existport in existports:
		Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [get_percent()], ["Detecting fingerprint of {}".format(str(existport))])

		for cms in rules:
			for rule in rules[cms]:
				
				try:
					if common.is_python2x():
						import httplib
						conn = httplib.HTTPConnection("127.0.0.1", existport, timeout = 1)
					else:
						from http.client import HTTPConnection
						conn = HTTPConnection("127.0.0.1", existport, timeout = 1)

					if conn:
						conn.request("GET", rule["url"])

						res = conn.getresponse()
						
						if res.status == 200:
							data = res.read()

							if "md5" in rule and hashlib.md5(data).hexdigest() == rule["md5"]:
								return cms

							elif "text" in rule:
								if type(rule["text"]) is list:
									for itext in rule["text"]:
										if itext in data:
											return cms

								elif rule["text"] in data:
									return cms

							elif "regexp" in rule:
								if type(rule["regexp"]) is list:
									for reg in rule["regexp"]:
										if re.search(reg, data):
											return cms

								elif re.search(rule["regexp"], data):
									return cms

						conn.close()

				except Exception as e:
					Klogger.error(str(e))

	return "Not CMS"
	
def parse_nginx_conf(ngconf_path):
	web_paths = []
	
	try:
		import nginxparser
	except Exception:
		pass
	else:
		if common.is_linux() and os.path.exists(ngconf_path):
			for root, dirs, files in os.walk(ngconf_path):
				for f in files:
					confs = nginxparser.load(open(os.path.join(root, f)))
					
					for conf in confs:
						for setting in conf[1]:
							if setting[0] == 'root':
								web_paths.append(setting[1])
							
	return web_paths
	
def parse_apache2_conf(apconf_path):
	web_paths = []
	
	if common.is_linux() and os.path.exists(apconf_path):
		for root, dirs, files in os.walk(apconf_path):
			for file in files:
				with open(os.path.join(root, file), "r") as f:
					data_all = f.read()

				#DocumentRoot "/var/www/html"
				match = re.search(r'DocumentRoot "(\S+)"', data_all)

				if match and len(match.groups()):
					web_paths.append(match.groups()[0])

	return web_paths

def read_conf(socket, session_id):
	global webfiles

	conf_func_dic = {"nginx" : parse_nginx_conf, "apache2" : parse_apache2_conf}
	confs_dic = {"nginx" : ["/etc/nginx/sites-enabled"], "apache2" : ["/etc/apache2/sites-enabled", "/etc/httpd"]}
	web_paths = []

	Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [0], ["Scanning Web files now"])

	for conf_type, conf_dirs in confs_dic.items():
		for conf_dir in conf_dirs:
			web_paths.extend(conf_func_dic[conf_type](conf_dir))

	if len(web_paths) > 0:
		web_paths = list(set(web_paths))

		for webpath in web_paths:
			for root, _, files in os.walk(webpath):
				for f in files:
					for extension in ['.html', '.htm', '.php', 'php3', 'phtm', 'phtml', '.jsp', '.asp', 'aspx']:
						if str.lower(os.path.splitext(f)[1]) == extension:
							webfiles.append(os.path.join(root, f))

	Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [add_percent(0.1)], ["Found {} Web files".format(len(webfiles))])

def webshell_scan(socket, session_id, response):
	global webfiles
	
	values = [["Location", "Keyword", "Last modification time"]]
	rulelist = [
		'(\$_(GET|POST|REQUEST)\[.{0,15}\]\s{0,10}\(\s{0,10}\$_(GET|POST|REQUEST)\[.{0,15}\]\))',
		'(base64_decode\([\'"][\w\+/=]{200,}[\'"]\))',
		'(eval(\s|\n)*\(base64_decode(\s|\n)*\((.|\n){1,200})',
		'((eval|assert)(\s|\n)*\((\s|\n)*\$_(POST|GET|REQUEST)\[.{0,15}\]\))',
		'(\$[\w_]{0,15}(\s|\n)*\((\s|\n)*\$_(POST|GET|REQUEST)\[.{0,15}\]\))',
		'(call_user_func\(.{0,15}\$_(GET|POST|REQUEST))',
		'(preg_replace(\s|\n)*\(.{1,100}[/@].{0,3}e.{1,6},.{0,10}\$_(GET|POST|REQUEST))',
		'(wscript\.shell)',
		'(cmd\.exe)',
		'(shell\.application)',
		'(documents\s+and\s+settings)',
		'(system32)',
		'(serv-u)',
		'(phpspy)',
		'(jspspy)',
		'(webshell)',
		'(Program\s+Files)'
	]
	
	Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [get_percent()], ["Scanning Webshell Now"])

	for filesname in webfiles:
		if os.path.getsize(filesname) < 5 * 1024 * 1024:
			with open(filesname, "r") as f:
				data = f.read()
				
			for rule in rulelist:
				tmp = re.compile(rule).findall(data)
				
				if tmp:
					values.append(["{}".format(filesname),
								"{}".format(' '.join(tmp[0])[0:50]),
								"{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(filesname))))])

	response["web"].append({
		"name" : "WebShell",
		"value" : len(values) - 1,
		"values" : values
	})
	
	Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [add_percent(0.2)], ["Scan Webshell Finished"])	
	
def darklink_scan(socket, session_id, response):
	global webfiles
	
	values = [["Location", "Keyword", "Last modification time"]]
	keywords = [
		u'seo',
		u'SEO'
	]
	
	Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [get_percent()], ["Scanning darklinks now"])
	
	try:
		from bs4 import BeautifulSoup
	except Exception:
		pass
	else:
		for filesname in webfiles:
			soup = BeautifulSoup(open(filesname), 'lxml')
			found_keyword = []
			
			for link in soup.find_all('a'):
				if link.string:
					for keyword in keywords:
						if keyword in link.string:
							found_keyword.append(keyword)
							
			if len(found_keyword) > 0:
				values.append(["{}".format(filesname),
							"{}".format('/'.join(found_keyword)),
							"{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(filesname))))])
							
	response["web"].append({
		"name" : "Dark Link",
		"value" : len(values) - 1,
		"values" : values
	})
	
	Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [add_percent(0.2)], ["Scanning darklinks end"])
	
def run(payload, socket):
	global webfiles

	session_id = payload["args"]["session_id"]
	response = {
		"error" : "",		
		"cmd_id" : payload['cmd_id'],
		"session_id" : payload["args"]["session_id"],
		"web" : []
	}

	existports = common.get_listen_port([80, 8080])
	webfiles = []
	
	read_conf(socket, session_id)

	response["web"].append({
		"name" : "Fingerprint",
		"value" : detect_cms(socket, session_id, existports, response)
	})

	Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [add_percent(0.2)], ["Detect fingerprint finished"])

	webshell_scan(socket, session_id, response)			
	darklink_scan(socket, session_id, response)

	Kharden().sync_process(socket, session_id, Kharden().WEBSCAN, 0, [1.0], ["Finished"])

	socket.response(response)
