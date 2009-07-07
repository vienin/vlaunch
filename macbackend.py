import fcntl
import struct
import commands
import glob
import sys
import os, os.path as path
import subprocess
import logging
import conf
import shutil
import easygui
import tempfile
import time
from utils import *
import Tkinter

conf.APP_PATH = path.dirname(path.dirname(conf.SCRIPT_DIR))
conf.MOBILE = not conf.USESERVICE
conf.VBOX_INSTALLED = path.exists("/Applications/VirtualBox.app") and \
                      not path.islink("/Applications/VirtualBox.app")
logging.debug("Using Mobile mode : " + str(conf.MOBILE.__nonzero__()))
logging.debug("Is VirtualBox installed : " + str(conf.VBOX_INSTALLED))

class MacBackend(Backend):
    VBOXMANAGE_EXECUTABLE = "VBoxManage"
    VIRTUALBOX_EXECUTABLE = "VirtualBox"

    def __init__(self):
        self.KEXTS = "kexts"
        self.OS_VERSION = os.uname()[2]
        if self.OS_VERSION < "9":
            self.KEXTS = path.join(self.KEXTS, "Tiger")
        self.tk = Tkinter.Tk()
        self.tk.withdraw()
        self.disks = []
        self.tmpdir = ""
        self.ufo_dir = path.join(path.realpath(path.dirname(sys.argv[0])), "..", "..", "..")
        self.updater_path = path.join(self.ufo_dir, "UFO.app", "Contents", "Resources", "Updater.app")
        self.shadow_updater_path = tempfile.mktemp(prefix="Updater", suffix=".app")
        self.shadow_updater_executable = path.join(self.shadow_updater_path,
                                                  "Contents", "MacOS", "Updater")

    def get_model(self, dev):
        medianame = grep(commands.getoutput("/usr/sbin/diskutil info " + dev), "Media Name:")
        if medianame:
            return medianame[medianame.find(':') + 1:]

    def find_device_by_uuid(self, dev_uuid):
        return ""
    
    def find_device_by_volume(self, dev_volume):
        output = grep(commands.getoutput("diskutil list"), " " + dev_volume + " ").split()
        if output:
            return "/dev/" + output[-1][:-2]
        return ""

    def find_device_by_model(self, dev_model):
        for device in glob.glob("/dev/disk[0-9]"):
            model = self.get_model(device)
            logging.debug("device: %s, %s" % (device, model))
            if model == dev_model:
                return device[:-2]
        return ""

    def get_free_ram(self):
        maxmem = 384
        mem = grep(commands.getoutput("top -l 1"), "PhysMem:").split()
        for ind, val in enumerate(mem):
            if ind > 0 and val in [ "inactive", "free", "free." ]:
                val = mem[ind - 1]
                ival = float(val[:-1])
                if val.endswith('G'):
                    ival *= 1024
                maxmem = max(int(ival), maxmem)
        return maxmem

    def get_dvd_device(self):
        pass

    def get_host_home(self):
        return path.expanduser('~'), "Mes documents Mac"
    
    def get_usb_devices(self):
        disks = []
        try: 
            for device in glob.glob("/dev/disk[0-9]s[0-9]"):
                infos = commands.getoutput("diskutil info " + device)
                if grep(infos, "Protocol:").split()[1] == "USB" and \
                   len(grep(infos, "Volume Name:").split()) > 2 and \
                   len(grep(infos, "Mount Point:").split()) > 2:
                    disks.append((grep(infos, "Mount Point:").split()[2],
                                  grep(infos, "Volume Name:").split()[2]))
        except: return []
        return disks

    def restore_fstab(self):
        if path.exists('/etc/fstab'):
            os.unlink('/etc/fstab')
        if path.exists('/etc/fstab.bak'):
            shutil.copyfile("/etc/fstab.bak", "/etc/fstab")

    def dialog_question(self, msg, title, button1, button2):
        choices = [ button1, button2 ]
        reply = easygui.buttonbox(msg=msg, title=title, choices=choices, root=self.tk)
        return reply

    """
    output, err = subprocess.call(
        ["/usr/bin/osascript", "-e",
         'tell application "UFO" to display dialog "%s" with title "%s" buttons {"%s", "%s"} default button 2' %
            (msg, title, button1, button2)])
    match = "button returned:"
    ind = output.find(match)
    if ind != -1:
        return output[ind + len(match):]
    return ""
    """

    def dialog_info(self, title, msg):
        """
        subprocess.call(
            ["/usr/bin/osascript", "-e",
             'tell app "UFO" to display dialog "%s" with title "%s" buttons "OK"' %
                (msg, title) ])
        """
        easygui.msgbox(msg=msg, title=title, root=self.tk)
            
    # generic dialog box for ask password 
    # params :
    # return : pass_string
    def dialog_password(self):
        return easygui.passwordbox(msg="Veuillez entrer le mot de passe de cet ordinateur", root=self.tk)

        return subprocess.Popen([ "/usr/bin/osascript" ], stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate("""
with timeout of 300 seconds
  tell app "UFO"
    activate
    set Input to display dialog "Entrez votre mot de passe:"
     with title "Mot de passe"
     with icon caution
     default answer ""
     buttons {"Annuler", "OK"}
     default button 2
     with hidden answer
    giving up after 295
    return text returned of Input as string
  end tell
end timeout
""")

    def get_device_size(self, dev):
        fd = os.open(dev, os.O_RDONLY)
  
        DKIOCGETBLOCKSIZE = 1074029592
        DKIOCGETBLOCKCOUNT = 1074291737
    
        blocksize = struct.unpack("l", fcntl.ioctl(fd, DKIOCGETBLOCKSIZE, struct.pack("l", 0)))[0]
        blockcount = struct.unpack("L", fcntl.ioctl(fd, DKIOCGETBLOCKCOUNT, struct.pack("L", 0)))[0]

        os.close(fd)
        return blockcount

    def find_network_device(self):
       if conf.NETTYPE == conf.NET_HOST and conf.HOSTNET != "":
           return conf.NET_HOST, conf.HOSTNET   

       return conf.NET_NAT, ""
  
    # find each mountable partitions of the device
    # and add an entry in fstab to disable automount
    # params : dev_string
    # return : 0 if device is ready
    def prepare_device(self, disk):
        if conf.MOBILE:
            if path.exists("/etc/fstab"):
                shutil.copyfile("/etc/fstab", "/etc/fstab.bak")
    
        for partition in glob.glob(disk + "s*"):
            volname = grep(commands.getoutput("diskutil info " + partition), "Volume Name:").split()
            if not volname or len(volname) < 3: continue
            volname = volname[2]
            fstype = grep(commands.getoutput("diskutil info " + partition), "File System:").split()
            if fstype:
                fstype = fstype[2]
                fstype = { "MS-DOS" : "msdos", "Ext2" : "ext2", "Ext3" : "ext3" }.get(fstype, fstype)
                logging.debug('echo "LABEL=%s none %s rw,noauto" >> /etc/fstab' % (volname, fstype))
                if conf.MOBILE:
                    append_to_end("/etc/fstab", "LABEL=%s none %s rw,noauto\n" % (volname, fstype))
                retcode = self.call([ "diskutil", "unmount", partition ])
                if not retcode: return retcode
        return 0

    def check_privileges(self):
        if os.geteuid() != 0:
            password = self.dialog_password()
            if conf.USESERVICE:
                self.call([ "sudo", "/Applications/UFO.app/Contents/MacOS/UFO" ])
                sys.exit(0)
            else:
                self.call([ "sudo" , "-k" ])
                if path.basename(sys.executable) == "python":
                    cmd = [ path.join(path.dirname(sys.executable), "UFO") ]
                else:
                    cmd = [ sys.executable ] + sys.argv
                logging.debug(" ".join([ "sudo", "-S" ] + cmd))
                logging.debug("Sudoing and exiting")
                logging.shutdown()
                p = subprocess.Popen([ "sudo", "-S" ] + cmd, stdin=subprocess.PIPE, close_fds=True)
                p.communicate(password)
                if p.returncode:
                    self.dialog_info(title="Erreur", msg="Erreur lors de la saisie du mot de passe")
                # logging.debug("Exiting...")
                sys.exit(0)

    def is_ready(self):
        # test if i need to mode at another location
        if not conf.APP_PATH.startswith("/Volumes"):
            conf.READY = 1

        if not conf.READY:
            self.tmpdir = tempfile.mkdtemp(suffix="ufo")
            logging.debug("Copying myself to " + self.tmpdir)
            self.call([ "cp", "-P", "-R", conf.APP_PATH, self.tmpdir + "/"])
            logging.debug(" ".join([ path.join(self.tmpdir, "UFO.app", "Contents", "MacOS", "UFO") ]))
            logging.shutdown()
            env = os.environ.copy()
            env["VBOX_USER_HOME"] = conf.HOME
            subprocess.Popen([ path.join(self.tmpdir, "UFO.app", "Contents", "MacOS", "UFO") ],
                env = env, close_fds=True)
            # logging.debug("Exiting for good")
            sys.exit(0)

        logging.debug("Ready")

    def load_kexts(self):
        # loading kernel extentions
        KEXTS = path.join(conf.BIN, self.KEXTS)

        if self.OS_VERSION < "9":
            modules = [ "VBoxDrvTiger.kext" ]
        else:
            modules = [ "VBoxDrv.kext", "VBoxNetFlt.kext" ]

        self.call(["/sbin/kextload"] + map(lambda x: path.join(KEXTS, x), modules))

    def kill_resilient_vbox(self):
        # Kill resident com server
        self.call([ "killall", "-9", "VBoxXPCOMIPCD" ])

    def build_command(self):
        if conf.STARTVM:
            # VBoxSDL do not exist for Mac...
            return [ path.join(conf.BIN, "VirtualBoxVM"), "-startvm", conf.VM ]
            # return [ path.join(conf.BIN, "VBoxManage"), "startvm", conf.VM ]
        else:
            return [ path.join(conf.BIN, "VirtualBox") ]

    def prepare(self):
        # Ajusting paths
        if not conf.HOME: conf.HOME = path.join(conf.APP_PATH, "Contents", "Resources", ".VirtualBox")
        if not conf.BIN: conf.BIN = path.join(conf.APP_PATH, "Contents", "Resources", "VirtualBox.app", "Contents", "MacOS")

        self.check_privileges()
        self.is_ready()
        if not conf.VBOX_INSTALLED:
            if os.path.islink("/Applications/VirtualBox.app"):
                os.unlink("/Applications/VirtualBox.app")
            
            os.symlink(path.join(conf.APP_PATH, "Contents", "Resources", "VirtualBox.app"),
                       "/Applications/VirtualBox.app")
                         
            # Restore permissions
            self.call([ "/usr/sbin/chown", "-R", "0:0", conf.APP_PATH ])
            self.call([ "chmod", "-R", "755", "/Applications/VirtualBox.app/Contents" ])
            for f in glob.glob("/Applications/VirtualBox.app/Contents/*.*"):
                self.call([ "chmod", "-R", "644", f ])
        
            self.load_kexts()

    def cleanup(self, command):
        if conf.MOBILE:
            self.restore_fstab()
    
        if not conf.VBOX_INSTALLED:
            os.unlink("/Applications/VirtualBox.app")
        
        self.call([ "diskutil", "mountDisk", conf.DEV ])
    
        # clean host
        command = path.basename(command[0])
        if command.lower() != "Virtualbox".lower():
            while True:
                if not grep(grep(commands.getoutput("ps ax -o pid,command"), "VirtualBoxVM"), "grep", inverse=True):
                    break
                time.sleep(2)

        if conf.MOBILE:
            shutil.copyfile(conf.LOG, path.join(tempfile.gettempdir(), path.basename(conf.LOG)))
            logging.debug("Got VBOX_USER_HOME from parent : " + str(os.environ.get("VBOX_USER_HOME")))
            if os.environ.has_key("VBOX_USER_HOME"):
                logging.debug("Overwriting " + os.path.join(os.environ["VBOX_USER_HOME"], "VirtualBox.xml") + \
                              " with " + os.path.join(conf.HOME, "VirtualBox.xml"))
                shutil.copyfile(os.path.join(conf.HOME, "VirtualBox.xml"),
                                os.path.join(os.environ["VBOX_USER_HOME"], "VirtualBox.xml"))
            if self.tmpdir:
                shutil.rmtree(self.tmpdir)

    def check_usb_changes(self):
        while True:
            logging.debug("Waiting for VirtualBoxVM to start")
            if grep(grep(commands.getoutput("ps ax -o pid,command"), "VirtualBoxVM"), "grep", inverse=True):
                break
            time.sleep(2)
        while True:
            logging.debug("Waiting for termination")
            if not grep(grep(commands.getoutput("ps ax -o pid,command"), "VirtualBoxVM"), "grep", inverse=True):
                break
            disks = glob.glob("/dev/disk[0-9]")
            if self.disks != disks:
                self.check_usb_devices()
                self.disks = disks
            time.sleep(2)

    def run_vbox(self, command, env):
        self.splash.destroy()
        import thread
        thread.start_new_thread(self.check_usb_changes, ())
        self.call(command, env = env, cwd = conf.BIN)

    def find_resolution(self):
        return ""
