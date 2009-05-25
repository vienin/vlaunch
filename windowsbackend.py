# -*- coding: utf-8 -*-
# Author        : Kevin Pouget 
# Version       : 1.1
# Description   : Search any UFO key among usb devices, build appropriate .vmdk file, and start virtual machine.

import _winreg
# Ideally, we should use easygui, but it causes problems with py2exe
# import easygui
import win32gui, win32con, win32api
import subprocess
import os, os.path as path
import wmi
import sys
import logging
import conf
import time
import platform
from utils import *

VBOXMANAGE_EXECUTABLE = "VBoxManage.exe"
VIRTUALBOX_EXECUTABLE = "VirtualBox.exe"
WMI = None
systemdir = win32api.GetSystemDirectory ()

# class Blackhole(object):
#     def write(self, text):
#         pass

# sys.stdout = Blackhole()
# sys.stderr = Blackhole()
# del Blackhole

def build_command():
    if conf.STARTVM:
        if conf.KIOSKMODE:
            command = [ path.join(conf.BIN, "VBoxSDL.exe"), "-vm", conf.VM, "-termacpi", "-fullscreen", "-fullscreenresize", "-nofstoggle", "-noresize", "-nohostkeys", "fnpqrs" ]
        else:
            command = [ path.join(conf.BIN, "VBoxManage.exe"), "startvm", conf.VM ]
    else:
        command = [ path.join(conf.BIN, "VirtualBox.exe") ]
    return command
    

def start_services():
    if conf.CREATESRVS:
        logging.debug("Creating services :")

        if call([ "sc", "create", "PortableVBoxDRV",
                  "binpath=", path.join(conf.BIN, "drivers", "VBoxDrv", "VBoxDrv.sys"),
                  "type=", "kernel", "start=", "demand", "error=", "normal", "displayname=", "PortableVBoxDRV" ], shell=True) == 5:
            return 1
        call([ "sc", "create", "PortableVBoxUSBMon", "binpath=", path.join(conf.BIN, "drivers", "USB", "filter", "VBoxUSBMon.sys"),
                          "type=", "kernel", "start=", "demand", "error=", "normal", "displayname=", "PortableVBoxUSBMon" ], shell=True)
                         
        try:
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\VBoxUSB")
            if _winreg.QueryValue(key, "DisplayName") != "VirtualBox USB":
                call(["sc", "create", "VBoxUSB", "binpath=", path.join(conf.BIN, "drivers", "USB", "device", "VBoxUSB.sys"),
                                "type=", "kernel", "start=", "demand", "error=", "normal", "displayname=", "PortableVBoxUSB" ], shell=True)
        except:
            logging.debug("The key HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\VBoxUSB does not exist")
    
    if conf.STARTSRVS:
        logging.debug("Starting services :")
        
        if call([ "sc", "start", "PortableVBoxDRV" ], shell=True) in [ 1060, 5 ]:
           return 1

        call([ "sc", "start", "PortableVBoxUSBMon" ], shell=True)

    logging.debug("Re-registering server:")

    call([ path.join(conf.BIN, "VBoxSVC.exe"), "/reregserver" ], shell=True)
    call([ "regsvr32.exe", "/S", path.join(conf.BIN, "VBoxC.dll") ], shell=True)
    call([ "rundll32.exe", "/S", path.join(conf.BIN, "VBoxRT.dll"), "RTR3Init" ], cwd = conf.BIN, shell=True)
    
    return 0

def kill_resilient_vbox():
    call([ 'taskkill', '/F', '/IM', 'VBoxSVC.exe' ], shell=True) 

def process_wait_close(process):
    processes = WMI.Win32_Process(name=process)
    while processes:
        time.sleep(0.1)
        processes = WMI.Win32_Process(name=process)

def processes_wait_close():
    process_wait_close("VBoxSDL.exe")
    process_wait_close("VirtualBox.exe")
    process_wait_close("VBoxManage.exe")
    process_wait_close("VBoxSVC.exe")

