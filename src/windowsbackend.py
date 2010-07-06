# -*- coding: utf-8 -*-

# UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
#
# Copyright (c) 2008-2010 Agorabox, Inc.
#
# This is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA. 


import _winreg
import win32con
import os, os.path as path
import wmi
import sys
import logging
from conf import conf
import tempfile
import platform
import glob
import gui
import time
import utils

from osbackend import OSBackend
from shutil import copyfile, copytree

class WindowsBackend(OSBackend):

    VBOXMANAGE_EXECUTABLE = "VBoxManage.exe"
    VIRTUALBOX_EXECUTABLE = "VirtualBox.exe"
    RELATIVE_VMDK_POLICY  = False

    def __init__(self):
        OSBackend.__init__(self, "windows")
        self.WMI = wmi.WMI()

    def get_default_audio_driver(self):
        return self.vbox.constants.AudioDriverType_DirectSound

    def check_process(self):
        logging.debug("Checking UFO process")
        # TODO: Get pid for possible kill
        processes = []
        for p in  self.WMI.Win32_Process():
            if "ufo" in p.Name or p.Name == conf.WINDOWSEXE:
                processes.append(p)

        logging.debug("ufo process : " + str(processes))
        if len(processes) > 1:
            logging.debug(str([ x.Name for x in processes if x.ProcessId != os.getpid() ]))
            self.error_already_running("\n".join([ x.Name for x in processes if x.ProcessId != os.getpid() ]).strip())
            sys.exit(0)

        logging.debug("Checking VBoxXPCOMIPCD process")
        processes = self.WMI.Win32_Process(Name="VBoxSVC.exe")
        if len(processes)>1 :
            logging.debug("VBoxXPCOMIPCD is still running. Exiting")
            self.error_already_running("\n".join([ x.Name for x in processes ]), "VirtualBox")
            sys.exit(0)

    def prepare_self_copy(self):
        self_copied_path = tempfile.mkdtemp(prefix="ufo-self-copied")
        patterns = [ "*.exe", "*.dll", "library.zip", "Qt*.dll", "msv*.dll", "*.pyd", "py*.dll", "Microsoft.VC*.CRT"]
        logging.debug("Copying launcher to " + self_copied_path)
        files = []
        for pattern in patterns:
            files += glob.glob(path.join(conf.SCRIPT_DIR, pattern))

        os.mkdir(os.path.join(self_copied_path, "Windows"))
        os.mkdir(os.path.join(self_copied_path, "Windows", "bin"))
        os.mkdir(os.path.join(self_copied_path, ".data"))
        for file in files:
            dest = os.path.join(self_copied_path, "Windows", "bin", os.path.basename(file))
            # logging.debug("Copying " + str(file) + " to " + str(dest))
            if os.path.isdir(file):
                copytree(file, dest)
            else:
                copyfile(file, dest)

        key_root = os.path.dirname(os.path.dirname(conf.SCRIPT_DIR))
        copytree(path.join(key_root, ".data" , "images"), path.join(self_copied_path, ".data", "images"))
        copytree(path.join(key_root, ".data", "locale"), path.join(self_copied_path, ".data", "locale"))

        return path.join(self_copied_path, "Windows", "bin", os.path.basename(conf.SCRIPT_PATH))

    def prepare_update(self):
        return self.prepare_self_copy()

    def call(self, cmd, env = None, shell = True, cwd = None, output=False):
        return OSBackend.call(self, cmd, env, shell, cwd, output)

    def get_service_state(self, service):
        logging.debug("Checking if service " + service + " exists")
        retcode, output = self.call([ "sc", "query", service ], shell=True, output=True)
        if retcode == 0 and not ("FAILED" in output):
            logging.debug("Service " + service + " exists")
            lines = output.split("\n")
            for line in lines:
                splt = line.split()
                if "STATE" in splt:
                    logging.debug("Service " + service + ": state " + splt[-1])
                    return splt[-1]
            logging.debug("Service " + service + ": unknown state")
            return "FAILED"
        else:
            logging.debug("Service " + service + " does not exists")
            return "FAILED"

    def create_service(self, service, path):
        logging.debug("Creating service " + service)
        ret, output = self.call([ "sc", "create", service, "binpath=", path, "type=", "kernel",
                                  "start=", "demand", "error=", "normal", "displayname=", service ], 
                                shell=True, output=True)
        return ret

    def start_service(self, service):
        logging.debug("Starting service " + service)
        ret, output = self.call([ "sc", "start", service ], shell=True, output=True)
        return ret
        
    def stop_service(self, service):
        logging.debug("Stopping service " + service)
        ret, output = self.call([ "sc", "stop", service ], shell=True, output=True)
        return ret
        
    def register_vbox_com(self, vbox_path):
        if self.call([ path.join(vbox_path, "VBoxSVC.exe"), "/reregserver" ], cwd = vbox_path, shell=True):
            return False

        self.call([ "regsvr32.exe", "/S", path.join(vbox_path, "VBoxC.dll") ], cwd = vbox_path, shell=True)
        self.call([ "rundll32.exe", "/S", path.join(vbox_path, "VBoxRT.dll"), "RTR3Init" ], cwd = vbox_path, shell=True)
        return True
        
    def start_services(self):
        start_service = True
        
        # Is vbox installed ?
        vboxdrv_state = self.get_service_state("VBoxDrv")
        if vboxdrv_state == "RUNNING":
            # try to unload VboxDrv
            self.stop_service("VBoxDrv")
            
            # is service is really stopped ?
            vboxdrv_state = self.get_service_state("VBoxDrv")
            if vboxdrv_state != "STOPPED" or not os.environ.get("VBOX_INSTALL_PATH"):
                return 2
                
            self.vbox_install = os.environ.get("VBOX_INSTALL_PATH")

        elif vboxdrv_state == "STOP_PENDING":
            return 2

        if conf.CREATESRVS:
            create_service = True
            portable_vboxdrv_state = self.get_service_state("PortableVBoxDrv")
            if portable_vboxdrv_state == "STOPPED":
                logging.debug("Removing PortableVBoxDrv")
                self.call([ "sc", "delete", "PortableVBoxDrv" ], shell=True)
                
            elif portable_vboxdrv_state == "RUNNING":
                logging.debug("Service PortableVBoxDrv is running")
                create_service = False
                start_service = False

            if create_service:
                logging.debug("Creating services :")
                if self.create_service("PortableVBoxDrv",
                                       path.join(conf.VBOXDRIVERS, "VBoxDrv.sys")) != 0:
                    # We dont have root permissons
                    return 1

            if self.puel:
                self.create_service("PortableVBoxUSBMon",
                                    path.join(conf.BIN, "drivers", "USB", "filter", "VBoxUSBMon.sys"))

                try:
                    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                          "SYSTEM\\CurrentControlSet\\Services\\VBoxUSB")
                    if _winreg.QueryValue(key, "DisplayName") != "VirtualBox USB":
                        self.create_service("VBoxUSB",
                                            path.join(conf.BIN, "drivers", "USB", "device", "VBoxUSB.sys"))

                except:
                    logging.debug("The key HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\VBoxUSB does not exist")
    
        if conf.STARTSRVS and start_service:
            logging.debug("Starting services :")
            start_portable_vboxdrv = self.start_service("PortableVBoxDRV")
            if start_portable_vboxdrv in [ 1060, 5]:
                logging.debug("Got error: " + str(code) + " " + output)
                return 1
            elif start_portable_vboxdrv == 183:
                logging.debug("VirtualBox seems to be installed but not catched (sc start service returns 183)")
                return 2

            if self.puel:
                self.start_service("PortableVBoxUSBMon")

        logging.debug("Re-registering server:")
        if not self.register_vbox_com(conf.BIN):
            return 1

        return 0

    def stop_services(self):
        if conf.STARTSRVS:
            # self.call([ "sc", "stop", "PortableVBoxDRV" ], shell=True)
            if self.puel:
                self.call([ "sc", "stop", "PortableVBoxUSBMon" ], shell=True)
            self.call([ path.join(conf.BIN, "VBoxSVC.exe"), "/unregserver" ], shell=True)
            self.call([ "regsvr32.exe", "/S", "/U", path.join(conf.BIN, "VBoxC.dll") ], shell=True)

        if conf.CREATESRVS:
            # Do not delete service because some Windows reports "service mark as deleted"
            # self.call([ "sc", "delete", "PortableVBoxDRV" ], shell=True)
            if self.puel:
                self.call([ "sc", "delete", "PortableVBoxUSBMon" ], shell=True)

        if self.puel:
            try:
                key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\VBoxUSB")
                if _winreg.QueryValue(key, "DisplayName") != "VirtualBox USB":
                    self.call([ "sc", "stop", "VBoxUSB" ], shell=True)
                    self.call([ "sc", "delete", "VBoxUSB" ], shell=True)
            except:
                logging.debug("The key HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\VBoxUSB does not exist")

        if self.vbox_install:
            # We assume that if VBoxDrv can be stopped and restart, so PortableVboxDrv too
            self.stop_service("PortableVBoxDrv")
            self.start_service("VBoxDrv")
            self.register_vbox_com(self.vbox_install)

    def kill_resilient_vbox(self):
        self.call([ 'taskkill', '/F', '/IM', 'VBoxSVC.exe' ], shell=True) 

    def get_device_parts(self, device_name):
        disks = self.WMI.Win32_DiskDrive(Name = device_name)
        if not disks:
            return {}

        partitions = disks[0].associators(wmi_association_class="Win32_DiskDriveToDiskPartition")
        if not partitions:
            return {}

        device_parts = {}
        for part in partitions:
            part_info = [ device_name, part.NumberOfBlocks ]
            device_parts.update({ (int(part.Index) + 1) : part_info })
        return device_parts

    def find_device_by_uuid(self, path):
        return ""

    def find_device_by_volume(self, dev_volume):
        logical_disks = self.WMI.Win32_LogicalDisk (VolumeName = dev_volume)
        if not logical_disks:
            return ""
        
        partitions = logical_disks[0].associators(wmi_association_class="Win32_LogicalDiskToPartition")
        if not partitions:
            return ""
        
        disks = partitions[0].associators(wmi_result_class="Win32_DiskDrive")
        if len(disks) > 0:
            return disks[0].Name
        return ""

    def find_device_by_model(self, model):
        disks = self.WMI.Win32_DiskDrive(Model = model)
    
        # Probably manage multiple UFO key choice...
        if len(disks) > 0:
            return disks[0].Name
        return ""

    def get_disk_from_partition(self, part):
        partitions = part.associators(wmi_association_class="Win32_LogicalDiskToPartition")
        if not partitions:
            return ""

        disks = partitions[0].associators(wmi_result_class="Win32_DiskDrive")
        if len(disks) > 0:
            return disks[0].Name

    def prepare_device(self, dev):
        pass

    def get_device_size(self, name, partition = 0):
        assert partition == 0

        import win32file
        import win32con
        import winioctlcon
        import win32api
        import struct

        hFile = win32file.CreateFile(name, win32con.GENERIC_READ, 0, None, win32con.OPEN_EXISTING, 0, None)
        buffer = " " * 1024
        data = win32file.DeviceIoControl(hFile, winioctlcon.IOCTL_DISK_GET_DRIVE_GEOMETRY, buffer, 1024)
        tup = struct.unpack("qiiii", data)
        if tup[1] in (winioctlcon.FixedMedia, winioctlcon.RemovableMedia):
            size = reduce(int.__mul__, tup[:1] + tup[2:])
            logging.debug("Found FixedMedia or RemovableMedia of size " + str(size))
        data = win32file.DeviceIoControl(hFile, winioctlcon.IOCTL_DISK_GET_LENGTH_INFO, buffer, 1024)
        win32api.CloseHandle(hFile)
        if data:
            tup = struct.unpack("q", data)
            size = tup[0]
            logging.debug("Found regular device of size " + str(size))
        return size >> 9

    def get_disk_geometry(self, device):
        import win32file
        import win32con
        import winioctlcon
        import win32api
        import struct

        hFile = win32file.CreateFile(device, win32con.GENERIC_READ, 0, None, win32con.OPEN_EXISTING, 0, None)
        buffer = " " * 1024
        data = win32file.DeviceIoControl(hFile, winioctlcon.IOCTL_DISK_GET_DRIVE_GEOMETRY, buffer, 1024)
        win32api.CloseHandle(hFile)
        tup = struct.unpack("qiiii", data)
        if tup[1] in (winioctlcon.FixedMedia, winioctlcon.RemovableMedia):
            size = reduce(int.__mul__, tup[:1] + tup[2:])
            logging.debug("Found FixedMedia or RemovableMedia of size " + str(size))
        Cylinders, MediaType, TracksPerCylinder, SectorsPerTrack, BytesPerSector = struct.unpack("qiiii", data)
        return Cylinders, TracksPerCylinder, SectorsPerTrack

    def list_devices(self):
        for disk in self.WMI.Win32_DiskDrive():
            print disk.Model

    def find_network_device(self):
        if conf.NETTYPE == conf.NET_HOST:
            if conf.HOSTNET != "":
                return conf.NET_HOST, conf.HOSTNET
        
            net = self.WMI.Win32_networkadapter(NetConnectionStatus = 2)
    
            for adapter in net:
                try: logging.debug("Found net adapter " + adapter.Name)
                except: pass
                if '1394' in adapter.Name:
                    continue
                # Probably except VMware connection for example...
                return conf.NET_HOST, adapter.Name

        return conf.NET_NAT, ""

    def get_dvd_device(self):
        cds = self.WMI.Win32_CDROMDrive()
        drive, burner = None, False
        for cd in cds:
            if not burner: # Already found one, should use the faster one...
                drive, burner = cd.Id, 4 in cd.Capabilities
        return drive
    
    def find_resolution(self):
        if gui.backend == "PyQt":
            return str(gui.screenRect.width()) + "x" + str(gui.screenRect.height())
        
        display = self.WMI.Win32_DisplayControllerConfiguration()
    
        if len(display) > 0:
            return str(display[0].HorizontalResolution) + "x" + str(display[0].VerticalResolution)
        return ""

    def get_free_ram (self):
        try:
            ram = self.WMI.Win32_PerfFormattedData_PerfOS_Memory()
            if len(ram) > 0:
                return max((int(ram[0].AvailableBytes) + int(ram[0].CacheBytes)) / (1<<20), 384)
        except:
            logging.debug("Failed creating WMI object Win32_PerfFormattedData_PerfOS_Memory")
            ram = self.WMI.Win32_ComputerSystem()
            if len(ram) > 0:
                return max(int(ram[0].TotalPhysicalMemory) / 1024 / 1024 / 2, 384)
        return 0

    def get_free_space(self, path):
        import win32api
        available, x, x = win32api.GetDiskFreeSpaceEx(path)
        return available

    def get_host_shares(self):
        import _winreg
        shares = []
        wanted = { 'Desktop'  : _("My Windows desktop"),
                   'Personal' : _("My Windows documents") }

        key_string = "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        try:
            hive = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
            key  = _winreg.OpenKey(hive, key_string)
            for i in range(0, _winreg.QueryInfoKey(key)[1]):
                name, value, type = _winreg.EnumValue(key, i)
                if name in wanted:
                    shares.append({ 'sharename' : "windows" + name.lower() + "hosthome",
                                    'sharepath' : value,
                                    'displayed' : wanted[name] })
            _winreg.CloseKey(key)
            _winreg.CloseKey(hive)

        except WindowsError:
            shares.append({ 'sharename' : "windowshosthome",
                            'sharepath' : path.expanduser('~'),
                            'displayed' : "Mes documents Windows" })

        return shares
    
    def get_usb_devices(self):
        logical_disks = self.WMI.Win32_LogicalDisk (DriveType = 2)
        return [[logical_disk.Caption + '\\',
                  str(logical_disk.Caption) + str("_") + str(logical_disk.VolumeName),
                  self.get_disk_from_partition(logical_disk) ] for logical_disk in logical_disks ]

    def get_usb_sticks(self):
        disks = self.WMI.Win32_DiskDrive()
        return [[ disk.Name, disk.Model ] for disk in disks if disk.InterfaceType == "USB" ]

    def open(self, path, mode='r'):
        import win32file
        import win32con
        import winioctlcon
        import win32api
        class WindowsFile:
            def __init__(self, path, mode=0, access=win32con.GENERIC_ALL):
                self.name = path
                if path.startswith("\\\\"):
                    self.handle = win32file.CreateFile(path, access, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_RANDOM_ACCESS, None)
                else:
                    self.handle = win32file.CreateFile(path, win32con.GENERIC_READ, 0, None, win32con.OPEN_EXISTING, 0, None)

            def __del__(self):
                self.close()

            def close(self):
                if self.handle:
                    win32api.CloseHandle(self.handle)
                    self.handle = None

            def read(self, size):
                if size < 512: size = 512
                return win32file.ReadFile(self.handle, size)[1]

            def write(self, data):
                size = len(data)
                if size < 512: data += "\0" * (512 - size)
                print self.handle, len(data), data[:16]
                win32file.WriteFile(self.handle, data)

            def seek(self, offset, position):
                win32file.SetFilePointer(self.handle, offset, position)

        file = WindowsFile(path, mode)
        return file

    def rights_error(self):
        msg = _("You don't have enough permissions to run %s.") % (conf.PRODUCTNAME,)
        logging.debug("Using Windows version " + str(platform.win32_ver()))
        if platform.win32_ver()[0].lower() == "vista":
            msg += _("Run %s as Administrator by right clicking on %s and select : 'Run as administrator'") % (conf.PRODUCTNAME, path.splitext(conf.WINDOWSEXE)[0])
        else:
            msg += _("Run %s as Administrator by right clicking on %s and select : 'Run as ...'") % (conf.PRODUCTNAME, path.splitext(conf.WINDOWSEXE)[0])
        gui.dialog_info(title=_("Not enough permissions"), msg=msg)
        sys.exit(1)

    def installed_vbox_error(self):
        msg = _("We have detected an existing VirtualBox installation on this computer.\n"
                "%s is not compatible with this version of VirtualBox, please remove this VirtualBox installation to run %s.\n\n"
                "Note that if you want to use your own VirtualBox installation, you need to reboot your computer.") % (conf.PRODUCTNAME, conf.PRODUCTNAME)
        gui.dialog_info(title=_("VirtualBox detected"), msg=msg)
        sys.exit(1)

    def execv(self, cmd, root=False):
        logging.shutdown()
        os.execv(cmd[0], cmd)

    def is_admin(self):
        # We assume that we are admin as the exe manifest requires
        return True;

    def umount_device(self, mntpoint):
        import win32file
        import win32api
        import winioctlcon
        import win32con
        try:
            hVolume = win32file.CreateFile("\\\\.\\%s:" % (mntpoint[0]),
                                           win32con.GENERIC_READ, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                                           None, win32con.OPEN_EXISTING, 0, None)
            win32file.DeviceIoControl(hVolume, winioctlcon.FSCTL_LOCK_VOLUME, None, 0)
            win32file.DeviceIoControl(hVolume, winioctlcon.FSCTL_DISMOUNT_VOLUME, None, 0)
            self.hVolume = hVolume
            # win32api.CloseHandle(hVolume)
            return True
        except:
            return False

    def prepare(self):
        # Adjusting paths
        if not conf.HOME: 
            conf.HOME = path.join(conf.APP_PATH, ".VirtualBox")

        services_state = self.start_services()
        if services_state == 2:
            logging.debug("Cannot stop the installed VirtualBox")
            self.installed_vbox_error()
        elif services_state == 1:
            logging.debug("Insufficient rights")
            self.rights_error()

    def cleanup(self):
        self.stop_services()
        if self.eject_at_exit:
            self.eject_key()

    def eject_key(self):
        self.call([ path.join(conf.BIN, "USB_Disk_Eject.exe"), "/REMOVETHIS" ], shell=True)

    def run_vbox(self, command, env):
        self.call(command, env = env, shell=True)

    def wait_for_events(self, interval):
        # Overloaded on Windows because of a VERY STRANGE bug
        # After the first call to VBox's waitForEvents, the
        # characters typed into the balloon windows are uppercase...
        time.sleep(interval)
        gui.app.process_gui_events()

    def onExtraDataCanChange(self, key, value):
        # win32com need 3 return values (2 out parameters and return value)
        return "", True, 0

