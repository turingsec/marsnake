from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QWidget, QAction, QApplication, QCheckBox, QComboBox,
		QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
		QMessageBox, QMenu, QPushButton, QSpinBox, QStyle, QSystemTrayIcon,
		QTextEdit, QVBoxLayout, QInputDialog)
from PyQt5.QtCore import (QThread, QTimer, QFile, QSettings)

from PyQt5 import QtCore, QtGui, QtWidgets
from utils import common, net_op
from core.profile_reader import KProfile
#from core.computer_score import KScore
from ui import resources_rc
from ui.login import Ui_Login
from ui.settings import Ui_Settings
from ui.about import Ui_About
from ui.startup import KStartup
import urllib.parse, json
from multiprocessing import Pipe
import start

wlogin = None
wsettings = None
wabout = None

ti = None
main_proc = None
machine_status = {
	"virus_count": 0,
	"vuls_count": 0,
	"threat_count": 0,
	"monitor_count": 0,
	"audit_count": 0,
	"garbage_count": "0 GB",
	"score": 100
}
parent_end = None
child_end = None

def start_python_main():
	global main_proc
	global parent_end
	global child_end

	parent_end, child_end = Pipe()

	main_proc = common.fork_process(start.python_main, (child_end,))
	main_proc.daemon = True
	main_proc.start()

def terminate_main():
	global main_proc
	global parent_end
	global child_end

	if main_proc:
		main_proc.terminate()

	if parent_end and child_end:
		parent_end.close()
		child_end.close()

		parent_end = None
		child_end = None

def try_to_login(host, port, username, password, encrypt = 0):
	ret_code = 3
	status, data = net_op.create_http_request("{}:{}".format(host, port),
		"POST",
		"/client/login",
		urllib.parse.urlencode({'username': username, 'password': password, 'encrypt': encrypt}),
		{"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"})

	if not data:
		return ret_code

	ret = json.loads(data)

	if "code" in ret:
		if ret["code"] == 0:
			fullname = ret["fullname"]

			KProfile().write_username_fullname(username, fullname)

			global ti
			ti.checkout_loggon = True
			ti.loggon_menu.setTitle("&{}({})".format(fullname, username))
			ti.set_icon()

			start_python_main()

			return 0
		elif ret["code"] == -10 or ret["code"] == -5:	#USERNAME_NOT_EXIST, USERNAMEORPWD_ERROR
			ret_code = 1
		else:											#TEAM_NOT_EXISTS, NOT_JOIN_A_TEAM
			ret_code = 2

	KProfile().write_password("")
	return ret_code

