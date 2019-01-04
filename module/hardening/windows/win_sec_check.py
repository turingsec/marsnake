# encoding=utf-8
import os
try:
	import _winreg
except ImportError:
	import winreg as _winreg
import sys
import re,subprocess
import ctypes
import chardet

def QueryAutoCdRom():
	keypath=r'SYSTEM\CurrentControlSet\Services\cdrom'
	try:
		key=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,keypath)
		return  _winreg.QueryValueEx(key,'AutoRun')[0]
	except:
		return None

# def QueryHKCUNoDriveAutoRun():# 0-0x3FFFFFF 
# 	keypath=r'Software\Microsoft\Windows\CurrentVersion\Policies\Explorer'
# 	try:
# 		key=_winreg.OpenKey(_winreg.HKEY_CURRENT_USER,keypath)
# 		return  _winreg.QueryValueEx(key,'NoDriveAutoRun ')[0]
# 	except:
# 		return None

# def QueryHKCUNoDriveTypeAutoRun():
# 	keypath=r'Software\Microsoft\Windows\CurrentVersion\Policies\Explorer'
# 	try:
# 		key=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,keypath)
# 		return  _winreg.QueryValueEx(key,'NoDriveTypeAutoRun ')[0]
# 	except:
# 		return None

def QueryHKLMNoDriveAutoRun():
	keypath=r'Software\Microsoft\Windows\CurrentVersion\Policies\Explorer'
	try:
		key=_winreg.OpenKey(_winreg.HKEY_CURRENT_USER,keypath)
		return  _winreg.QueryValueEx(key,'NoDriveAutoRun ')[0]
	except:
		return None

def QueryHKLMNoDriveTypeAutoRun():
	keypath=r'Software\Microsoft\Windows\CurrentVersion\Policies\Explorer'
	try:
		key=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,keypath)
		return  _winreg.QueryValueEx(key,'NoDriveTypeAutoRun ')[0]
	except:
		return None

def QueryScreenSaver():
	keypath=r'Control Panel\Desktop'
	key=_winreg.OpenKey(_winreg.HKEY_CURRENT_USER,keypath)
	isSecure=0
	isSaverEnable=0
	saverTimeOut='0'
	try:
		ret=_winreg.QueryValueEx(key,'ScreenSaveActive')[0]
		if ret == u'1':
			isSaverEnable=1
		ret=_winreg.QueryValueEx(key,'ScreenSaverIsSecure')[0]
		if ret == u'1':
			isSecure=1
		saverTimeOut=_winreg.QueryValueEx(key,'ScreenSaveTimeOut')[0]# seconds
	except:
		pass
	return (isSaverEnable,isSecure,saverTimeOut)

