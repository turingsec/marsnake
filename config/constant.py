VERSION = "v0.1"

DEBUG = False

TMP_DIRECTORY = ".marsnake"
TMP_FILE = "tmp_file.zip"

FILE_TRANSFER_SIZE_PER_TIME = 1 * 512 * 1024
SOCKET_BUFFER_SIZE = 4 * 1024 * 1024
SOCKET_RECV_SIZE = 1 * 1024 * 1024

RSA_PRIVATE_KEY = "config/private_key_2048.pem"
RSA_PUBLIC_KEY = "config/public_key_2048.pem"
CREDENTIAL = "config/credential"
SERVER_PUBLIC_KEY = "config/server_public_key.pem"

#LOG
LOG_FILE = "log/marsnake.log"
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

SERVER_URL = "gateway.turingsec.com:443"

MSG_ID = []

ALLOW_MODULE_ID = {
	"1000" : {
		"des" : "module/basic/get_info.py",
		"enabled" : True
	},
	"1007" : {
		"des" : "module/status/network_status.py",
		"enabled" : True
	},
	"1008" : {
		"des" : "module/basic/overview.py",
		"enabled" : True
	},
	"10081" : {
		"des" : "module/basic/overview_win.py",
		"enabled" : True
	},
	"1009" : {
		"des" : "module/basic/system_status.py",
		"enabled" : True
	},
	"1010" : {
		"des" : "module/status/cpu_status.py",
		"enabled" : True
	},
	"1011" : {
		"des" : "module/status/ram_status.py",
		"enabled" : True
	},
	"1012" : {
		"des" : "module/status/disk_status.py",
		"enabled" : True
	},
	"1013" : {
		"des" : "module/status/user_status.py",
		"enabled" : True
	},
	"1015" : {
		"des" : "module/hardening/web_scan.py",
		"enabled" : True
	},
	"1016" : {
		"des" : "module/hardening/vulscan.py",
		"enabled" : True
	},
	"1017" : {
		"des" : "module/runshell.py",
		"enabled" : True
	},
	"1022" : {
		"des" : "module/hardening/boot_services.py",
		"enabled" : True
	},
	"1023" : {
		"des" : "module/hardening/kernel.py",
		"enabled" : True
	},
	"1025" : {
		"des" : "module/hardening/authentication.py",
		"enabled" : True
	},
	"1026" : {
		"des" : "module/hardening/network_audit.py",
		"enabled" : True
	},
	"1027" : {
		"des" : "module/status/service_status.py",
		"enabled" : True
	},
	"1028" : {
		"des" : "module/hardening/weakpwd_scan.py",
		"enabled" : True
	},
	"1030" : {
		"des" : "module/status/process_detail.py",
		"enabled" : True
	}
}

