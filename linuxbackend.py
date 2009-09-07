# -*- coding: utf-8 -*-

import os, sys, statvfs
import os.path as path
import conf
import logging
import platform
import gui

def get_su_command(): 
    if os.path.exists("/usr/bin/gksudo"):
        return "/usr/bin/gksudo"                   
    elif os.path.exists("/usr/bin/kdesudo"):   
        return "/usr/bin/kdesudo"
    else:
        return "sudo"

def zenityfy(cmd, msg = []):
    if os.path.exists("/usr/bin/zenity"):
        logging.debug("Zenitify " + " ".join(cmd))
        if msg: msg = [ "--text", msg ]
        self.call([ [ cmd ], [ "/usr/bin/zenity", "--progress", "--auto-close" ] + msg ])
        #p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        #p2 = subprocess.Popen([ "/usr/bin/zenity", "--progress", "--auto-close" ] + msg, stdin=p1.stdout)
        #p2.communicate()
    else:
        self.call([ cmd ])

def get_distro():
    if os.path.exists("/usr/bin/lsb_release"):
        return (self.call([ 'lsb_release', '--short', '-i' ], output=True)[1].strip(),
                self.call([ 'lsb_release', '--short', '-r' ], output=True)[1].strip(),
                self.call([ 'lsb_release', '--short', '-c' ], output=True)[1].strip())
    else:
        return platform.dist()
                                    
def run_as_root(command):
    if os.geteuid() != 0:
       if os.path.exists("/usr/bin/gksudo"):
           os.execv("/usr/bin/gksudo", [ "/usr/bin/gksudo" ] + command)
       elif os.path.exists("/usr/bin/kdesudo"):
           os.execv("/usr/bin/kdesudo", [ "/usr/bin/kdesudo" ] + command)
       else:
           dist, version, codename = get_distro()
           version = float(version)
           if dist in ("Fedora", "redhat") and version >= 10:
               if not os.path.exists("/usr/bin/beesu"):
                   msg = "Veuillez patientez pendant l'installation de composants\nnécessaires au lancement d'UFO"
                   if os.path.exists("/usr/bin/gpk-install-package-name"):
                       zenityfy([ "/usr/bin/gpk-install-package-name", "beesu" ], msg)
                   else:
                       zenityfy([ "/usr/bin/pkcon", "install", "beesu" ], msg)
               if os.path.exists("/usr/bin/beesu"):
                   os.execv("/usr/bin/beesu", [ "beesu" ] + command)
           if os.isatty(0):
               graphical_ask_pass = False
               os.environ["SUDO_ASKPASS"] = path.join(conf.SCRIPT_DIR, "bin", "ask-password")
               try:
                   version = self.call([ "sudo", "-V" ], output=True)[1].split("\n")[0].split()[2]
                   if version >= "1.7.1":
                       graphical_ask_pass = True
               except:
                   raise
               if graphical_ask_pass:
                   os.execv("/usr/bin/sudo", [ "sudo", "-A" ] + command)
           os.execv("/usr/bin/xterm", [ "xterm", "-e", "su -c " + " ".join(command) ])
            
try:
    import easygui
except ImportError:
    distro, release, codename = get_distro()
    if distro == "Ubuntu":
        run_as_root([ "apt-get", "-y", "install", "python-tk" ])
        import easygui
        reload(easygui)
    elif distro == "fedora" or os.path.exists('/usr/bin/pkcon'):
        zenitify([ "pkcon", "install", "tkinter" ])
        import easygui
        reload(easygui)
    else:
        msg = 'Votre distribution Linux n\'est pas officiellement ' \
               'supportée.\nVeuillez installer les packages python-tk et VirtualBox.'
        if os.path.exists("/usr/bin/zenity"):
            self.call([ "zenity", "--info", '--text="' + msg + '"' ])
        else:
            print msg
        sys.exit(1)

import glob
import tempfile
import time
from utils import *
from shutil import copytree