def QueryFireWallState():
	t=subprocess.Popen("netsh advfirewall show allprofiles state",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	d=t.communicate()[0]
	du = d.decode(chardet.detect(d)['encoding'])
	ret=re.findall("(OFF|ON|"+u'启用'+'|'+u'关闭'+")",du)
	domainProfileState='OFF'
	privateProfileState='OFF'
	publicProfileState='OFF'
	if ret[0]==u'启用' or ret[0]=='ON':
		domainProfileState='ON'
	if ret[1]==u'启用' or ret[1]=='ON':
		privateProfileState='ON'
	if ret[2]==u'启用' or ret[2]=='ON':
		publicProfileState='ON'
	return (domainProfileState,privateProfileState,publicProfileState)

def QueryGuestUserState():
	t=subprocess.Popen("net user guest",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	du=t.communicate()[0].decode('gbk')
	ret=re.findall("(Yes|No)",du)
	isGuestEnable='Yes'
	if ret[0]==u'No':
		isGuestEnable='No'
	return isGuestEnable

def QueryIsCurrentUserAdmin():
	ret=os.getenv('username')
	if ret =='Administrator':
		return "Current User is Administrator!"
	return "It's OK."

def QueryUACLevel():
	if sys.platform != 'win32':
		return -1
	i, consentPromptBehaviorAdmin, enableLUA, promptOnSecureDesktop = 0, None, None, None
	try:
		Registry = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
		RawKey = _winreg.OpenKey(Registry, "SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")
	except:
		return -1
	while True:
		try:
			name, value, type = _winreg.EnumValue(RawKey, i)
			if name == "ConsentPromptBehaviorAdmin": consentPromptBehaviorAdmin = value
			elif name == "EnableLUA": enableLUA = value
			elif name == "PromptOnSecureDesktop": promptOnSecureDesktop = value
			i+=1
		except WindowsError:
			break
	if consentPromptBehaviorAdmin == 2 and enableLUA == 1:
		return 3
	elif consentPromptBehaviorAdmin == 5 and enableLUA == 1 and promptOnSecureDesktop == 1:
		return 2
	elif consentPromptBehaviorAdmin == 5 and enableLUA == 1 and promptOnSecureDesktop == 0:
		return 1
	elif enableLUA == 0:
		return 0
	return -1

def QueryIfIISInstalled():
	import urllib
	try:
		urllib.urlopen('http://localhost')
		return 'IIS is Running'
	except:
		return None
	#'Get-WindowsOptionalFeature -Online | where {$_.state -eq "Enabled"} | ft -Property featurename' need admin

def QueryOtherPoliciesSetting(response):# you need administrator privilege
	if ctypes.windll.shell32.IsUserAnAdmin() != 1:
		return "No privilege!"
	tmppath=os.getenv('temp')
	t=subprocess.Popen("secedit /export /cfg "+tmppath+"\\cur.cfg",stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	t.wait()
	fd=None
	try:
		fd=open(tmppath+"\\cur.cfg",'rb')
	except:
		print "Open cfg Fail!"
		return None
	tmpData=fd.read(1024)
	a=tmpData
	while tmpData:
		tmpData=fd.read(1024)
		a+=tmpData
	fd.close()
	os.remove(tmppath+"\\cur.cfg")

	encoding = chardet.detect(a)
	a = a.decode(encoding['encoding'])
	getValueOrNone = lambda x: x.group() if x else 'None'
	MaximumPasswordAge = getValueOrNone(re.search('(?<=MaximumPasswordAge = )-?\d+',a))#suggest less than 60
	MinimumPasswordLength = getValueOrNone(re.search('(?<=MinimumPasswordLength = )-?\d+',a))#suggest more than 14
	PasswordHistorySize = getValueOrNone(re.search('(?<=PasswordHistorySize = )-?\d+',a))#suggest 24
	PasswordComplexity = getValueOrNone(re.search('(?<=PasswordComplexity = )\d',a))
	LockoutBadCount = getValueOrNone(re.search('(?<=LockoutBadCount = )-?\d+',a))#suggest 10
	ResetLockoutCount = getValueOrNone(re.search('(?<=ResetLockoutCount = )-?\d+',a))
	LockoutDuration = getValueOrNone(re.search('(?<=LockoutDuration = )-?\d+',a))
	ForceLogoffWhenHourExpire = getValueOrNone(re.search('(?<=ForceLogoffWhenHourExpire = )-?\d+',a))
	NewAdministratorName = getValueOrNone(re.search('(?<=NewAdministratorName = ")\w+',a))
	EnableAdminAccount = getValueOrNone(re.search('(?<=EnableAdminAccount = )-?\d+',a))
	EnableGuestAccount = getValueOrNone(re.search('(?<=EnableGuestAccount = )-?\d+',a))
	ScRemoveOption = getValueOrNone(re.search('(?<=ScRemoveOption=1,")\d',a))# if your computer uses smartcard,enable this
	ConsentPromptBehaviorAdmin = getValueOrNone(re.search('(?<=ConsentPromptBehaviorAdmin=4,)\d',a))# '1' '3' need password.2,4 need prompt.'5' is default.should not be '0'
	ConsentPromptBehaviorUser = getValueOrNone(re.search('(?<=ConsentPromptBehaviorUser=4,)\d',a))# suggest 0
	MaxDevicePasswordFailedAttempts = getValueOrNone(re.search('(?<=MaxDevicePasswordFailedAttempts=4,)-?\d+',a))# if no bitlocker,you don't need it,otherwise,set to 10.
	LmCompatibilityLevel = getValueOrNone(re.search('(?<=LmCompatibilityLevel=4,)\d',a))# suggest 5.not must.
	allownullsessionfallback = getValueOrNone(re.search('(?<=allownullsessionfallback=4,)\d',a))#suggest 0
	AllowOnlineID = getValueOrNone(re.search('(?<=AllowOnlineID=4,)\d',a))#suggest 0
	RestrictAnonymous = getValueOrNone(re.search('(?<=RestrictAnonymous=4,)\d',a))#suggest 1
	SCENoApplyLegacyAuditPolicy = getValueOrNone(re.search('(?<=SCENoApplyLegacyAuditPolicy=4,)\d',a))#suggest 1
	AutoDisconnect = getValueOrNone(re.search('(?<=AutoDisconnect=4,)-?\d+',a))#suggest 15
	LMSEnableSecuritySignature = getValueOrNone(re.search(r'(?<=LanManServer\\Parameters\\EnableSecuritySignature=4,)\d',a))#suggest 1
	LMSRequireSecuritySignature = getValueOrNone(re.search(r'(?<=LanManServer\\Parameters\\RequireSecuritySignature=4,)\d',a))#suggest 1
	LWRequireSecuritySignature = getValueOrNone(re.search(r'(?<=LanmanWorkstation\\Parameters\\RequireSecuritySignature=4,)\d',a))#suggest 1
	LWEnableSecuritySignature = getValueOrNone(re.search(r'(?<=LanmanWorkstation\\Parameters\\EnableSecuritySignature=4,)\d',a))#suggest 1

	level = LEVEL_WARNING
	if MaximumPasswordAge != 'None':
		if int(MaximumPasswordAge,10) > 45:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['MaximumPasswordAge',MaximumPasswordAge,level,"Microsoft Baseline: 60."])
	level = LEVEL_WARNING
	if MinimumPasswordLength != 'None':
		if int(MinimumPasswordLength,10) > 7:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['MinimumPasswordLength',MinimumPasswordLength,level,"Microsoft Baseline: 14.We don't waring if it is bigger than 7."])
	level = LEVEL_WARNING
	if PasswordHistorySize != 'None':
		if int(PasswordHistorySize,10) >= 24:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['PasswordHistorySize',PasswordHistorySize,level,"Microsoft Baseline: 24."])
	level = LEVEL_WARNING
	if PasswordComplexity != 'None':
		if int(PasswordComplexity,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['PasswordComplexity',PasswordComplexity,level,"Microsoft Baseline: 1."])
	level = LEVEL_WARNING
	if LockoutBadCount != 'None':
		if int(LockoutBadCount,10) > 9:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['LockoutBadCount',LockoutBadCount,level,"Microsoft Baseline: 10."])
	level = LEVEL_WARNING
	if ResetLockoutCount != 'None':
		if int(ResetLockoutCount,10) > 0:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['ResetLockoutCount',ResetLockoutCount,level,"Microsoft Baseline: 15."])
	level = LEVEL_WARNING
	if LockoutDuration != 'None':
		if int(LockoutDuration,10) > 0:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['LockoutDuration',LockoutDuration,level,"Microsoft Baseline: 15."])
	level = LEVEL_WARNING
	if ForceLogoffWhenHourExpire != 'None':
		if int(ForceLogoffWhenHourExpire,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['ForceLogoffWhenHourExpire',ForceLogoffWhenHourExpire,level,"Microsoft Baseline: 1."])
	level = LEVEL_WARNING
	if NewAdministratorName != 'Administrator':
		level = LEVEL_SECURITY
	response['authentication'].append(
		['NewAdministratorName',NewAdministratorName,level,"We advice you change your administrator account's user name instead of the default name--'Administrator'."])
	level = LEVEL_WARNING
	if EnableAdminAccount != 'None':
		if int(EnableAdminAccount,10) == 0:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['EnableAdminAccount',EnableAdminAccount,level,"Microsoft Baseline: disable it."])
	level = LEVEL_WARNING
	if EnableGuestAccount != 'None':
		if int(EnableGuestAccount,10) == 0:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['EnableGuestAccount',EnableGuestAccount,level,"Microsoft Baseline: disable it."])
	level = LEVEL_WARNING
	if ScRemoveOption != 'None':
		if int(ScRemoveOption,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['ScRemoveOption',ScRemoveOption,level,"Microsoft Baseline: enable it."])
	level = LEVEL_WARNING
	if ConsentPromptBehaviorAdmin != 'None':
		if int(ConsentPromptBehaviorAdmin,10) in (1,2,3,4):
			level = LEVEL_SECURITY
	response['authentication'].append(
		['ConsentPromptBehaviorAdmin',ConsentPromptBehaviorAdmin,level,"Microsoft Baseline: 1.If you are a normal user,setting it to 2 is enough."])
	level = LEVEL_WARNING
	if ConsentPromptBehaviorUser != 'None':
		if int(ConsentPromptBehaviorUser,10) == 0:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['ConsentPromptBehaviorUser',ConsentPromptBehaviorUser,level,"Microsoft Baseline: 0."])
	level = LEVEL_WARNING
	if MaxDevicePasswordFailedAttempts != 'None':
		if int(MaxDevicePasswordFailedAttempts,10) > 800:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['MaxDevicePasswordFailedAttempts',MaxDevicePasswordFailedAttempts,level,"Microsoft Baseline: 900."])
	level = LEVEL_WARNING
	if LmCompatibilityLevel != 'None':
		if int(LmCompatibilityLevel,10) == 5:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['LmCompatibilityLevel',LmCompatibilityLevel,level,"Microsoft Baseline: 5."])
	level = LEVEL_WARNING
	if allownullsessionfallback != 'None':
		if int(allownullsessionfallback,10) == 0:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['allownullsessionfallback',allownullsessionfallback,level,"Microsoft Baseline: 0."])
	level = LEVEL_WARNING
	if AllowOnlineID != 'None':
		if int(AllowOnlineID,10) == 0:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['AllowOnlineID',AllowOnlineID,level,"Microsoft Baseline: 0."])
	level = LEVEL_WARNING
	if RestrictAnonymous != 'None':
		if int(RestrictAnonymous,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['RestrictAnonymous',RestrictAnonymous,level,"Microsoft Baseline: Enable it."])
	level = LEVEL_WARNING
	if SCENoApplyLegacyAuditPolicy != 'None':
		if int(SCENoApplyLegacyAuditPolicy,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['SCENoApplyLegacyAuditPolicy',SCENoApplyLegacyAuditPolicy,level,"Microsoft Baseline: Enable it."])
	level = LEVEL_WARNING
	if AutoDisconnect != 'None':
		if int(AutoDisconnect,10) > 10:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['LMSAutoDisconnect',AutoDisconnect,level,"Microsoft Baseline: 15."])
	level = LEVEL_WARNING
	if LMSEnableSecuritySignature != 'None':
		if int(LMSEnableSecuritySignature,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['LMSEnableSecuritySignature',LMSEnableSecuritySignature,level,"Microsoft Baseline: Enable it."])
	level = LEVEL_WARNING
	if LMSRequireSecuritySignature != 'None':
		if int(LMSRequireSecuritySignature,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['LMSRequireSecuritySignature',LMSRequireSecuritySignature,level,"Microsoft Baseline: Enable it."])
	level = LEVEL_WARNING
	if LWRequireSecuritySignature != 'None':
		if int(LWRequireSecuritySignature,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['LWRequireSecuritySignature',LWRequireSecuritySignature,level,"Microsoft Baseline: Enable it."])
	level = LEVEL_WARNING
	if LWEnableSecuritySignature != 'None':
		if int(LWEnableSecuritySignature,10) == 1:
			level = LEVEL_SECURITY
	response['authentication'].append(
		['LWEnableSecuritySignature',LWEnableSecuritySignature,level,"Microsoft Baseline: Enable it."])




