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


import os, sys, statvfs
import os.path as path
import conf
import logging
import platform
import gui
import glob
import tempfile
import utils
import re

from osbackend import OSBackend
from shutil import copytree

class LinuxBackend(OSBackend):

    VBOXMANAGE_EXECUTABLE = "VBoxManage"
    VIRTUALBOX_EXECUTABLE = "VirtualBox"
    RELATIVE_VMDK_POLICY  = True

    def __init__(self, dist, version, codename):
        OSBackend.__init__(self)
        self.dist     = dist
        self.version  = version
        self.codename = codename
        self.run_as_root = self.create_run_as_root()

    def get_default_audio_driver(self):
        return self.vbox.constants.AudioDriverType_Pulse

    def check_process(self):
        logging.debug("Checking UFO process")
        # We used to use a pipe, but Satan knows why, it returns a shadow
        # of the running program. So we run two separate commands
        psout = self.call(["ps", "ax", "-o", "pid,command"], output = True)[1]
        processes = [ x[0].strip() for x in re.findall(r"(.*/[Uu][Ff][Oo](\n| .*))", psout) ]
        logging.debug("ufo process : " + str(processes))
        if len(processes) > 1 :
            pids = [i.strip().split(" ")[0] for i in processes]
            i = len(pids) - 1
            while i >= 0:
                if self.call(["ps", "-p", pids[i], "-o", "ppid"], output=True)[1].strip().split("\n")[-1].strip() in pids:
                    del pids[i]
                i -= 1
            if len(pids) > 1: 
                logging.debug("U.F.O launched twice. Exiting")
                self.error_already_running('\n'.join(processes))
                sys.exit(0)

        logging.debug("Checking VBoxXPCOMIPCD process")
        processes = self.call([["ps", "ax", "-o", "pid,command"],
                               ["grep", "VBoxXPCOMIPCD"],
                               ["grep", "-v", "grep"]], output = True)[1]
        if processes and not os.environ.has_key("NOVBOXCHECK"):
            logging.debug("VBoxXPCOMIPCD is still running. Exiting")
            if self.error_already_running(processes, "VirtualBox"):
                self.kill_resilient_vbox()
            else:
                sys.exit(0)
    
    def prepare_update(self):
        return conf.SCRIPT_PATH
    
    def prepare(self):
        if os.getuid() != 0:
            self.run_as_root.call([sys.executable] + sys.argv + [ "--respawn" ], replace=True)

        self.call(["rmmod", "kvm-intel"])
        self.call(["rmmod", "kvm-amd"])
        self.call(["rmmod", "kvm"])
                                             
    def cleanup(self):
        pass

    def kill_resilient_vbox(self):
        self.call(["killall", "-9", "VBoxXPCOMIPCD"])
        self.call(["killall", "-9", "VBoxSVC"])

    def run_vbox(self, command, env):
        # For some reason, it doesn't work with 'call'
        cmd = "VBOX_USER_HOME=" + env["VBOX_USER_HOME"] + " VBOX_PROGRAM_PATH=" + \
              env["VBOX_PROGRAM_PATH"] + " " + command
        os.system(cmd)
        
    def get_uuid(self, dev):
        return self.call(["blkid", "-o", "value", "-s", "UUID", dev], output=True)[1].strip()

    def find_device_by_uuid(self, dev_uuid):
        for device in glob.glob("/dev/sd*[0-9]"):
            uuid = self.get_uuid(device)
            if uuid == dev_uuid:
                if device[-1] >= "0" and device[-1] <= "9":
                    device = device[:-1]
                return device
        return ""
    
    def find_device_by_volume(self, dev_volume):
        if path.exists('/dev/disk/by-label/' + dev_volume):
            device = path.realpath('/dev/disk/by-label/' + dev_volume)
            if device[-1] >= "0" and device[-1] <= "9":
                device = device[:-1]
            return device
        return ""

    def find_device_by_model(self, dev_model):
        return ""
        
    def find_device_by_path(self, path):
        mounts = open('/proc/mounts', 'r').readlines()
        for mount in reversed(mounts):
            splitted = mount.split(" ")
            l = len(splitted)
            if l > 6:
                splitted = splitted[:1] + " ".join(splitted[1:l - 5 + 1]) + splitted[-4:]
            dev, mountpoint, type, options, opt1, opt2 = splitted
            if path.startswith(mountpoint):
                return dev[:-1]
        return ""

    def prepare_device(self, disk):
        self.call(["umount", disk + "3"])
        self.call(["umount", disk + "4"])
    
    def get_device_parts(self, dev):
        parts = glob.glob(dev + '[0-9]')
        device_parts = {}
        for part in parts:
            part_number = int(part[len(part)-1:])
            part_info = [part, self.get_device_size(dev, part_number)]
            device_parts.update({part_number: part_info})
        return device_parts

    def get_device_size(self, dev, partition=0):
        if partition > 0:
            return int(open(path.join("/", "sys", "block", path.basename(dev), path.basename(dev) + str(partition), "size")).read())
        else:
            return int(open(path.join("/", "sys", "block", path.basename(dev), "size")).read())

    def find_network_device(self):
        if conf.NETTYPE == conf.NET_HOST and conf.HOSTNET != "":
            return conf.NET_HOST, conf.HOSTNET   

        return conf.NET_NAT, ""

    def get_free_ram(self):
        mem_info = open("/proc/meminfo").read()
        free = int(grep(mem_info, "MemFree:").split()[1])
        cached = int(grep(mem_info, "Cached:").split()[1])
        return max((free + cached) / 1024, 384)

    def get_dvd_device(self):
        if path.exists("/dev/cdrom"):
            return "/dev/cdrom"

    def set_password(self, password):
        os.setreuid(0, self.get_user_uid())
        OSBackend.set_password(self, password)
        os.setreuid(0, 0)

    def get_password(self):
        os.setreuid(0, self.get_user_uid())
        password = OSBackend.get_password(self)
        os.setreuid(0, 0)
        return password

    def get_user_uid(self):
        if os.environ.has_key("SUDO_UID"):
            uid = os.getenv("SUDO_UID")
        elif os.environ.has_key("USERHELPER_UID"):
            uid = os.getenv("USERHELPER_UID")
        else:
            uid = os.getuid()
        return int(uid)

    def get_host_home(self):
        if os.environ.has_key("SUDO_USER"):
            user = os.getenv("SUDO_USER", "")
        elif os.environ.has_key("USERHELPER_UID"):
            user = self.call([["getent", "passwd", os.getenv("USERHELPER_UID")], 
                               ["cut", "-f", "1", "-d", ":"]], output=True)[1].strip()
        else:
            user = os.getenv("USER")
        return path.expanduser("~" + user), "Mes documents Linux"

    def get_usb_devices(self):
        if os.path.exists('/dev/disk/by-id'):
            usb_devices = [os.path.realpath(os.path.join('/dev/disk/by-id', link)) \
                           for link in os.listdir('/dev/disk/by-id') if link[0:3] == "usb"]
            usb_paths = [mnt.split()[1] for mnt in open('/proc/mounts', 'r').readlines() \
                         if mnt.split()[0] in usb_devices]
            return [[path, os.path.basename(path)] for path in usb_paths]
        return [], []

    def get_usb_sticks(self):
        if os.path.exists('/dev/disk/by-id'):
            usb_devices = [os.path.realpath(os.path.join('/dev/disk/by-id', link)) \
                           for link in os.listdir('/dev/disk/by-id') \
                           if link[0:3] == "usb" and "-part" not in link ]
            return [[dev, open(path.join("/", "sys", "block", path.basename(dev), "device", "model")).read().strip()] \
                    for dev in usb_devices]
        return [], []

    def find_resolution(self):
        if gui.backend == "PyQt":
            return str(gui.screenRect.width()) + "x" + str(gui.screenRect.height())
        
        if path.exists("/usr/bin/xrandr"):
            return self.call([["/usr/bin/xrandr"], ["grep", "*"]], output=True)[1].split()[0]
        return ""
        
    def get_free_size(self, path):
        stats = os.statvfs(path)
        return (stats[statvfs.F_BSIZE] * stats[statvfs.F_BFREE]) / 1000000
        
    def onExtraDataCanChange(self, key, value):
        # xpcom only return the both out parameters
        return True, ""
        
    def checking_pyqt(self):
        raise Exception("Implemented in subclasses")

    def look_for_virtualbox(self):
        if platform.architecture()[0] == '64bit' and path.isdir('/usr/lib64/virtualbox'): 
            conf.BIN = '/usr/lib64/virtualbox'
        elif platform.architecture()[0] == '32bit' and path.isdir('/usr/lib/virtualbox'): 
            conf.BIN = '/usr/lib/virtualbox'
        else: 
            conf.BIN = path.dirname(self.call(["which", "VirtualBox"], output=True)[1].strip())
            
        OSBackend.update_env(self)
        OSBackend.look_for_virtualbox(self)

    def create_run_as_root(self):
        if os.path.exists("/usr/bin/gksudo"):
            return GkSudoRunAsRoot()
        elif os.path.exists("/usr/bin/kdesudo"):
            return KdeSudoRunAsRoot()
        elif os.path.exists("/usr/bin/beesu"):
            return BeesuRunAsRoot()
        else:
            if os.isatty(0):
                os.environ["SUDO_ASKPASS"] = path.join(conf.SCRIPT_DIR, "bin", "ask-password")
                version = None
                try:
                    version = utils.call(["sudo", "-V"], output=True)[1].split("\n")[0].split()[2]
                except:
                    pass
                if version >= "1.7.1":
                        return SudoRunAsRoot()
                return XtermRunAsRoot()
        raise "No 'run as root' command available"
        
    def get_generic_installation_messages(self, component):
        return { "title" : _("Please wait"),
                 "msg" : _('Installing %s (required by UFO)') % (component,),
                 "success_msg" : _("%s was successfully installed") % (component,),
                 "error_msg" : _("An error occurred while installing %s") % (component,) }

        