class TrayIcon(QSystemTrayIcon):
	def __init__(self, parent = None):
		super(TrayIcon, self).__init__(parent)

		self.checkout_loggon = False

		# UI
		self.createActions()
		self.createTrayIcon()

		self.set_icon()

		self.setToolTip("Marsnake正在保护您的设备")

	def set_icon(self):
		global machine_status

		score = machine_status["score"]
		icon_png = ""

		if self.checkout_loggon:
			if score == 100:
				icon_png = ":icons/status_0.png"
			elif score >= 80:
				icon_png = ":icons/status_1.png"
			elif score >= 30:
				icon_png = ":icons/status_2.png"
			else:
				icon_png = ":icons/status_3.png"
		else:
			icon_png = ":icons/icon.png"

		# Draw system tray icon
		pixmap = QtGui.QPixmap(QtGui.QPixmap(icon_png))

		self.setIcon(QtGui.QIcon(pixmap))
		# End drawing system tray icon

		# Menu actions
	def createActions(self):
		self.inprotected = QAction("&Marsnake正在保护您的设备", self)
		self.inprotected.setDisabled(True)
		self.setting = QAction("&设置", self, triggered = self.trigger_setting)
		self.quit_proc = QAction("&退出", self, triggered = self.trigger_exit)
		self.tologin = QAction("&登录", self, triggered = self.trigger_tologin)
		self.logout = QAction("&退出登录", self, triggered = self.trigger_logout)

		self.goto_online = QAction("&访问网页", self, triggered = self.trigger_goto_online)

		self.help_checkupdate = QAction("&检查更新", self, triggered = self.trigger_help_checkupdate)
		self.help_feedback = QAction("&问题反馈", self, triggered = self.trigger_help_feedback)
		self.help_instruction = QAction("&使用说明书", self, triggered = self.trigger_help_instruction)
		self.help_about = QAction("&关于", self, triggered = self.trigger_help_about)

		self.status_virus = QAction("&发现病毒: 0", self, triggered = self.trigger_goto_online)
		self.status_vuls = QAction("&发现漏洞: 0", self, triggered = self.trigger_goto_online)
		self.status_threat = QAction("&威胁事件: 0", self, triggered = self.trigger_goto_online)
		self.status_resource = QAction("&资源异常: 0", self, triggered = self.trigger_goto_online)
		self.status_audit = QAction("&基线检查: 0", self, triggered = self.trigger_goto_online)
		self.status_garbage = QAction("&系统垃圾: 0 GB", self, triggered = self.trigger_goto_online)

		# UI functions
	def createTrayIcon(self):
		self.main_menu = QMenu()
		self.help_menu = QMenu()
		self.loggon_menu = QMenu()
		self.status_menu = QMenu()

		self.help_menu.setTitle("帮助")
		#self.help_menu.addAction(self.help_checkupdate)
		#self.help_menu.addAction(self.help_feedback)
		self.help_menu.addAction(self.help_instruction)
		self.help_menu.addAction(self.help_about)

		self.loggon_menu.addAction(self.logout)

		self.status_menu.setTitle("系统状态: 100分")
		self.status_menu.addAction(self.status_virus)
		self.status_menu.addAction(self.status_vuls)
		self.status_menu.addAction(self.status_threat)
		self.status_menu.addAction(self.status_resource)
		self.status_menu.addAction(self.status_audit)
		self.status_menu.addAction(self.status_garbage)

		self.main_menu.addAction(self.inprotected)
		self.main_menu.addMenu(self.loggon_menu)
		self.main_menu.addAction(self.tologin)

		self.main_menu.addSeparator()
		self.main_menu.addMenu(self.status_menu)
		self.main_menu.addAction(self.setting)
		self.main_menu.addAction(self.goto_online)
		self.main_menu.addMenu(self.help_menu)
		self.main_menu.addAction(self.quit_proc)

		self.setContextMenu(self.main_menu)
		self.activated.connect(self.trayIconActivated)

	def trigger_goto_online(self):
		QtGui.QDesktopServices.openUrl(QtCore.QUrl('http://marsnake.com/login'))

	def trigger_help_checkupdate(self):
		self.showMessage("测试", "检查更新")

	def trigger_help_feedback(self):
		self.showMessage("测试", "问题反馈")

	def trigger_help_instruction(self):
		QtGui.QDesktopServices.openUrl(QtCore.QUrl('http://marsnake.com/release/Marsnake_Instruction.pdf'))

	def trigger_help_about(self):
		global wabout

		wabout.show()
		wabout.activateWindow()

	def trigger_tologin(self):
		global wlogin

		wlogin.show()
		wlogin.activateWindow()

	def trigger_setting(self):
		global wsettings

		wsettings.show()
		wsettings.activateWindow()

	def trigger_logout(self):
		self.checkout_loggon = False
		self.set_icon()

		#KProfile().write_username_fullname("", "")
		KProfile().write_password("")

		terminate_main()

	def trigger_exit(self):
		terminate_main()
		QApplication.instance().quit()

	def trayIconActivated(self, reason):
		#更新系统状态信息
		global machine_status

		if self.checkout_loggon:
			self.inprotected.setText("&Marsnake正在保护您的设备")
			self.inprotected.setVisible(True)
			self.loggon_menu.menuAction().setVisible(True)
			self.status_menu.menuAction().setVisible(True)
			self.tologin.setVisible(False)
		else:
			self.inprotected.setVisible(False)
			self.loggon_menu.menuAction().setVisible(False)
			self.status_menu.menuAction().setVisible(False)
			self.tologin.setVisible(True)

		self.status_menu.setTitle("系统状态: {}分".format(machine_status["score"]))
		self.status_virus.setText("&发现病毒: {}".format(machine_status["virus_count"]))
		self.status_vuls.setText("&发现漏洞: {}".format(machine_status["vuls_count"]))
		self.status_threat.setText("&威胁事件: {}".format(machine_status["threat_count"]))
		self.status_resource.setText("&资源异常: {}".format(machine_status["monitor_count"]))
		self.status_audit.setText("&基线检查: {}".format(machine_status["audit_count"]))
		self.status_garbage.setText("&系统垃圾: {}".format(machine_status["garbage_count"]))

class Login(QDialog):
	def __init__(self):
		super(Login, self).__init__()

		self.ui = Ui_Login()
		self.ui.setupUi(self)

		self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.trigger_btn_ok_clicked)
		self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.trigger_btn_cancel_clicked)

		self.setWindowFlags(QtCore.Qt.Window)#QtCore.Qt.WindowMinimizeButtonHint

	def showEvent(self, event):
		self.ui.show()
		
	def closeEvent(self, event):
		event.ignore()
		self.hide()

	def trigger_btn_ok_clicked(self):
		host = self.ui.txtbox_server.text()
		port = self.ui.txtbox_port.text()
		username = self.ui.txtbox_username.text()
		password = self.ui.txtbox_password.text()

		ret = try_to_login(host, port, username, password)

		if ret == 0:
			KProfile().write_server_conn(host, port)
			KProfile().write_password(common.sha256_hmac(password))

			QMessageBox.information(self, "登录", "登录成功", QMessageBox.Yes)
			self.accept()
		elif ret == 1:
			QMessageBox.information(self, "登录", "账号或密码错误", QMessageBox.Yes)
		elif ret == 2:
			QMessageBox.information(self, "登录", "请先加入团队以使用Marsnake", QMessageBox.Yes)
			QtGui.QDesktopServices.openUrl(QtCore.QUrl('http://marsnake.com/login'))
		else:
			QMessageBox.information(self, "登录", "连接服务器失败", QMessageBox.Yes)

	def trigger_btn_cancel_clicked(self):
		self.reject()

