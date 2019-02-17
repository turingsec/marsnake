STORY_KIND = {
	"INSTRUSION" : 0,
	"PRIVILEGE_ESCALATION" : 1,
	"LATERAL_MOVEMENT" : 2,
	"CC" : 3,
	"DATA_LOSS" : 4,
	"MAX" : 5
}

SUB_STORY_KIND = {
	"1000" : [0, "Unauthorized user"],
	"1001" : [1, "Known malware"],
	"1002" : [2, "Unknown malware"],
	"1003" : [3, "Injected process"],
	"1004" : [4, "Vulnerability"],
	"1005" : [5, "Illegal process"]
}

ACTIVITY = {
	"10000" : [0, "Scanning"],
	"10001" : [1, "Privilege escalation"],
	"10002" : [2, "Lateral movement"],
	"10003" : [3, "C&C"],
	"10004" : [4, "Data loss"],
	"10005" : [5, "Backdoor"]
}

EVENTS = {
	"USB_PLUGGED" : 0,
	"MALWARE_DETECT" : 1,
	"SSH_FAILED" : 2,
	"SSH_SUCCESS" : 3,
	"MALICIOUS_IP_REPORT" : 4,
	"MALWARE_PROC_DETAIL" : 5,
	"BACKDOOR" : 6
}

SCORE = {
	"NOTIFY" : 0,
	"WARNING" : 10,
	"DANGEROUS" : 60,
	"VULNERABLE" : 100,
	"VULNERABLE_THRESHOLD" : 100
}

RISK_LEVEL = {
	"NORMAL" : 0,
	"LOW_RISK" : 1,
	"HIGH_RISK" : 2,
	"VULNERABLE" : 3
}

PERIOD_BACKDOOR_SCAN = 30
PERIOD_SSH_SCAN = 30
PERIOD_IP_SCAN = 30

AUTH_LOG = "/var/log/auth.log"
SECURE_LOG = "/var/log/secure.log"