class FedoraLinuxBackend(LinuxBackend):
    
    AGORABOX_VBOX_REPO = "http://downloads.agorabox.org/virtualbox/yum/"
    
    def __init__(self, dist, version, codename):
        LinuxBackend.__init__(self, dist, version, codename)
        
    def create_run_as_root(self):
        version = float(self.version)
        if (self.dist == "Fedora" and version >= 10) or \
           (self.dist == "U.F.O" and version >= 1.0):
            if not os.path.exists("/usr/bin/beesu"):
                # if os.path.exists("/usr/bin/gpk-install-package-name"):
                #    print (["/usr/bin/gpk-install-package-name", "beesu"], msg)'
                #else:
                gui.wait_command(["/usr/bin/pkcon", "install", "beesu"], **self.get_generic_installation_messages("beesu"))
        return LinuxBackend.create_run_as_root(self)

    def checking_pyqt(self):
        logging.debug("Checking PyQt")
        if gui.backend != "PyQt":
            gui.wait_command(self.run_as_root.get_prefix() + [ "yum", "-y", "install", "PyQt4"],
                             **self.get_generic_installation_messages("Qt4 for Python"))
            reload(gui)
            if gui.backend != "PyQt":
                logging.debug("Could not enable PyQt")

    def look_for_virtualbox(self):
        logging.debug("Checking VirtualBox binaries")
        if not path.exists(path.join(conf.BIN, self.VIRTUALBOX_EXECUTABLE)):
            logging.debug("Installing Agorabox repository for VirtualBox")
            gui.wait_command(["yum", "-y", "install", "yum-priorities"],
                             **self.get_generic_installation_messages("yum-priorities"))
            gui.wait_command(["rpm", "-ivf", self.AGORABOX_VBOX_REPO + "agorabox-virtualbox-yum-repository-1.0.noarch.rpm"],
                             msg=_("Setting Yum Agorabox repository"))
            kernel = "kernel"
            if os.uname()[2].endswith("PAE"):
                kernel += "-PAE"
            logging.debug("Kernel is: " + kernel)
            
            logging.debug("Installing VirtualBox")
            gui.wait_command(["yum", "-y", "install", "VirtualBox-OSE", "VirtualBox-OSE-kmodsrc", kernel + "-devel", "gcc", "make", "lzma"],
                             msg=_("Installing VirtualBox Open Source edition. This can take a few minutes"))
            version = self.call(["rpm", "-q", "--queryformat", "%{VERSION}", "VirtualBox-OSE"], output=True)[1]
            kmod_name = "VirtualBox-OSE-kmod-" + str(version)
            
            logging.debug("Decompressing drivers source code from /usr/share/%s/%s.tar" % (kmod_name, kmod_name, ))
            tarfile = glob.glob("/usr/share/%s/%s.tar.*" % (kmod_name, kmod_name, ))[0]
            tarext  = os.path.splitext(tarfile)[1][1:]
            utils.call(["tar", "--use-compress-program", tarext, "-xf", "/usr/share/%s/%s.tar.%s" % (kmod_name, kmod_name, tarext, )],
                       cwd = tempfile.gettempdir())
            
            compdir = os.path.join(tempfile.gettempdir(), kmod_name, "vboxdrv")
            logging.debug("Compiling vboxdrv source code in %s" % (compdir, ))
            gui.wait_command(["make", "install", "-C", compdir], 
                             msg=_("Compiling VirtualBox drivers"))
            
            logging.debug("Loading vboxdrv module")
            self.call(["/etc/sysconfig/modules/VirtualBox-OSE.modules"])
            
        LinuxBackend.look_for_virtualbox(self)
        

