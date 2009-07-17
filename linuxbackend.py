import os, sys, statvfs
import commands
import conf
import subprocess
import platform

def get_su_command(): 
    if os.path.exists("/usr/bin/gksudo"):
        return "/usr/bin/gksudo"                   
    elif os.path.exists("/usr/bin/kdesudo"):   
        return "/usr/bin/kdesudo"
    else:
        return "sudo"

def get_linux_release():
    pass
                                    
try:
    import easygui
except ImportError:
    if os.geteuid() != 0:
       if os.path.exists("/usr/bin/gksudo"):
           os.execv("/usr/bin/gksudo", [ "/usr/bin/gksudo", sys.executable ] + sys.argv)
       elif os.path.exists("/usr/bin/kdesudo"):
           os.execv("/usr/bin/kdesudo", [ "/usr/bin/kdesudo", sys.executable ] + sys.argv)
       else:
           subprocess.call([ "sudo", "-A", sys.executable ] + sys.argv,
                           env = { "SUDO_ASKPASS" : "/media/UFO/Linux/bin/ask-password" })

    if platform.dist()[0] == "Ubuntu" or \
       (os.path.exists("/etc/lsb-release") and "Ubuntu" in open('/etc/lsb-release').read()):
        subprocess.call([ "apt-get", "-y", "install", "python-tk" ])
        import easygui
        reload(easygui)

import glob
import tempfile
import Tkinter
import time
from utils import *
from shutil import copytree

class LinuxBackend(Backend):
    VBOXMANAGE_EXECUTABLE = "VBoxManage"
    VIRTUALBOX_EXECUTABLE = "VirtualBox"

    def __init__(self):
        Backend.__init__(self)
        self.terminated = False
        self.tk = Tkinter.Tk()
        self.tk.withdraw()
        self.ufo_dir = path.normpath(path.join(
                           path.realpath(path.dirname(sys.argv[0])), ".."))
        self.updater_path = self.shadow_updater_path = path.normpath(path.join(self.ufo_dir, "Linux", "bin"))
        self.updater_executable = self.shadow_updater_executable = path.normpath(path.join(self.updater_path,"updater.py"))

    def prepare_update(self):
        shutil.copytree(os.path.join(self.updater_path, "..", "settings"),
                            os.path.join(self.shadow_updater_path, "settings"))
        
    def getuuid(self, dev):
        return commands.getoutput("blkid -o value -s UUID " + dev)

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

    def get_device_size(self, dev):
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
        user = "~" + os.getenv("SUDO_USER", "")
        return path.expanduser(user), "Mes documents Linux"

    def get_usb_devices(self):
        if os.path.exists('/dev/disk/by-id'):
            usb_devices = [ os.path.realpath(os.path.join('/dev/disk/by-id', link)) for link in os.listdir('/dev/disk/by-id') if link[0:3] == "usb" ]
            usb_paths = [ mnt.split()[1] for mnt in open('/proc/mounts','r').readlines() if mnt.split()[0] in usb_devices ]
            return [[path,os.path.basename(path)] for path in usb_paths ]
        return [], []

    def find_resolution(self):
        if path.exists("/usr/bin/xrandr"):
            return commands.getoutput('/usr/bin/xrandr | grep "*"').split()[0]
        return ""

    def build_command(self):
        if conf.STARTVM:
            if conf.KIOSKMODE:
                return [ path.join(conf.BIN, "VBoxSDL"),  "-vm", conf.VM, "-termacpi", "-fullscreen",
                      "-fullscreenresize", "-nofstoggle", "-noresize", "-nohostkeys",  "fnpqrs" ]
            else:
                return [ path.join(conf.BIN, "VBoxManage"), "startvm", conf.VM ]
        else:
            return [ path.join(conf.BIN, "VirtualBox") ]

    def dialog_info(self, title, msg):
        easygui.msgbox(msg=msg, title=title)

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
        if os.geteuid() != 0:
            if os.path.exists("/usr/bin/gksudo"):
                os.execv("/usr/bin/gksudo", [ "/usr/bin/gksudo", sys.executable ] + sys.argv)
            elif os.path.exists("/usr/bin/kdesudo"):
                print [ "/usr/bin/kdesudo", sys.executable ] + sys.argv
                os.execv("/usr/bin/kdesudo", [ "/usr/bin/kdesudo", sys.executable ] + sys.argv)
            else:
                env = os.environ.copy()
                env.update( { "SUDO_ASKPASS" : "/media/UFO/Linux/bin/ask-password" } )
                subprocess.call([ "sudo", "-A", sys.executable ] + sys.argv,
                                env = env)
                                             
    def cleanup(self, command):
        pass

    def kill_resilient_vbox(self):
        self.call([ "killall", "-9", "VBoxXPCOMIPCD" ])
        self.call([ "killall", "-9", "VBoxSVC" ])

    def dialog_question(self, title, msg, button1, button2):
        choices = [ button1, button2 ]
        reply = easygui.buttonbox(msg, title, choices=choices)
        return reply

    def wait_for_termination(self):
        while True:
            if not grep(grep(commands.getoutput("ps ax -o pid,command"), "VirtualBox"), "grep", inverse=True):   
                break
            # logging.debug("Checking for USB devices")
            self.check_usb_devices()
            time.sleep(3)

    def run_vbox(self, command, env):
        # For some reason, it doesn't work with 'call'
        cmd = "VBOX_USER_HOME=" + env["VBOX_USER_HOME"] + " VBOX_PROGRAM_PATH=" + env["VBOX_PROGRAM_PATH"] + " " + " ".join(command)
        os.system(cmd)
        self.wait_for_termination()
        
    def get_free_size(self, path):
        stats = os.statvfs(path)
        return (stats[statvfs.F_BSIZE] * stats[statvfs.F_BFREE]) / 1000000

    def look_for_virtualbox(self):
        logging.debug("Checking VirtualBox binaries")
        if not path.exists(path.join(conf.BIN, self.VIRTUALBOX_EXECUTABLE)) or \
           not path.exists(path.join(conf.BIN, self.VBOXMANAGE_EXECUTABLE)):
            import platform
            dist = platform.dist()
            if dist[0] == "Ubuntu" or \
               (os.path.exists("/etc/lsb-release") and "Ubuntu" in open('/etc/lsb-release').read()):
                dist = "hardy"
                open("/etc/apt/sources.list", "a").write(
                    "deb http://download.virtualbox.org/virtualbox/debian %s non-free\n" % (dist,))
                os.system("wget -q http://download.virtualbox.org/virtualbox/debian/sun_vbox.asc -O- | sudo apt-key add -")
                subprocess.call([ "apt-get", "update" ])
                subprocess.call([ "apt-get", "-y", "install", "virtualbox-2.2" ])
        Backend.look_for_virtualbox(self)

