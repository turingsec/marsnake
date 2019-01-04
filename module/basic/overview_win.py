from __future__ import division
import sys
import os
import platform
import getpass
if sys.version_info[0] == 2:
    import _winreg
else:
    import winreg as _winreg
import time
import pythoncom
import wmi
import psutil
from utils import common, time_op
from core.db import Kdatabase
from core.language import Klanguage

def get_network_card_info():
    reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                          "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\NetworkCards")
    info = []
    for i in range(6):
        try:
            descp = _winreg.QueryValueEx(_winreg.OpenKeyEx(
                reg, _winreg.EnumKey(reg, i)), 'Description')[0]
            info.append(descp)
        except:
            break

    return info

def get_bios_info():
    try:
        reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                              "HARDWARE\\DESCRIPTION\\System\\BIOS")
        info = _winreg.QueryValueEx(reg, 'BIOSVendor')[0]+' '
        info += _winreg.QueryValueEx(reg, 'BIOSVersion')[0]
    except:
        info = "Unknow"
        
    return info

def get_cpu_info():
    reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "HARDWARE\\DESCRIPTION\\System\\CentralProcessor")
    flag = True
    model_name = ""
    num = _winreg.QueryInfoKey(reg)[0]
    reg2 = _winreg.OpenKeyEx(reg, _winreg.EnumKey(reg, 0))
    model_name = _winreg.QueryValueEx(reg2, 'ProcessorNameString')[0]

    return "{} *{}".format(model_name, num)

def get_disk_partition(win32):
    info = []
    for physical_disk in win32.Win32_DiskDrive():
        for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
            for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                info.append(physical_disk.Caption + ' ' + partition.Caption + ' ' + logical_disk.Caption)
    return info

def get_windows_product_info():
    reg_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion")
    return _winreg.QueryValueEx(reg_key, "BuildLabEx")[0]

def get_gpu_info(win32):
    info = []
    for each in win32.Win32_videocontroller():
        info.append(each.Description)
    return info

def get_system_info(response):
    system_info = response["system_info"]

    system_info.append({Klanguage().to_ts(1024) : "{}/{}".format(get_windows_product_info(), platform.machine())})
    system_info.append({Klanguage().to_ts(1025) : common.get_distribution()})
    system_info.append({Klanguage().to_ts(1027) : time_op.timestamp2string(psutil.boot_time())})
    system_info.append({Klanguage().to_ts(1028) : time_op.timestamp2string(time.time())})

def get_hardware_info(response):
    pythoncom.CoInitialize()
    win32 = wmi.WMI()

    hardware = response["hardware"]

    hardware.append({Klanguage().to_ts(1011) : [get_cpu_info()]})
    #hardware.append({'Memory' : [""]})
    hardware.append({Klanguage().to_ts(1016) : get_disk_partition(win32)})
    hardware.append({Klanguage().to_ts(1017) : [get_bios_info()]})
    hardware.append({Klanguage().to_ts(1013) : get_gpu_info(win32)})
    hardware.append({Klanguage().to_ts(1012) : get_network_card_info()})

    pythoncom.CoUninitialize()

def get_mem_disk_info(response):
    #name    STATS   USED    MOUNT   FILESYSTEM
    for item in psutil.disk_partitions():
        device, mountpoint, fstype, opts = item

        try:
            total, used, free, percent = psutil.disk_usage(mountpoint)

            response["disk"][device] = percent
        except Exception:
            pass

    mem = psutil.virtual_memory()
    response["ram"]["total"] = common.size_human_readable(mem[0])
    response["ram"]["used"] = common.size_human_readable(mem[3])

def get_garbage(response):
    cleaner = Kdatabase().get_obj("cleaner")

    for kind, info in cleaner["kinds"].items():
        size = info["size"]

        if size > 0:
            response["garbage"].append({
                "name" : Klanguage().to_ts(info["name"]),
                "size" :  info["size"]
            })

def run(payload, socket):
    response = {
        "cmd_id" : "1008",
        "session_id" : payload["args"]["session_id"],
        "hardware" : [],
        "system_info" : [],
        "usage" : {
            "cpu" : [],
            "memory" : 0,
            "disk" : {
                "read" : [],
                "write" : []
            },
            "network" : {
                "tx" : [],
                "rx" : []
            }
        },
        "disk" : {},
        "ram" : {
            "total" : 0,
            "used" : 0
        },
        "garbage" : [],
        "error" : ""
    }

    get_hardware_info(response)
    get_system_info(response)
    get_mem_disk_info(response)
    get_garbage(response)

    monitor_second = Kdatabase().get_monitor_second()

    response["usage"]["cpu"] = common.extend_at_front(monitor_second["cpu"], 71, 0)
    try:
        response["usage"]["memory"] = monitor_second["memory"][-1]
    except:
        response["usage"]["memory"] = 0.0
    response["usage"]["disk"]["read"] = common.extend_at_front(monitor_second["disk_io"]["read"], 71, 0)
    response["usage"]["disk"]["write"] = common.extend_at_front(monitor_second["disk_io"]["write"], 71, 0)
    response["usage"]["network"]["tx"] = common.extend_at_front(monitor_second["net_io"]["tx"], 71, 0)
    response["usage"]["network"]["rx"] = common.extend_at_front(monitor_second["net_io"]["rx"], 71, 0)

    socket.response(response)
