# -*- coding: utf-8 -*-

import _winreg
import win32gui, win32con, win32api
import os, os.path as path
import wmi
import sys
import logging
import conf
import tempfile
import time
import platform
from utils import *
from shutil import copyfile, copytree

class WindowsBackend(Backend):
    VBOXMANAGE_EXECUTABLE = "VBoxManage.exe"
    VIRTUALBOX_EXECUTABLE = "VirtualBox.exe"

    HOST_AUDIO_DRIVER = "DirectSound"

    RELATIVE_VMDK_POLICY = False
    systemdir = win32api.GetSystemDirectory ()

    def __init__(self):
        Backend.__init__(self)
        self.create_splash_screen()
        gui.set_icon(path.join(conf.SCRIPT_DIR, "..", "UFO.ico"))
        self.WMI = wmi.WMI()

    def check_process(self):
        logging.debug("Checking UFO process")
        # TODO: Get pid for possible kill
        processes = self.WMI.Win32_Process(name="ufo.exe")
        logging.debug("ufo process : "+str(processes))
        if len(processes)>1 :
            logging.debug("U.F.O launched twice. Exiting")
            logging.debug(str([ x.Name for x in processes if x.ProcessId != os.getpid() ]))
            gui.dialog_error_report(title=u"Impossible de lancer UFO",
                                    msg=u"UFO semble déjà en cours d'utilisation.\n" + \
                                        u"Veuillez fermer toutes les fenêtres UFO, et relancer le programme.\n" + \
                                        "Processus :\n" + "\n".join([ x.Name for x in processes if x.ProcessId != os.getpid() ]).strip())
            sys.exit(0)

        logging.debug("Checking VBoxXPCOMIPCD process")
        processes = self.WMI.Win32_Process(name="VBoxSVC.exe")
        if len(processes)>1 :
            logging.debug("VBoxXPCOMIPCD is still running. Exiting")
            gui.dialog_info(title=u"Impossible de lancer UFO",
                             error=True,
                             msg=u"VirtualBox semble déjà en cours d'utilisation. \n" \
                                 u"Veuillez fermer toutes les fenêtres de VirtualBox, et relancer le programme.")
            sys.exit(0)

    def prepare_update(self):
        updater_path = tempfile.mkdtemp(prefix="ufo-updater")
        logging.debug("Copying " + conf.SCRIPT_PATH + " to " + updater_path)
        exe_path = path.join(updater_path, "ufo.exe")
        shutil.copyfile(conf.SCRIPT_PATH, exe_path)
        return exe_path

    def call(self, cmd, env = None, shell = True, cwd = None, output=False):
        return Backend.call(self, cmd, env, shell, cwd, output)

    def start_services(self):
        start_service = True
        if conf.CREATESRVS:
            logging.debug("Creating services :")

            """
            services = self.WMI.Win32_Service(name="PortableVBoxDrv")
            logging.debug("WMI services: " + str(services))
            if services:
                logging.debug("Service PortableVBoxDrv exists")
                if services[0].State == "Running":
                    logging.debug("Service PortableVBoxDrv is running")
                else:
                    logging.debug("Removing PortableVBoxDrv")
                    elf.call([ "sc", "delete", "PortableVBoxDrv" ], shell=True)

            if self.call([ "sc", "create", "PortableVBoxDrv",
                      "binpath=", path.join(conf.BIN, "drivers", "VBoxDrv", "VBoxDrv.sys"),
                      "type=", "kernel", "start=", "demand", "error=", "normal", 
                      "displayname=", "PortableVBoxDrv" ], shell=True) == 5:
                return 1
            """
        
            logging.debug("Checking if service PortableVBoxDrv exists")
            retcode, output = self.call([ "sc", "query", "PortableVBoxDrv" ], shell=True, output=True)
            create_service = True
            if retcode == 0 and not ("FAILED" in output):
                logging.debug("Service PortableVBoxDrv exists")
                lines = output.split("\n")
                for line in lines:
                    splt = line.split()
                    if "STATE" in splt:
                        logging.debug("State " + splt[-1])
                        if splt[-1] == "STOPPED":
                            logging.debug("Removing PortableVBoxDrv")
                            self.call([ "sc", "delete", "PortableVBoxDrv" ], shell=True)
                        elif splt[-1] == "RUNNING":
                            logging.debug("Service PortableVBoxDrv is running")
                            create_service = False
                            start_service = False

            if create_service:
                ret, output = self.call([ "sc", "create", "PortableVBoxDrv",
                                           "binpath=", path.join(conf.BIN, "drivers", "VBoxDrv", "VBoxDrv.sys"),
                                           "type=", "kernel", "start=", "demand", "error=", "normal", 
                                           "displayname=", "PortableVBoxDrv" ], shell=True, output=True)
                if ret == 5 or "FAILED" in output:
                    return 1

            if self.puel:
                self.call([ "sc", "create", "PortableVBoxUSBMon", "binpath=", 
                             path.join(conf.BIN, "drivers", "USB", "filter", "VBoxUSBMon.sys"),
                             "type=", "kernel", "start=", "demand", "error=", "normal", 
                             "displayname=", "PortableVBoxUSBMon" ], shell=True)
                         
                try:
                    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 
                                          "SYSTEM\\CurrentControlSet\\Services\\VBoxUSB")
                    if _winreg.QueryValue(key, "DisplayName") != "VirtualBox USB":
                        self.call(["sc", "create", "VBoxUSB", "binpath=", 
                                   path.join(conf.BIN, "drivers", "USB", "device", "VBoxUSB.sys"),
                                   "type=", "kernel", "start=", "demand", "error=", "normal", 
                                   "displayname=", "PortableVBoxUSB" ], shell=True)
                except:
                    logging.debug("The key HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\VBoxUSB does not exist")
    
        if conf.STARTSRVS and start_service:
            logging.debug("Starting services :")
        
            code, output = self.call([ "sc", "start", "PortableVBoxDRV" ], shell=True, output=True)
            if code in [ 1060, 5 ] or "FAILED" in output:
                logging.debug("Got error: " + str(code) + " " + output)
                return 1

            if self.puel:
                self.call([ "sc", "start", "PortableVBoxUSBMon" ], shell=True)

        logging.debug("Re-registering server:")

        if self.call([ path.join(conf.BIN, "VBoxSVC.exe"), "/reregserver" ], cwd = conf.BIN, shell=True):
            return 1
        
        self.call([ "regsvr32.exe", "/S", path.join(conf.BIN, "VBoxC.dll") ], cwd = conf.BIN, shell=True)
        self.call([ "rundll32.exe", "/S", path.join(conf.BIN, "VBoxRT.dll"), "RTR3Init" ], cwd = conf.BIN, shell=True)
    
        return 0

    def kill_resilient_vbox(self):
        self.call([ 'taskkill', '/F', '/IM', 'VBoxSVC.exe' ], shell=True) 

    """
    def process_wait_close(self, process):
        processes = self.WMI.Win32_Process(name=process)
        while processes:
            time.sleep(2)
            processes = self.WMI.Win32_Process(name=process)
            self.check_usb_devices()

    def wait_for_termination(self):
        self.process_wait_close("VBoxSDL.exe")
        self.process_wait_close("VirtualBox.exe")
        self.process_wait_close("VBoxManage.exe")
        self.process_wait_close("VBoxSVC.exe")
    """

    def stop_services(self):
        if conf.STARTSRVS:
            # self.call([ "sc", "stop", "PortableVBoxDRV" ], shell=True)
            if self.puel:
                self.call([ "sc", "stop", "PortableVBoxUSBMon" ], shell=True)
            self.call([ path.join(conf.BIN, "VBoxSVC.exe"), "/unregserver" ], shell=True)
            self.call([ "regsvr32.exe", "/S", "/U", path.join(conf.BIN, "VBoxC.dll") ], shell=True)

        if conf.CREATESRVS:
            pass
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

    def find_device_by_uuid(self, dev_uuid):
        return ""

    def get_device_parts(self, device_name):
        disks = self.WMI.Win32_DiskDrive(Name = device_name)
        if not disks:
            return {}
        
        partitions = disks[0].associators(wmi_association_class="Win32_LogicalDiskToPartition")
        if not partitions:
            return {}

        device_parts = {}
        for part in partitions:
            part_info = [ device_name, part.NumberOfBlocks ]
            device_parts.update({ part.Index : part_info })
        return device_parts

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
              
    def prepare_device(self, dev):
        pass

    def get_device_size(self, name, partition = 0):
        assert partition == 0

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

    def list_devices(self):
        for disk in self.WMI.Win32_DiskDrive():
            print disk.Model

    def find_network_device(self):
        if conf.NETTYPE == conf.NET_HOST and \
           not conf.VBOX_INSTALLED and \
           not path.exists(path.join(self.systemdir, "VBoxNetFltNotify.dll")):
            logging.debug("Installing VirtualBox driver")
            protocolpath = path.join(conf.BIN, "drivers", "network", "netflt")
            snetcfg = path.join(conf.BIN, "snetcfg_x86.exe")
            self.call([snetcfg, "-v", "-u", "sun_VBoxNetFlt"], shell=True)
            self.call([snetcfg, "-v", "-l", "drivers\\network\\netflt\\VBoxNetFlt.inf",
                   "-m", "drivers\\network\\netflt\\VBoxNetFlt_m.inf",
                   "-c", "s", "-i", "sun_VBoxNetFlt"], shell=True, cwd=conf.BIN)
            shutil.copy(path.join(protocolpath, "VBoxNetFltNotify.dll"), self.systemdir)
            shutil.copy(path.join(protocolpath, "VBoxNetFlt.sys"), path.join(self.systemdir, "drivers"))
            self.call(["regsvr32.exe", "/S", path.join(self.systemdir, "VBoxNetFltNotify.dll")], shell=True)

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

    def get_host_home(self):
        return path.expanduser('~'), "Mes documents Windows"
    
    def get_usb_devices(self):
        logical_disks = self.WMI.Win32_LogicalDisk (DriveType = 2)
        return [[logical_disk.Caption + '\\',
                  str(logical_disk.Caption) + str("_") + str(logical_disk.VolumeName)] for logical_disk in logical_disks ]

    def get_usb_sticks(self):
        disks = self.WMI.Win32_DiskDrive()
        return [[ disk.Name, disk.Model ] for disk in disks if disk.InterfaceType == "USB" ]

    def rights_error(self):
        msg = u"Vous ne possédez pas les permissions nécessaires pour lancer UFO."
        logging.debug("Using Windows version " + str(platform.win32_ver()))
        if platform.win32_ver()[0].lower() == "vista":
            msg += u"\n\nExécutez UFO en tant qu'administrateur en sélectionnant :\nClic droit -> Exécuter en tant qu'administrateur"
        else:
            msg += u"\n\nExécutez UFO en tant qu'administrateur en sélectionnant :\nClic droit -> Exécuter en tant qu'administrateur"
        gui.dialog_info(title=u"Permissions insuffisantes", msg=msg)
        sys.exit(1)

    def prepare(self):
        # Ajusting paths
        if not conf.HOME: conf.HOME = path.join(conf.APP_PATH, ".VirtualBox")
        images = glob.glob(path.join(conf.HOME, "ufo-*.png"))
        try:
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\VBoxUSB")
            conf.VBOX_INSTALLED = True
        except:
            conf.VBOX_INSTALLED = False

        if self.start_services():
            logging.debug("Insufficient rights")
            self.rights_error()

    def cleanup(self):
        self.stop_services()
        if conf.NETTYPE == conf.NET_HOST and not conf.VBOX_INSTALLED and conf.UNINSTALLDRIVERS:
            self.call(["regsvr32.exe", "/S", "/U", path.join(self.systemdir, "VBoxNetFltNotify.dll")])
            self.call([path.join(conf.BIN, "snetcfg_x86.exe"), "-v", "-u", "sun_VBoxNetFlt"])
            # self.call(["sc", "delete", "VBoxNetFlt" ])
            # os.unlink(path.join(self.systemdir, "VBoxNetFltNotify.dll"))
            # os.unlink(path.join(self.systemdir, "drivers", "VBoxNetFlt.sys"))

    def run_vbox(self, command, env):
        self.call(command, env = env, shell=True)
        
    def get_free_size(self, path):
        logical_disks = self.WMI.Win32_LogicalDisk (Caption = path[0:2])
        if not logical_disks:
            return ""

        return int(logical_disks[0].FreeSpace) / 1000000

