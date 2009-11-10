# -*- coding: utf-8 -*-

# UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
#
# Copyright (c) 2008-2009 Agorabox, Inc.
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


import logging
import fcntl
import struct
import glob
import sys
import os, os.path as path
import conf
import shutil
import gui
import tempfile
import utils

from osbackend import OSBackend

conf.MOBILE = not conf.USESERVICE
conf.VBOX_INSTALLED = path.exists("/Applications/VirtualBox.app") and \
                      not path.islink("/Applications/VirtualBox.app")

logging.debug("Using Mobile mode : " + str(conf.MOBILE.__nonzero__()))
logging.debug("Is VirtualBox installed : " + str(conf.VBOX_INSTALLED))

class MacBackend(OSBackend):
    VBOXMANAGE_EXECUTABLE = "VBoxManage"
    VIRTUALBOX_EXECUTABLE = "VirtualBox"

    HOST_AUDIO_DRIVER = "CoreAudio"

    RELATIVE_VMDK_POLICY = True

    def __init__(self):
        OSBackend.__init__(self)
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
                    del processes[i]
                i -= 1
            if len(pids) > 1:
                logging.debug("U.F.O launched twice. Exiting")
                if gui.dialog_error_report(u"Impossible de lancer UFO", u"UFO semble déjà en cours d'utilisation.\n" + \
                                           u"Veuillez fermer toutes les fenêtres UFO, et relancer le programme.",
                                           u"Forcer à quitter", "Processus " + str("\nProcessus ".join(processes).strip())):
                    for pid in pids:
                        self.call([ "kill", "-9", pid ])

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
        tmpdir = tempfile.mkdtemp(prefix="ufo-updater")

        src = path.join(conf.DATA_DIR, "..", "Mac-Intel")
        logging.debug("Copying " + path.join(src, "UFO.app") + " to " + tmpdir)
        output = self.call([ [ "tar", "-cf", "-", "-C", src, "UFO.app" ],
                             [ "tar", "xf", "-", "-C", tmpdir ] ], output = True)[1]
                                                  
        return path.join(tmpdir, "UFO.app", "Contents", "MacOS", "UFO")

    def get_model(self, dev):
        medianame = utils.grep(self.call(["/usr/sbin/diskutil", "info", dev]), "Media Name:")
        if medianame:
            return medianame[medianame.find(':') + 1:]

    def find_device_by_uuid(self, dev_uuid):
        return ""
    
    def find_device_by_volume(self, dev_volume):
        output = utils.grep(self.call([ "diskutil", "list" ], output=True)[1], " " + dev_volume + " ").split()
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
        mem = utils.grep(self.call([ "top", "-l", "1" ], output=True)[1], "PhysMem:").split()
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
                if utils.grep(infos, "Protocol:").split()[1] == "USB" and \
                   len(utils.grep(infos, "Volume Name:").split()) > 2 and \
                   len(utils.grep(infos, "Mount Point:").split()) > 2:
                    disks.append((utils.grep(infos, "Mount Point:").split()[2],
                                  " ".join(utils.grep(infos, "Volume Name:").split()[2:])))
        except: return []
        return disks

    def get_usb_sticks(self):
        disks = []
        try: 
            for device in glob.glob("/dev/disk[0-9]"):
                infos = self.call([ "diskutil", "info", device ], output=True)[1]
                if utils.grep(infos, "Protocol:").split()[1] == "USB":
                    disks.append([ device, " ".join(utils.grep(infos, "Media Name:").split()[2:]) ])
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
                    if not retcode: 
                        logging.debug("Unable to umount %s, exiting script" % (conf.DEV,))
                        gui.dialog_info(title="Erreur", 
                                        msg=u"Impossible de démonter le volume " + str(volname), 
                                        error=True)
                        return retcode
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
                logging.debug("Environment: " + str(os.environ))
                logging.debug("Sudoing and execv: " + " ".join([ "/usr/bin/sudo" ] + cmd))
                logging.shutdown()
                if False:
                    os.execv("/usr/bin/sudo", [ "/usr/bin/sudo" ] + cmd)
                    # self.call([ "sudo" ] + cmd, fork=False)
                else:
                    self.call([ "sudo" ] + cmd)
                logging.debug("Should not be displayed....")
                sys.exit(0)
            
            sys.exit(0)

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
        self.check_privileges()
        try:
            logging.debug("Creating splash screen")
            self.create_splash_screen()
        except:
            logging.debug("Failed to create splash screen")

        if not conf.VBOX_INSTALLED:
            if os.path.islink("/Applications/VirtualBox.app"):
                os.unlink("/Applications/VirtualBox.app")
            
            os.symlink(path.join(conf.BIN, "..", ".."),
                       "/Applications/VirtualBox.app")
                         
            # Restore permissions
            # self.call([ "/usr/sbin/chown", "-R", "0:0", conf.APP_PATH ])
            # self.call([ "chmod", "-R", "755", "/Applications/VirtualBox.app/Contents" ])
            # for f in glob.glob("/Applications/VirtualBox.app/Contents/*.*"):
            #     self.call([ "chmod", "-R", "644", f ])
        
            self.load_kexts()

    def cleanup(self):
        if conf.MOBILE and conf.PARTS == "all":
            self.restore_fstab()
    
        if not conf.VBOX_INSTALLED:
            os.unlink("/Applications/VirtualBox.app")
        
        if conf.PARTS == "all":
            self.call([ "diskutil", "mountDisk", conf.DEV ])

        if self.tmpdir:
            shutil.rmtree(self.tmpdir)

    def run_vbox(self, command, env):
        self.call(command, env = env, cwd = conf.BIN)

    def find_resolution(self):
        if gui.backend == "PyQt":
            return str(gui.screenRect.width()) + "x" + str(gui.screenRect.height())
        
        return ""
        
    def get_free_size(self, path):
        return 1000
    
    def onExtraDataCanChange(self, key, value):
        # xpcom only return the both out parameters
        return True, ""
