from utils import common
from datetime import datetime, timedelta
import time

def now():
	return int(time.time())

def get_last_min(t):
	if not t:
		t = time.time()

	a = int(t)
	b = a % 60

	return a - b

def get_last_day(t = None):
	if not t:
		t = time.time()

	t = time.localtime(t)
	time1 = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00', t), '%Y-%m-%d %H:%M:%S'))

	if common.is_python2x():
		return long(time1)
	else:
		return time1

def get_last_month(t = None):
	if not t:
		t = time.time()

	t = time.localtime(t)
	time1 = time.mktime(time.strptime(time.strftime('%Y-%m-1 00:00:00', t), '%Y-%m-%d %H:%M:%S'))

	if common.is_python2x():
		return long(time1)
	else:
		return time1

def get_last_nday_ts(n):
	t = time.time()
	last_nday = []

	for i in range(n):
		last_nday.append(get_last_day(t))
		t -= 60 * 60 * 24

	return last_nday

def get_last_nmonth_ts(n):
	t = time.localtime(time.time())
	year, month = t.tm_year, t.tm_mon
	last_nmonth = []

	for i in range(n):
		time_format = '{}-{}-1 00:00:00'.format(year, month)
		month -= 1

		if month == 0:
			year -= 1
			month = 12

		time1 = time.mktime(time.strptime(time_format, '%Y-%m-%d %H:%M:%S'))

		if common.is_python2x():
			time1 = long(time1)

		last_nmonth.append(time1)

	return last_nmonth

def get_last_nmonday_ts(n):
	today = datetime.fromtimestamp(get_last_day())
	monday = today - timedelta(days = today.weekday()) + timedelta(days = 0)
	last_nmonday = [to_timestamp(monday)]
	n -= 1

	for i in range(n):
		temp = monday - timedelta(days = 7 * (i + 1))
		last_nmonday.append(to_timestamp(temp))

	return last_nmonday

def to_timestamp(dt):
	return time.mktime(dt.timetuple())

def get_last_n_hour(n):
	return to_timestamp(datetime.now() - timedelta(hours = n))

def timestamp2string(timestamp):
	try:
		d = datetime.fromtimestamp(timestamp)
		return str(d.strftime("%Y-%m-%d %H:%M:%S"))
	except Exception as e:
		pass

	return '00/00/00'

def time2string(t):
	return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))

def localtime2string():
	return "{}{}{}{}{}{}".format(*(time.localtime()[0:6]))
