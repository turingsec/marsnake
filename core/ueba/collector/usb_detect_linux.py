from pyudev import Context, Monitor
from pyudev import MonitorObserver
import pyudev, psutil

class usb_detect():
	def __init__(self, usb_plugged, usb_unplugged):
		self.usb_plugged = usb_plugged
		self.usb_unplugged = usb_unplugged
		
		self.context = pyudev.Context()
		self.monitor = pyudev.Monitor.from_netlink(self.context)
		self.monitor.filter_by('block')
		
	def do(self):
		#(u'add', u'/dev/sdb', u'disk', u'')
		#(u'add', u'/dev/sdb1', u'partition', u'ntfs')
		for device in iter(self.monitor.poll, None):
			if 'ID_FS_TYPE' in device:
				mnt = None
				
				for item in psutil.disk_partitions():
					dev, mountpoint, fstype, opts = item
					
					if dev == device.device_node:
						mnt = mountpoint
						break
						
				if device.action == "add":
					self.usb_plugged({
						"node" : device.device_node,
						"type" : device.device_type,
						"fs_type" : device.get('ID_FS_TYPE'),
						"mnt" : mnt
					})
				elif device.action == "remove":
					self.usb_unplugged({
						"node" : device.device_node,
						"type" : device.device_type,
						"fs_type" : device.get('ID_FS_TYPE'),
						"mnt" : mnt
					})