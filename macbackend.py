import fcntl
import struct
import glob
import sys
import os, os.path as path
import logging
import conf
import shutil
import gui
import tempfile
import time
from utils import *

conf.APP_PATH = path.dirname(path.dirname(conf.SCRIPT_DIR))
conf.MOBILE = not conf.USESERVICE
conf.VBOX_INSTALLED = path.exists("/Applications/VirtualBox.app") and \
                      not path.islink("/Applications/VirtualBox.app")
logging.debug("Using Mobile mode : " + str(conf.MOBILE.__nonzero__()))
logging.debug("Is VirtualBox installed : " + str(conf.VBOX_INSTALLED))

class MacBackend(Backend):
    VBOXMANAGE_EXECUTABLE = "VBoxManage"
    VIRTUALBOX_EXECUTABLE = "VirtualBox"

    HOST_AUDIO_DRIVER = "CoreAudio"

    RELATIVE_VMDK_POLICY = True

    def __init__(self):
        Backend.__init__(self)
        gui.set_icon(path.join(conf.SCRIPT_DIR, "..", "..", "..", "UFO.ico"))
        self.KEXTS = "kexts"
        self.OS_VERSION = os.uname()[2]
        if self.OS_VERSION < "9":
            self.KEXTS = path.join(self.KEXTS, "Tiger")
        self.disks = []
        self.tmpdir = ""

    def check_process(self):
        logging.debug("Checking UFO process")
        processes = self.call([ ["ps", "ax", "-o", "pid,command"],
                                ["grep", "-i", "\\/ufo\\(-updater.py\\)\\?\\( \\|$\\)"] ], output = True)[1].strip().split("\n")
        logging.debug("ufo process : " + str(processes))
        if len(processes) > 1 :
            pids = [ i.strip().split(" ")[0] for i in processes ]
            i = len(pids) - 1
            while i >= 0:
                if self.call(["ps", "-p", pids[i], "-o", "ppid"], output=True)[1].strip().split("\n")[-1].strip() in pids:
                    del pids[i]
                i -= 1
            if len(pids) > 1: 
                logging.debug("U.F.O launched twice. Exiting")
                gui.dialog_info(title=u"Impossible de lancer UFO",
                                 error=True,
                                 msg=u"UFO semble déjà en cours d'utilisation. \n" \
                                     u"Veuillez fermer toutes les fenêtres UFO, et" \
                                     u"relancer le programme.")
                sys.exit(0)

        logging.debug("Checking VBoxXPCOMIPCD process")
        if self.call([ ["ps", "ax", "-o", "pid,command"],
                       ["grep", "VBoxXPCOMIPCD"],
                       ["grep", "-v", "grep" ] ], output = True)[1]:
            logging.debug("VBoxXPCOMIPCD is still running. Exiting")
            gui.dialog_info(title=u"Impossible de lancer UFO",
                             error=True,
                             msg=u"VirtualBox semble déjà en cours d'utilisation. \n" \
                                 u"Veuillez fermer toutes les fenêtres de VirtualBox, " \
                                 u"et relancer le programme.")
            sys.exit(0)

    def prepare_update(self):
        self.ufo_dir = path.join(path.realpath(path.dirname(sys.argv[0])), "..", "..", "..", "..")
        self.updater_path = path.join(self.ufo_dir, "Mac-Intel", "UFO.app", "Contents", "Resources", "Ufo-updater.app")
        self.shadow_updater_path = tempfile.mktemp(prefix="ufo-updater", suffix=".app")
        self.shadow_updater_executable = path.join(self.shadow_updater_path,
                                                  "Contents", "MacOS", "Ufo-updater")
                                                  
        logging.debug("Copying " + self.updater_path + " to " + self.shadow_updater_path)
        shutil.copytree(self.updater_path, self.shadow_updater_path)
        shutil.copytree(path.join(self.updater_path, "..", ".VirtualBox"),
                        path.join(self.shadow_updater_path, "Contents", "Resources", ".VirtualBox"))
                        # ignore=ignore_patterns(("comp*", "Hard*", "Iso*", "Machine*", "ufo-pole*", "uuid", "Virt*", "xpti*")))
        shutil.copytree(path.join(self.updater_path, "..", "settings"),
                        path.join(self.shadow_updater_path, "Contents", "Resources", "settings"))

    def get_model(self, dev):
        medianame = grep(self.call(["/usr/sbin/diskutil", "info", dev]), "Media Name:")
        if medianame:
            return medianame[medianame.find(':') + 1:]

    def find_device_by_uuid(self, dev_uuid):
        return ""
    
    def find_device_by_volume(self, dev_volume):
        output = grep(self.call([ "diskutil", "list" ], output=True)[1], " " + dev_volume + " ").split()
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
        mem = grep(self.call([ "top", "-l", "1" ], output=True)[1], "PhysMem:").split()
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
                infos = self.call([ "diskutil", "info", device ], output=True)[1]
                if grep(infos, "Protocol:").split()[1] == "USB" and \
                   len(grep(infos, "Volume Name:").split()) > 2 and \
                   len(grep(infos, "Mount Point:").split()) > 2:
                    disks.append((grep(infos, "Mount Point:").split()[2],
                                  " ".join(grep(infos, "Volume Name:").split()[2:])))
        except: return []
        return disks

    def restore_fstab(self):
        if path.exists('/etc/fstab'):
            os.unlink('/etc/fstab')
        if path.exists('/etc/fstab.bak'):
            shutil.copyfile("/etc/fstab.bak", "/etc/fstab")

    def get_device_parts(self, dev):
        parts = glob.glob(dev + 's[0-9]')
        device_parts = {}
        for part in parts:
            part_number = int(part[len(part)-1:])
            part_info = [ part, self.get_device_size(dev[:5] + "r" + dev[5:], part_number) ]
            device_parts.update({ part_number : part_info })
        return device_parts

    def get_device_size(self, dev, partition = 0):
        if partition > 0:
            dev = dev + "s" + str(partition)
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
        # TODO:
        # Use chflags cmd insteadof fstab workaround 
        # when conf.PARTS == "all".
        # Also use chflags to avoid system mounts 
        # other volume than UFO, if they are mountable. 
        if conf.PARTS == "all":
            if conf.MOBILE:
                if path.exists("/etc/fstab"):
                    shutil.copyfile("/etc/fstab", "/etc/fstab.bak")
    
            for partition in glob.glob(disk + "s*"):
                volname = grep(self.call([ "diskutil", "info", partition ], output=True)[1], "Volume Name:").split()
                if not volname or len(volname) < 3: continue
                volname = volname[2]
                fstype = grep(self.call([ "diskutil", "info", partition ], output=True)[1], "File System:").split()
                if fstype:
                    fstype = fstype[2]
                    fstype = { "MS-DOS" : "msdos", "Ext2" : "ext2", "Ext3" : "ext3" }.get(fstype, fstype)
                    logging.debug('echo "LABEL=%s none %s rw,noauto" >> /etc/fstab' % (volname, fstype))
                    if conf.MOBILE:
                        append_to_end("/etc/fstab", "LABEL=%s none %s rw,noauto\n" % (volname, fstype))
                    retcode = self.call([ "diskutil", "unmount", partition ])
                    if not retcode: return retcode
            return 0
        return 0

    def check_privileges(self):
        if os.geteuid() != 0:
            tries = 0
            while tries < 3:
                logging.debug("Asking user password")
                password, ok = gui.dialog_password(rcode=True)
                if not ok:
                    ret = -1
                    break

                self.call([ "sudo", "-k" ])
                ret = self.call([ [ "echo", str(password)], 
                                  [ "sudo", "-S", "touch", sys.executable ] ])[0]
                if ret == 0:
                    break
                else:
                    gui.dialog_info(title="Erreur", 
                                     msg="Erreur lors de la saisie du mot de passe", 
                                     error=True)
                    tries += 1

            if ret == 0:
                if path.basename(sys.executable) == "python":
                    cmd = [ path.join(path.dirname(sys.executable), "UFO") ]
                else:
                    cmd = [ sys.executable ] + sys.argv
                cmd += [ "--respawn" ]
                logging.debug("Sudoing and execv")
                logging.shutdown()
                self.call([ "sudo" ] + cmd, fork=False)
                logging.debug("Should not be displayed....")
                sys.exit(0)
            
            sys.exit(0)

    def is_ready(self):
        # test if i need to move at another location
        if conf.APP_PATH.startswith("/Volumes") and conf.PARTS == "all":
            conf.READY = 0
        else:
            conf.READY = 1

        if not conf.READY:
            self.tmpdir = tempfile.mkdtemp(suffix="ufo")
            logging.debug("Copying myself from " + conf.APP_PATH + " to " + self.tmpdir)

            output = self.call([ [ "tar", "-cf", "-", "-C", conf.APP_PATH, ".." ], 
                                 [ "tar", "xf", "-", "-C", self.tmpdir ] ], output = True)[1]

            logging.debug(" ".join([ path.join(self.tmpdir, "UFO.app", "Contents", "MacOS", "UFO") ]))
            logging.shutdown()

            env = os.environ.copy()
            env["VBOX_USER_HOME"] = conf.HOME
            self.call([ path.join(self.tmpdir, "UFO.app", "Contents", "MacOS", "UFO") ], env = env)
            sys.exit(0)

        logging.debug("Ready")

    def load_kexts(self):
        # loading kernel extentions
        KEXTS = path.join(conf.BIN, self.KEXTS)
        tmpdir = tempfile.mkdtemp()
        
        if self.OS_VERSION < "9":
            modules = [ "VBoxDrvTiger.kext" ]
        else:
            modules = [ "VBoxDrv.kext", "VBoxNetFlt.kext" ]

        for module in modules:
            modulepath = path.join(tmpdir, module)
            shutil.copytree(path.join(KEXTS, module), modulepath)
            self.call(["chmod", "-R", "644", modulepath ])
            self.call(["chown", "-R", "0:0", modulepath ])

        self.call(["/sbin/kextload"] + map(lambda x: path.join(tmpdir, x), modules))

    def kill_resilient_vbox(self):
        # Kill resident com server
        self.call([ "killall", "-9", "VBoxXPCOMIPCD" ])
        self.call([ "killall", "-9", "VBoxSVC" ])

    def prepare(self):
        # Ajusting paths
        if not conf.HOME: conf.HOME = path.join(conf.APP_PATH, "Contents", "Resources", ".VirtualBox")
        if not conf.BIN: conf.BIN = path.join(conf.APP_PATH, "Contents", "Resources", "VirtualBox.app", "Contents", "MacOS")

        self.check_privileges()
        try:
            logging.debug("Creating splash screen")
            self.create_splash_screen()
        except:
            logging.debug("Failed to create splash screen")
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

    def cleanup(self):
        if conf.MOBILE and conf.PARTS == "all":
            self.restore_fstab()
    
        if not conf.VBOX_INSTALLED:
            os.unlink("/Applications/VirtualBox.app")
        
        if conf.PARTS == "all":
            self.call([ "diskutil", "mountDisk", conf.DEV ])

        if conf.MOBILE and conf.PARTS == "all":
            shutil.copyfile(conf.LOG, path.join(tempfile.gettempdir(), path.basename(conf.LOG)))
            logging.debug("Got VBOX_USER_HOME from parent : " + str(os.environ.get("VBOX_USER_HOME")))
            if os.environ.has_key("VBOX_USER_HOME"):
                logging.debug("Overwriting " + os.path.join(os.environ["VBOX_USER_HOME"], "VirtualBox.xml") + \
                              " with " + os.path.join(conf.HOME, "VirtualBox.xml"))
                shutil.copyfile(os.path.join(conf.HOME, "VirtualBox.xml"),
                                os.path.join(os.environ["VBOX_USER_HOME"], "VirtualBox.xml"))
            if self.tmpdir:
                shutil.rmtree(self.tmpdir)

    """
    def wait_for_termination(self):
        while True:
            logging.debug("Splash screen ? " + str(self.splash))
            if not grep(grep(self.call([ "ps", "ax", "-o", "pid,command" ], output=True)[1], "VirtualBoxVM"), "grep", inverse=True):
                break
            disks = glob.glob("/dev/disk[0-9]")
            if self.disks != disks:
                self.check_usb_devices()
                self.disks = disks
            time.sleep(2)
    """

    def run_vbox(self, command, env):
        self.call(command, env = env, cwd = conf.BIN)

    def find_resolution(self):
        return ""
        
    def get_free_size(self, path):
        return 1000