class Settings(QDialog):
	def __init__(self):
		super(Settings, self).__init__()

		self.ui = Ui_Settings()
		self.ui.setupUi(self)

		self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.trigger_btn_ok_clicked)
		self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.trigger_btn_cancel_clicked)

		self.setWindowFlags(QtCore.Qt.Window)

	def showEvent(self, event):
		self.ui.show()

	def closeEvent(self, event):
		event.ignore()
		self.hide()

	def trigger_btn_ok_clicked(self):
		remote_support_code = self.ui.remote_support_code.text()

		if remote_support_code:
			startup = self.ui.auto_startup.isChecked()

			if startup:
				if not KStartup().query_auto_run():
					KStartup().enable_auto_run()
			else:
				if KStartup().query_auto_run():
					KStartup().disable_auto_run()

			KProfile().write_settings(self.ui.auto_vul_repair_interval.currentData(),
											self.ui.auto_cleaner_interval.currentData(),
											self.ui.virus_scan_interval.currentData(),
											self.ui.allow_terminal.isChecked(),
											self.ui.allow_vnc.isChecked(),
											self.ui.remote_support_code.text())

			self.accept()
		else:
			QMessageBox.information(self, "设置", "连接码不能为空", QMessageBox.Yes)

	def trigger_btn_cancel_clicked(self):
		self.reject()

class About(QDialog):
	def __init__(self):
		super(About, self).__init__()

		self.ui = Ui_About()
		self.ui.setupUi(self)

		self.setWindowFlags(QtCore.Qt.Window)

	def closeEvent(self, event):
		event.ignore()
		self.hide()

	def trigger_btn_ok_clicked(self):
		self.accept()

class MyWindow(QWidget):
	def __init__(self, parent = None):
		super(MyWindow, self).__init__(parent)
		global ti

		ti = TrayIcon(self)
		ti.show()

		self.timer = QTimer(self)
		self.timer.timeout.connect(self.status_check)
		self.timer.setInterval(1000 * 10)
		self.timer.start()

		username = KProfile().read_username()
		password = KProfile().read_password()
		server_conn = KProfile().read_server()

		ret = try_to_login(server_conn["host"], server_conn["port"], username, password, 1)

		if ret != 0:
			ti.trigger_tologin()
		else:
			self.status_check()

	def status_check(self):
		global machine_status, ti
		global parent_end

		if ti.checkout_loggon and parent_end:
			#ask child for machine status
			parent_end.send({"code": 1})

			warning, score = parent_end.recv()

			machine_status["virus_count"] = warning["virus"]["detail"]
			machine_status["vuls_count"] = warning["vuls"]["detail"]

			ueba_detail = warning["ueba"]["detail"]
			machine_status["threat_count"] = 0

			for i in ueba_detail:
				machine_status["threat_count"] += i

			monitor_detail = warning["monitor"]["detail"]
			machine_status["monitor_count"] = 0

			for i in monitor_detail:
				machine_status["monitor_count"] += monitor_detail[i]

			machine_status["audit_count"] = warning["audit"]["detail"]["critical"] + warning["audit"]["detail"]["warning"]
			machine_status["garbage_count"] = common.size_human_readable(warning["cleaner"]["detail"])
			machine_status["score"] = score
			# else:
			# 	import random
			# 	machine_status["score"] = random.randint(0, 100)
			# 	print(machine_status["score"])

			ti.set_icon()

def signal_term_handler(signal, frame):
	global ti

	ti.trigger_exit()

def ui_main():
	import sys
	global wlogin, wsettings, wabout

	app = QApplication(sys.argv)
	systemtray_timeout = 0

	# Check if DE supports system tray
	while not QSystemTrayIcon.isSystemTrayAvailable():
		systemtray_timeout += 1
		time.sleep (20)
		if systemtray_timeout == 5:
			QMessageBox.critical(None, "Mail notifier",
					"I couldn't detect any system tray on this system.")
			sys.exit(1)

	QApplication.setQuitOnLastWindowClosed(False)

	import signal
	signal.signal(signal.SIGTERM, signal_term_handler)

	wabout = About()
	wlogin = Login()
	wsettings = Settings()
	window = MyWindow()

	sys.exit(app.exec_())

if __name__ == '__main__':
	ui_main()