def stop_services():
    if conf.STARTSRVS:
        call([ "sc", "stop", "PortableVBoxDRV" ], shell=True)
        call([ "sc", "stop", "PortableVBoxUSBMon" ], shell=True)
        call([ path.join(conf.BIN, "VBoxSVC.exe"), "/unregserver" ], shell=True)
        call([ "regsvr32.exe", "/S", "/U", path.join(conf.BIN, "VBoxC.dll") ], shell=True)

    if conf.CREATESRVS:
        call([ "sc", "delete", "PortableVBoxDRV" ], shell=True)
        call([ "sc", "delete", "PortableVBoxUSBMon" ], shell=True)

    try:
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\VBoxUSB")
        if _winreg.QueryValue(key, "DisplayName") != "VirtualBox USB":
            call([ "sc", "stop", "VBoxUSB" ], shell=True)
            call([ "sc", "delete", "VBoxUSB" ], shell=True)
    except:
        logging.debug("The key HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\VBoxUSB does not exist")

def find_device_by_uuid(dev_uuid):
    return ""
    
def find_device_by_volume(dev_volume):
    logical_disks = WMI.Win32_LogicalDisk (VolumeName = dev_volume)
    if not logical_disks:
        return ""
        
    partitions = logical_disks[0].associators(wmi_association_class="Win32_LogicalDiskToPartition")
    if not partitions:
        return ""
        
    disks = partitions[0].associators(wmi_result_class="Win32_DiskDrive")
    if len(disks) > 0:
        return disks[0].Name
    return ""

def find_device_by_model(model):
    disks = WMI.Win32_DiskDrive(Model = model)
    
    # Probably manage multiple UFO key choice...
    if len(disks) > 0:
        return disks[0].Name
    return ""
              
def prepare_device(dev):
    pass

def dialog_question(msg, title, button1, button2):
    ret = win32gui.MessageBox(None, title, msg, win32con.MB_YESNO)
    if ret == win32con.IDYES: return button1
    else: return button2

def dialog_info(msg, title):
    win32gui.MessageBox(None, msg, title, win32con.MB_OK)

def get_device_size(name):
    import win32file
    import win32con
    import winioctlcon
    import struct

    hFile = win32file.CreateFile(name, win32con.GENERIC_READ, 0, None, win32con.OPEN_EXISTING, 0, None)
    buffer = " " * 1024
    data = win32file.DeviceIoControl(hFile, winioctlcon.IOCTL_DISK_GET_DRIVE_GEOMETRY, buffer, 1024)
    tup = struct.unpack("qiiii", data)
    if tup[1] in (winioctlcon.FixedMedia, winioctlcon.RemovableMedia):
        size = reduce(int.__mul__, tup[:1] + tup[2:])
        logging.debug("Found FixedMedia or RemovableMedia of size " + str(size))
    data = win32file.DeviceIoControl(hFile, winioctlcon.IOCTL_DISK_GET_LENGTH_INFO, buffer, 1024)
    if data:
        tup = struct.unpack("q", data)
        size = tup[0]
        logging.debug("Found regular device of size " + str(size))
    return size >> 9

def list_devices():
    for disk in WMI.Win32_DiskDrive():
        print disk.Model

def find_network_device():
    if conf.NETTYPE in (conf.NET_NAT, conf.NET_HOST) and \
       not conf.VBOX_INSTALLED and \
       not path.exists(path.join(systemdir, "VBoxNetFltNotify.dll")):
        logging.debug("Installing VirtualBox driver")
        protocolpath = path.join(conf.BIN, "drivers", "network", "netflt")
        snetcfg = path.join(conf.BIN, "snetcfg_x86.exe")
        call([snetcfg, "-v", "-u", "sun_VBoxNetFlt"], shell=True)
        call([snetcfg, "-v", "-l", "drivers\\network\\netflt\\VBoxNetFlt.inf", # path.join(protocolpath, "VBoxNetFlt.inf"),
              "-m", "drivers\\network\\netflt\\VBoxNetFlt_m.inf", #  path.join("drivers", "network", "netflt", "miniport", "VBoxNetFlt_m.inf"),
              "-c", "s", "-i", "sun_VBoxNetFlt"], shell=True, cwd=conf.BIN)
        shutil.copy(path.join(protocolpath, "VBoxNetFltNotify.dll"), systemdir)
        shutil.copy(path.join(protocolpath, "VBoxNetFlt.sys"), path.join(systemdir, "drivers"))
        call(["regsvr32.exe", "/S", path.join(systemdir, "VBoxNetFltNotify.dll")], shell=True)

    if conf.NETTYPE == conf.NET_HOST:
        if conf.HOSTNET != "":
            return conf.NET_HOST, conf.HOSTNET
        
        net = WMI.Win32_networkadapter(NetConnectionStatus = 2)
    
        for adapter in net:
            try: logging.debug("Found net adapter " + adapter.Name)
            except: pass
            if '1394' in adapter.Name:
                continue
            # Probably except VMware connection for example...
            return conf.NET_HOST, adapter.Name

    return conf.NET_NAT, ""