class LinuxBackend(Backend):
    VBOXMANAGE_EXECUTABLE = "VBoxManage"
    VIRTUALBOX_EXECUTABLE = "VirtualBox"

    HOST_AUDIO_DRIVER = "Pulse"

    RELATIVE_VMDK_POLICY = True

    def __init__(self):
        Backend.__init__(self)
        gui.set_icon(path.join(conf.SCRIPT_DIR, "..", "UFO.ico"))
        self.terminated = False

    def check_process(self):
        logging.debug("Checking UFO process")
        processes = self.call([ ["ps", "ax", "-o", "pid,command"],
                                ["grep", "\\/ufo\\(-updater.py\\)\\?\\( \\|$\\)"] ], output = True)[1].strip().split("\n")
        logging.debug("ufo process : " + str(processes))
        if len(processes) > 1 :
            pids = [ i.strip().split(" ")[0] for i in processes ]
            i = len(pids) - 1
            while i >= 0:
                if self.call(["ps", "-p", pids[i], "-o", "ppid"], output=True)[1].strip().split("\n")[-1] in pids:
                    del pids[i]
                i -= 1
            if len(pids) > 1: 
                logging.debug("U.F.O launched twice. Exiting")
                self.dialog_info(title= u"Impossible de lancer UFO",
                                 error=True,
                                 msg=u"UFO semble déjà en cours d'utilisation. \n" \
                                    u"Veuillez fermer toutes les fenêtres UFO, et relancer le programme.")
                sys.exit(0)

        logging.debug("Checking VBoxXPCOMIPCD process")
        if self.call([ ["ps", "ax", "-o", "pid,command"],
                       ["grep", "VBoxXPCOMIPCD"],
                       ["grep", "-v", "grep" ] ], output = True)[1]:
            logging.debug("VBoxXPCOMIPCD is still running. Exiting")
            self.dialog_info(title=u"Impossible de lancer UFO",
                             error=True,
                             msg=u"VirtualBox semble déjà en cours d'utilisation. \n" \
                                 u"Veuillez fermer toutes les fenêtres de VirtualBox, et relancer le programme.")
            sys.exit(0)


    def prepare_update(self):
        self.ufo_dir = path.normpath(path.join(
                           path.realpath(path.dirname(sys.argv[0])), ".."))
        self.updater_path = self.shadow_updater_path = path.normpath(path.join(self.ufo_dir, "Linux", "bin"))
        self.updater_executable = self.shadow_updater_executable = path.normpath(path.join(self.updater_path,"ufo-updater.py"))
        
        shutil.copytree(os.path.join(self.updater_path, "..", "settings"),
                            os.path.join(self.shadow_updater_path, "settings"))
        
    def getuuid(self, dev):
        return self.getoutput([ "blkid", "-o", "value", "-s", "UUID", dev ])

    def find_device_by_uuid(self, dev_uuid):
        for device in glob.glob("/dev/sd*[0-9]"):
            uuid = self.getuuid(device)
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

    def prepare_device(self, disk):
        self.call([ "umount", disk + "3" ])
        self.call([ "umount", disk + "4" ])
    
    def get_device_parts(self, dev):
        parts = glob.glob(dev + '[0-9]')
        device_parts = {}
        for part in parts:
            part_number = int(part[len(part)-1:])
            part_info = [ part, self.get_device_size(dev, part_number) ]
            device_parts.update({ part_number : part_info })
        return device_parts

    def get_device_size(self, dev, partition = 0):
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

    def get_host_home(self):
        if os.environ.has_key("SUDO_USER"):
            user = os.getenv("SUDO_USER", "")
        elif os.environ.has_key("USERHELPER_UID"):
            user = self.call([ [ "getent", "passwd", os.getenv("USERHELPER_UID") ], 
                               [ "cut", "-f", "1", "-d", ":" ] ], output=True)[1].strip()
        else:
            user = os.getenv("USER")
        return path.expanduser("~" + user), "Mes documents Linux"

    def get_usb_devices(self):
        if os.path.exists('/dev/disk/by-id'):
            usb_devices = [ os.path.realpath(os.path.join('/dev/disk/by-id', link)) for link in os.listdir('/dev/disk/by-id') if link[0:3] == "usb" ]
            usb_paths = [ mnt.split()[1] for mnt in open('/proc/mounts','r').readlines() if mnt.split()[0] in usb_devices ]
            return [[path,os.path.basename(path)] for path in usb_paths ]
        return [], []

    def find_resolution(self):
        if path.exists("/usr/bin/xrandr"):
            try:
                return self.call([ [ "/usr/bin/xrandr" ], [ "grep", "*" ] ], output=True)[1].split()[0]
            except:
                raise
        return ""

    def dialog_info(self, title, msg, error = False):
        gui.msgbox(msg=msg, title=title, error=error)

    def check_privileges(self):
        if os.geteuid() != 0:
            dialog_info(title="Droits insuffisants",
                        msg="Vos permissions ne sont pas suffisantes pour lancer UFO. " + \
                        "Veuillez entrer le mot de passe administrateur dans l'invite de " + \
                        "la console :")
            self.call([ "su", "-c", sys.executable ])
            sys.exit(0)

    def prepare(self):
        self.call([ "rmmod", "kvm-intel" ])
        self.call([ "rmmod", "kvm-amd" ])
        self.call([ "rmmod", "kvm" ])
        run_as_root([ sys.executable ] + sys.argv + [ "--respawn" ])
                                             
    def cleanup(self):
        pass

    def kill_resilient_vbox(self):
        self.call([ "killall", "-9", "VBoxXPCOMIPCD" ])
        self.call([ "killall", "-9", "VBoxSVC" ])

    def dialog_question(self, title, msg, button1, button2):
        return gui.dialog_question(msg=msg, title=title, button1=button1, button2=button2)

    def wait_for_termination(self):
        while True:
            if not grep(grep(self.call([ "ps", "ax", "-o", "pid,command" ], output=True)[1], "VirtualBox"), "grep", inverse=True):   
                break
            # logging.debug("Checking for USB devices")
            self.check_usb_devices()
            time.sleep(3)

    def run_vbox(self, command, env):
        # For some reason, it doesn't work with 'call'
        cmd = "VBOX_USER_HOME=" + env["VBOX_USER_HOME"] + " VBOX_PROGRAM_PATH=" + env["VBOX_PROGRAM_PATH"] + " " + command
        os.system(cmd)
        
    def get_free_size(self, path):
        stats = os.statvfs(path)
        return (stats[statvfs.F_BSIZE] * stats[statvfs.F_BFREE]) / 1000000

    def look_for_virtualbox(self):
        logging.debug("Checking VirtualBox binaries")
        if not path.exists(path.join(conf.BIN, self.VIRTUALBOX_EXECUTABLE)) or \
           not path.exists(path.join(conf.BIN, self.VBOXMANAGE_EXECUTABLE)):
            distro, release, codename = get_distro()
            if distro == "Ubuntu":
                open("/etc/apt/sources.list", "a").write(
                    "deb http://download.virtualbox.org/virtualbox/debian %s non-free\n" % (codename.lower(),))
                os.system("wget -q http://download.virtualbox.org/virtualbox/debian/sun_vbox.asc -O- | apt-key add -")
                self.call([ "apt-get", "update" ])
                self.call([ "apt-get", "-y", "install", "virtualbox-2.2" ])
            elif distro == "Fedora":
                logging.debug("Installing Agorabox repository for VirtualBox")
                zenityfy([ "yum", "-y", "install", "yum-priorities" ], "Installation du plugin Yum : yum-priorities")
                self.call([ "rpm", "-ivf", "http://downloads.agorabox.org/virtualbox/yum/agorabox-virtualbox-yum-repository-1.0.noarch.rpm" ])
                kernel = "kernel"
                if os.uname()[2].endswith("PAE"):
                    kernel += "-PAE"
                logging.debug("Kernel is: " + kernel)
                logging.debug("Installing VirtualBox")
                zenityfy([ "yum", "-y", "install", "VirtualBox-OSE", "VirtualBox-OSE-kmodsrc", kernel + "-devel", "gcc", "make", "lzma" ])
                version = self.call([ "rpm", "-q", "--queryformat", "\"%{VERSION}\"", "VirtualBox-OSE" ], output=True)[1]
                kmod_dir = "VirtualBox-OSE-kmod-" + version
                logging.debug("Decompressing drivers source code from /usr/share/%s/%s.tar.lzma" % (kmod_dir, kmod_dir,))
                self.call([ "tar", "--use-compress-program", "lzma", "-xf", "/usr/share/%s/%s.tar.lzma" % (kmod_dir, kmod_dir,) ],
                                cwd = tempfile.gettempdir())
                tmpdir = tempfile.gettempdir() + "/" + kmod_dir
                if not os.path.exists(tmpdir): os.mkdir(tmpdir)
                ret = self.call([ "make" ], cwd = tmpdir)
                logging.debug("make returned %d", (ret,))
                
        Backend.look_for_virtualbox(self)

