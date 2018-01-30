from utils.singleton import singleton
from utils import lib, common
from core.logger import Klogger
from core.db import Kdatabase
import os, re

@singleton
class Kvuls():
	def __init__(self):
		self.reset()
		
	def reset(self):
		self.vuls = {}
		self.installed_packages = {}
		self.upgradable_packages = {}
		self.upgradable_packages_count = 0
		self.changelogtool = ""
		
	def get_upgradable_packages_num(self):
		return self.upgradable_packages_count
		
	def candidate_size(self, package_name, candidate):
		apt = common.check_programs_installed("apt-get")
		size = 0
		
		if apt:
			data, success, retcode = lib.exec_command(["apt-cache", "show", package_name])
			
			if success:
				lines = data.split("\n")
				pattern_size = re.compile(r'^Size: (\d+)')
				
				for line in lines:
					match = pattern_size.match(line)
					
					if match:
						size = int(match.groups()[0])
						break
						
		yum = common.check_programs_installed("yum")
		
		#Available Packages
		#Name        : systemd
		#Arch        : x86_64
		#Version     : 219
		#Release     : 42.el7_4.4
		#Size        : 5.2 M
		if yum:
			data, success, retcode = lib.exec_command(["yum", "info", "available", package_name])
			
			if success:
				lines = data.split("\n")
				pattern = re.compile(r"^Size\s*:\s(.+)")	#need to upgrade
				
				for line in lines:
					match = pattern.match(line)
					
					if match:
						size = common.sizestring2int(match.groups()[0])
						break
						
		return size
		
	def get_installed_package_version(self, package):
		if self.installed_packages.has_key(package):
			return self.installed_packages[package]
		else:
			return ""

	def redhat_get_installed_packages(self):
		#atmel-firmware	atmel-firmware-1.3-16.fc26.noarch
		#libqb			libqb-1.0.2-1.fc26.x86_64
		#gnutls			gnutls-3.5.14-1.fc26.x86_64
		data, success, retcode = lib.exec_command(["rpm", "-qa", "--queryformat", "'%{NAME}\t%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n\'"])

		if success:
			lines = data.split("\n")

			for line in lines:
				result = line.split()

				if len(result) == 2:
					self.installed_packages[result[0]] = result[1]
					Klogger().info("package : {} version : {}".format(result[0], result[1]))

	def redhat_centos_checkupdate(self):
		#wireless-tools.i686				1:29-6.el6				base
		#xorg-x11-drv-ati-firmware.noarch	7.6.1-2.el6				base
		#Obsoleting Packages
		#firefox.i686						52.3.0-3.el6.centos		updates                                 
		data, success, retcode = lib.exec_command(["yum", "--color=never", "check-update"])

		#Returns exit value of 100 if there are packages available for an update
		if success or retcode == 100:
			lines = data.split("\n")
			start_parse = False

			pattern_end_parse = re.compile(r'Obsoleting Packages')

			for line in lines:

				if not start_parse:
					if len(line.split()) == 0:
						start_parse = True
						continue
				else:
					if pattern_end_parse.match(line):
						break

					result = line.split()

					#xorg-x11-xauth.x86_64		1:1.0.9-1.el6		base 
					#Obsoleting Packages
					if len(result) == 3:
						package_name, arch = result[0].split(".")
						version, release = result[1].split("-")
						if ":" in version:
							version = version.split(":")[1]

						self.upgradable_packages[package_name] = {
							"name" : package_name,
							"version" : version,
							"release" : release,
							"fullname" : "{0}-{1}-{2}.{3}".format(package_name, version, release, arch)
						}

						self.upgradable_packages_count += 1

	def redhat_centos_vulscan(self):
		cmd = "yum --changelog --assumeno update"
		cve_obj = re.compile(r'(CVE-\d{4}-\d{4,})')
		pattern_begin = re.compile(r'ChangeLog for:')
		pattern_end = re.compile(r'Dependencies Resolved')

		for key, value in self.upgradable_packages.items():
			tmp_cmd = "{0} {1}".format(cmd, key)
			
			data, success, retcode = lib.exec_command(tmp_cmd.split())
			
			if retcode == 1 or retcode == 0:
				lines = data.split("\n")
				begin_founded = False
				
				#Changes in packages about to be updated:
				#
				#ChangeLog for: bash-4.1.2-48.el6.x86_64
				#* Wed Feb 15 04:00:00 2017 Siteshwar Vashisht <svashisht@redhat.com> - 4.1.2-48
				#- Fix signal handling in read builtin
				#  Resolves: #1421926

				#* Mon Dec 12 04:00:00 2016 Siteshwar Vashisht <svashisht@redhat.com> - 4.1.2-47
				#- CVE-2016-9401 - Fix crash when '-' is passed as second sign to popd
				#  Resolves: #1396383
				#
				#Dependencies Resolved
				for line in lines:
					if not begin_founded:
						if pattern_begin.match(line):
							begin_founded = True
						continue
						
					if pattern_end.match(line):
						break

					cves = cve_obj.findall(line)
					cves = list(set(cves))

					if len(cves) != 0 and line.startswith("-"):
						for cve_id in cves:
							self.redhat_append_vulsinfo(cve_id, value["name"], value["fullname"])

	def redhat_common_checkupdate(self):
		#FEDORA-2017-f9b4e14129 bugfix       vim-filesystem-2:8.0.983-1.fc26.x86_64
		#FEDORA-2017-f9b4e14129 bugfix       vim-minimal-2:8.0.983-1.fc26.x86_64
		#FEDORA-2017-b8fa8e1a13 Unknown/Sec. xen-libs-4.8.1-7.fc26.x86_64
		#FEDORA-2017-b8fa8e1a13 Unknown/Sec. xen-licenses-4.8.1-7.fc26.x86_64
		#data, success, retcode = lib.exec_command(["yum", "--security", "--bugfix", "updateinfo", "list", "updates"])
		data, success, retcode = lib.exec_command(["yum", "updateinfo", "list", "updates", "sec"])

		if success:
			lines = data.split("\n")

			for line in lines:
				result = line.split()

				if len(result) == 3:
					update_id = result[0]
					#update_type = result[1]
					update_package = result[2]

					result = update_package.rsplit("-", 2)

					if len(result) == 3:
						name = result[0]
						version = result[1]

						if "." in result[2]:
							release = result[2].rsplit(".", 1)[0]

						if self.upgradable_packages.has_key(update_id):
							self.upgradable_packages[update_id].append({
								"name" : name,
								"version" : version,
								"release" : release,
								"fullname" : update_package
							})
						else:
							self.upgradable_packages[update_id] = [{
								"name" : name,
								"version" : version,
								"release" : release,
								"fullname" : update_package
							}]

	def redhat_common_vulscan(self):
		cmd = "yum updateinfo info"
		cve_obj = re.compile(r'(CVE-\d{4}-\d{4,})')

		for key, value in self.upgradable_packages.items():
			tmp_cmd = "{} {}".format(cmd, key)

			data, success, retcode = lib.exec_command(tmp_cmd.split())

			if success:
				cves = cve_obj.findall(data)
				cves = list(set(cves))
				
				for cveid in cves:
					for info in value:
						self.redhat_append_vulsinfo(cveid, info["name"], info["fullname"])

	def redhat_append_vulsinfo(self, cveid, name, fullname):
		installed = self.get_installed_package_version(name)

		self.common_response(cveid, name, installed, fullname)
		
	############################################## Debian ####################################################
	def debian_update_packages(self):

		if lib.check_root():
			lib.exec_command(['apt-get', 'update'])
		else:
			data, success, retcode = lib.exec_command(['sudo', '-n', 'ls'])
			
			if success:
				lib.exec_command(['sudo', 'apt-get', 'update'])

	def debian_check_dependencies(self):
		aptitude = common.check_programs_installed("aptitude")

		if aptitude:
			self.changelogtool = "aptitude"
			return

		self.changelogtool = "apt-get"

	def debian_get_installed_packages(self):
		data, success, retcode = lib.exec_command(['dpkg-query', '-W'])
		
		#snap-confine    		2.25
		#snapd  				2.25
		#snapd-login-service	1.2-0ubuntu1.1~xenial
		#sni-qt:amd64			0.2.7+16.04.20170217.1-0ubuntu1
		if success:
			lines = data.split("\n")

			for line in lines:
				if line:
					package, ver = line.split()
					package = package.split(":")[0]

					self.installed_packages[package] = ver
					Klogger().info("package : {}  ver : {}".format(package, ver))

	def debian_get_upgradable_packages(self):
		data, success, retcode = lib.exec_command(['LANGUAGE=en_US.UTF-8', 'apt-get', 'upgrade', '--dry-run'])
		packages = []

		if success:
			lines = data.split("\n")
			pattern_begin = re.compile(r'The following packages will be upgraded:')
			pattern_end = re.compile(r'^(\d+) upgraded.*')

			begin_found = False

			for line in lines:

				if not begin_found:
					if pattern_begin.match(line):
						begin_found = True
					continue
					
				match = pattern_end.match(line)

				if match:
					num = int(match.groups()[0])

					if num == len(packages):
						#should return here
						Klogger().info("packages : {}".format(packages))
						return packages
					else:
						return None
				else:
					line = line.strip("\n")
					packages.extend(line.split())

		#error
		return packages

	def debian_scan_cveid_from_changelog(self):
		cmd = "PAGER=cat {} -q=2 changelog".format(self.changelogtool)
		cve_obj = re.compile(r'(CVE-\d{4}-\d{4,})')
		self.upgradable_packages = self.debian_get_upgradable_packages()
		self.upgradable_packages_count = len(self.upgradable_packages)

		for package_name in self.upgradable_packages:
			tmp_cmd = "{} {}".format(cmd, package_name)

			data, success, retcode = lib.exec_command(tmp_cmd.split())

			if success:
				lines = data.split("\n")
				pattern_ver = re.compile(r'(%s)' % re.escape(self.get_installed_package_version(package_name)))

				for line in lines:
					if pattern_ver.search(line):
						break
					else:
						cves = cve_obj.findall(line)
						cves = list(set(cves))

						for cve_id in cves:
							self.debian_append_vulsinfo(cve_id, package_name)
			else:
				Klogger().error("{} failed:{}".format(tmp_cmd, data))
				
	def debian_append_vulsinfo(self, cveid, package_name):
		installed = ""
		candidate = ""
		
		data, success, retcode = lib.exec_command(['apt-cache', 'policy', package_name])
		
		if success:
			pattern_installed = re.compile(r'\s*Installed:\s*(.*)\n')
			pattern_candidate = re.compile(r'\s*Candidate:\s*(.*)\n')
			
			match = pattern_installed.search(data)
			if match:
				installed = match.groups()[0]
				
			match = pattern_candidate.search(data)
			if match:
				candidate = match.groups()[0]
				
			Klogger().info("cveid : {} package : {} installed : {} candidate : {}".format(cveid, package_name, installed, candidate))
			
		if installed and candidate:
			self.common_response(cveid, package_name, installed, candidate)
			
	############################################## Redhat and Debian send function ####################################################
	def common_response(self, cveid, package_name, installed, candidate):
		if self.vuls.has_key(package_name):
			
			cves = self.vuls[package_name]["cves"]
			
			if cveid not in cves:
				cves.append(cveid)
				
		else:
			self.vuls[package_name] = {
				"installed" : installed,
				"candidate" : candidate,
				"candidate_size" : self.candidate_size(package_name, candidate),
				"cves" : [cveid]
			}
			
			print("package : {} cve : {}".format(package_name, cveid))
			
	#yum install yum-changelog
	def vulscan(self):
		self.reset()
		
		distro, distro_release = lib.detect_distribution()
		
		yum = common.check_programs_installed("yum")
		apt = common.check_programs_installed("apt-get")
		
		if yum:
			self.redhat_get_installed_packages()
			
			if "centos" in distro.lower():
				self.redhat_centos_checkupdate()
				self.redhat_centos_vulscan()
			else:
				self.redhat_common_checkupdate()
				self.redhat_common_vulscan()
				
		if apt:
			self.debian_update_packages()
			self.debian_check_dependencies()
			self.debian_get_installed_packages()
			self.debian_scan_cveid_from_changelog()
			
		vuls = Kdatabase().get_obj("vuls")
		vuls["items"] = self.vuls
		
		#self.vuls = {}