class UbuntuLinuxBackend(LinuxBackend):
    def __init__(self, dist, version, codename):
        LinuxBackend.__init__(self, dist, version, codename)

    def checking_pyqt(self):
        logging.debug("Checking PyQt")
        if gui.backend != "PyQt":
            gui.wait_command(self.run_as_root.get_prefix() + ["apt-get", "-y", "install", "python-qt4"], 
                             **self.get_generic_installation_messages("Qt4 for Python"))
            reload(gui)
            if gui.backend != "PyQt":
                logging.debug("Could not enable PyQt")

    def look_for_virtualbox(self):
        logging.debug("Checking VirtualBox binaries")
        vbox_path = utils.call(["which", "VirtualBox"], output=True)[1].strip()
        if not os.path.lexists(vbox_path):
            open("/etc/apt/sources.list", "a").write("deb http://download.virtualbox.org/virtualbox/debian %s non-free\n" % (self.codename.lower(), ))
            os.system("wget -q http://download.virtualbox.org/virtualbox/debian/sun_vbox.asc -O- | apt-key add -")
            gui.wait_command(["apt-get", "update"],
                              msg="Votre système est en train d'être mis à jour")
            gui.wait_command(["apt-get", "-y", "install", "virtualbox-3.0"],
                             **self.get_generic_installation_messages("VirtualBox 3"))
            gui.wait_command(["/etc/init.d/vboxdrv", "setup"],
                             msg="Configuration en cours de \"VirtualBox 3\".")
         
        LinuxBackend.look_for_virtualbox(self)