LEVEL_INVALID = -1
LEVEL_SECURITY = 0
LEVEL_WARNING = 1
LEVEL_CRITICAL = 2

def getResponse(response):
	# normal Security Settings
	ret = QueryAutoCdRom()
	level = LEVEL_WARNING if ret else 'None'
	response['kernel'].append(["AutoRun",ret,level,"Determines whether the system sends a Media Change Notification (MCN) message to the Windows interface when it detects that a CD-ROM is inserted in the drive. The MCN message triggers media-related features, such as Autoplay.\n\nIf you don't trust the CD-ROM,we suggest you disable it."])
	
	ret = QueryHKLMNoDriveTypeAutoRun()
	level = LEVEL_WARNING
	if ret == 0xff:
		level = LEVEL_SECURITY
	elif ret==None:
		ret = 'None'
	response['kernel'].append(["HKLM_NoDriveTypeAutoRun",ret,level,"Disables the Autoplay feature on all drives of the type specified.\n\nIf you don't need a usb driver,we suggest you disable all."])

	level = LEVEL_WARNING
	ret = QueryHKLMNoDriveAutoRun()
	if ret == 0x3FFFFFF:
		level = LEVEL_SECURITY
	elif ret==None:
		ret = 'None'
	response['kernel'].append(["HKLM_NoDriveAutoRun",ret,level,"Determines whether Autoplay is enabled on each drive connected to the system. When Autoplay is enabled, media starts automatically when it is inserted in the drive.\n\nIf you don't need a usb driver,we suggest you disable all."])

	level = LEVEL_WARNING
	ret = QueryIfIISInstalled()
	if ret == None:
		level = LEVEL_SECURITY
		ret = 'Not Running'
	response['kernel'].append(["IIS Server State",ret,level,"IIS is an Internet Information Services,if you don't need it,you should disable it."])
	
	level = LEVEL_CRITICAL
	(isSaverEnable,isSecure,saverTimeOut) = QueryScreenSaver()
	suggest	= 'We suggest you enable this.'
	if isSaverEnable:
		level = LEVEL_WARNING
		if isSecure:
			level = LEVEL_SECURITY
		if int(saverTimeOut,10) < 1200:
			level = LEVEL_WARNING
			suggest = 'Your timeout is too long,we suggest you set it less than 1200s.'
	ret = 'IsEnable:'+str(isSaverEnable)+'  IsPasswordNeedWhenUnlock:'+ \
		str(isSecure)+'  TimeOutToLock:'+saverTimeOut+' seconds'
	response['kernel'].append(['ScreenSaver',ret,level,"If you forget to lock your computer when you leave away,the screen saver will autolock it after timeout." + suggest])
	
	level = LEVEL_WARNING
	ret = QueryGuestUserState()
	if ret=='No':
		level = LEVEL_SECURITY
	response['kernel'].append(['Guest User State',ret,level,"When someone is visiting for a while and needs access to your Windows computer or tablet, you should not give away your user account details. The best thing you can do is enable the Guest account in Windows and have your visitor use it.\n\nIf you don't need it,we suggest you disable it."])
	
	# Feature
	level = LEVEL_CRITICAL
	(domainProfileState,privateProfileState,publicProfileState) = QueryFireWallState()
	if domainProfileState=='ON' and privateProfileState=='ON' and publicProfileState=='ON':
		level = LEVEL_SECURITY
	firewallValue='domainProfileState:'+domainProfileState+ \
		'  privateProfileState:'+privateProfileState+'  publicProfileState:'+publicProfileState
	response['feature'].append(
		['Firewall State',firewallValue,level,"Firewall keeps your computer safe from Internet,you must not disable it."])

	level = LEVEL_CRITICAL
	ret = QueryUACLevel()
	if ret > 0:
		level = LEVEL_SECURITY
	response['feature'].append(["UAC level",ret,level,"You must set your UAC level more than 0."])

	# Local Policies
	QueryOtherPoliciesSetting(response)

def run(payload, socket):
	response = {
		'cmd_id' : payload['cmd_id'],
		"session_id" : payload["args"]["session_id"],
		"kernel" : [['name','value','level','suggest']],
		"authentication" : [['name','value','level','suggest']],
		"feature" : [['name','value','level','suggest']],
		"name" : ["Security Feature", "Normal Security Settings", "Local Policies"],
		'error' : ""
	}
	getResponse(response)
	# socket.response(response)
	print response

run({'cmd_id':1001,'args':{'session_id':1000}},'')
# kernel:{"name":"","values":[["name","xx","xx"],如果没有子list,就不用list] "data"}
# feature:[['x','x','x'],[key,value,level,suggest]]
# authentication:[['x','title'],[]]