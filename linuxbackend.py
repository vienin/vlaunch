import os, sys
import commands
import conf
import easygui
import glob
import tempfile
import time
from utils import *

class LinuxBackend(Backend):
    VBOXMANAGE_EXECUTABLE = "VBoxManage"
    VIRTUALBOX_EXECUTABLE = "VirtualBox"

    def __init__(self):
        self.terminated = False
        self.ufo_dir = path.normpath(path.join(
                           path.realpath(path.dirname(sys.argv[0])), ".."))
        self.updater_path = path.normpath(path.join(
                           self.ufo_dir, "Linux", "bin", "updater.py"))
        self.shadow_update_executable = self.shadow_updater_path = tempfile.mktemp(prefix="updater", suffix=".py")

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
        return int(open(path.join("/", "sys", "class", "block", path.basename(dev), "size")).read())

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
        return path.expanduser('~'), "Mes documents Linux"

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