class GenericLinuxBackend(LinuxBackend):
    def __init__(self, dist, version, codename):
        LinuxBackend.__init__(self, dist, version, codename)

    def checking_pyqt(self):
        pass


class RunAsRoot():
    def __init__(self):
        self.prefix = None
    
    def call(self, command, replace=False):
        raise Exception("Implemented in subclasses")

    def get_prefix(self):
        return self.prefix
    
    
class BeesuRunAsRoot(RunAsRoot):
    def __init__(self):
        logging.debug("Using Beesu command for run as root")
        RunAsRoot.__init__(self)
        self.prefix = ["/usr/bin/beesu", "-m" ]
    
    def call(self, command, replace=False):
        if os.environ.has_key("GNOME_KEYRING_SOCKET"):
            command = [ "GNOME_KEYRING_SOCKET=" + os.environ["GNOME_KEYRING_SOCKET"] ] + command
        if replace:
            os.execv("/usr/bin/beesu", self.prefix + command)
        else:
            utils.call(self.prefix + command)


class KdeSudoRunAsRoot(RunAsRoot):
    def __init__(self):
        logging.debug("Using KdeSudo command for run as root")
        RunAsRoot.__init__(self)
        self.prefix = ["/usr/bin/kdesudo", "--"]
    
    def call(self, command, replace=False):
        if replace: 
            os.execv("/usr/bin/kdesudo", self.prefix + command)
        else:
            utils.call( self.prefix + command, "Veuillez patientez lors de l\'installation des composants", interactive)


class GkSudoRunAsRoot(RunAsRoot):
    # TODO: make fully working
    def __init__(self):
        logging.debug("Using GkSudo command for run as root")
        RunAsRoot.__init__(self)
        self.prefix = ["/usr/bin/gksudo" , "--"]
    
    def call(self, command, replace=False):
        if replace: 
            os.execv("/usr/bin/gksudo", ["--"] + command)
        else:
            print 'utils.call(["/usr/bin/gksudo" , "--"] + command , "Veuillez patientez lors de l\'installation des composants", interactive)'


class SudoRunAsRoot(RunAsRoot):
    # TODO: make working
    def __init__(self):
        logging.debug("Using Sudo command for run as root")
        RunAsRoot.__init__(self)
        self.prefix = ["/usr/bin/sudo", "-A"]
    
    def call(self, command, replace=False):
        if replace: 
            print "os.execv.sudo"
        else:
            print 'utils.call("/usr/bin/sudo", ["sudo", "-A"] + command)'


class XtermRunAsRoot(RunAsRoot):
    # TODO: make working
    def __init__(self):
        logging.debug("Using Xterm command for run as root")
        RunAsRoot.__init__(self)
        self.prefix = ["xterm", "-e", "su", "-c"]
    
    def call(self, command, replace=False):
        # TODO: utils.call (bug in subprocess)
        if replace: 
            print "os.execv.xterm"
        else:
            print 'utils.call("/usr/bin/xterm", ["xterm", "-e", "su -c" + " " . join(command)])'


def create_linux_distro_backend():
    distro_backend = None
    if os.path.exists("/usr/bin/lsb_release"):
        dist, version, codename = utils.call(['lsb_release', '--short', '-i'], output=True)[1].strip(), \
                                  utils.call(['lsb_release', '--short', '-r'], output=True)[1].strip(), \
                                  utils.call(['lsb_release', '--short', '-c'], output=True)[1].strip()
    else:
        dist, version, codename = platform.dist()
        dist = dist[0].upper() + dist[1:]
    
    if dist in ["Fedora", "U.F.O"]:
        distro_backend = FedoraLinuxBackend(dist, version, codename)
    elif dist == "Ubuntu":
        distro_backend = UbuntuLinuxBackend(dist, version, codename)
    else:
        distro_backend = GenericLinuxBackend(dist, version, codename)
    return distro_backend