def get_dvd_device():
    cds = WMI.Win32_CDROMDrive()
    drive, burner = None, False
    for cd in cds:
        if not burner: # Already found one, should use the faster one...
            drive, burner = cd.Id, 4 in cd.Capabilities
    
def find_resolution():
    display = WMI.Win32_DisplayControllerConfiguration()
    
    if len(display) > 0:
        return str(display[0].HorizontalResolution) + "x" + str(display[0].VerticalResolution)
    return ""

def get_free_ram ():
    try:
        ram = WMI.Win32_PerfFormattedData_PerfOS_Memory()
        if len(ram) > 0:
            return max((int(ram[0].AvailableBytes) + int(ram[0].CacheBytes)) / (1<<20), 384)
    except:
        logging.debug("Failed creating WMI object Win32_PerfFormattedData_PerfOS_Memory")
        ram = WMI.Win32_ComputerSystem()
        if len(ram) > 0:
            return max(int(ram[0].TotalPhysicalMemory) / 1024 / 1024 / 2, 384)
    return 0

def get_host_home():
    return path.expanduser('~'), "Mes documents Windows"
    
def get_usb_devices():
    logical_disks = WMI.Win32_LogicalDisk (DriveType = 2)
    return [ logical_disk.Caption + '\\' for logical_disk in logical_disks ], [ logical_disk.VolumeName for logical_disk in logical_disks ]

def rights_error():
    msg = u"Vous ne possédez pas les permissions nécessaires pour lancer UFO."
    logging.debug("Using Windows version " + str(platform.win32_ver()))
    if platform.win32_ver()[0].lower() == "vista":
        msg += u"\n\nExécutez UFO en tant qu'administrateur en sélectionnant :\nClic droit -> Exécuter en tant qu'administrateur"
    else:
        msg += u"\n\nExécutez UFO en tant qu'administrateur en sélectionnant :\nClic droit -> Exécuter en tant qu'administrateur"
    dialog_info(msg, u"Permissions insuffisantes")
    sys.exit(1)

def prepare():
    # Ajusting paths
    if not conf.HOME: conf.HOME = path.join(conf.APP_PATH, ".VirtualBox")
    try:
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\VBoxUSB")
        conf.VBOX_INSTALLED = True
    except:
        conf.VBOX_INSTALLED = False

    global WMI
    WMI = wmi.WMI()
    
    if start_services():
        logging.debug("Insufficient rights")
        rights_error()

def cleanup(command):
    processes_wait_close()
    stop_services()
    if conf.NETTYPE in (conf.NET_HOST, conf.NET_NAT) and not conf.VBOX_INSTALLED and conf.UNINSTALLDRIVERS:
      call(["regsvr32.exe", "/S", "/U", path.join(systemdir, "VBoxNetFltNotify.dll")])
      call([path.join(conf.BIN, "snetcfg_x86.exe"), "-v", "-u", "sun_VBoxNetFlt"])
      call(["sc", "delete", "VBoxNetFlt" ])
      # os.unlink(path.join(systemdir, "VBoxNetFltNotify.dll"))
      # os.unlink(path.join(systemdir, "drivers", "VBoxNetFlt.sys"))

def run_vbox(command, env):
    call(command, env = env, shell=True)
