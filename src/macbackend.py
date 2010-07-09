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


import logging
import fcntl
import struct
import glob
import sys
import os, os.path as path
from conf import conf
import shutil
import gui
import tempfile
import utils
import re

from osbackend import OSBackend

conf.MOBILE = not conf.USESERVICE
conf.VBOX_INSTALLED = path.exists("/Applications/VirtualBox.app") and \
                      not path.islink("/Applications/VirtualBox.app")

logging.debug("Using Mobile mode : " + str(conf.MOBILE.__nonzero__()))
logging.debug("Is VirtualBox installed : " + str(conf.VBOX_INSTALLED))

class MacBackend(OSBackend):

    VBOXMANAGE_EXECUTABLE = "VBoxManage"
    VIRTUALBOX_EXECUTABLE = "VirtualBox"
    RELATIVE_VMDK_POLICY  = True
    KEXTS                 = "kexts"

    def __init__(self):
        OSBackend.__init__(self, "macosx")
        self.OS_VERSION = os.uname()[2]
        if self.OS_VERSION < "9":
            self.KEXTS = path.join(self.KEXTS, "Tiger")
        self.disks = []
        self.tmpdir = ""

    def get_default_audio_driver(self):
        return self.vbox.constants.AudioDriverType_CoreAudio

    def check_process(self):
        logging.debug("Checking UFO process")
        # We used to use a pipe, but Satan knows why, it returns a shadow
        # of the running program. So we run two separate commands
        psout = self.call(["ps", "ax", "-o", "pid,command"], output = True)[1]
        processes = [ x[0].strip() for x in re.findall(r"(.*/UFO(\n| .*))", psout) ]
        logging.debug("ufo process : " + str(processes))
        if len(processes) > 1 :
            pids = [ i.strip().split(" ")[0] for i in processes ]
            i = len(pids) - 1
            while i >= 0:
                ppid = self.call(["ps", "-p", pids[i], "-o", "ppid"], output=True)[1].split("\n")[-1].strip()
                logging.debug("Process %s is a child of %s" % (pids[i], ppid))
                if ppid in pids:
                    del pids[i]
                    del processes[i]
                i -= 1
            if len(pids) > 1:
                logging.debug("U.F.O launched twice. Exiting")
                if self.error_already_running("\nProcessus ".join(processes)):
                    for pid in pids:
                        self.call([ "kill", "-9", pid ])

                sys.exit(0)

        logging.debug("Checking VBoxXPCOMIPCD process")
        if self.call([ ["ps", "ax", "-o", "pid,command"],
                       ["grep", "VBoxXPCOMIPCD"],
                       ["grep", "-v", "grep" ] ], output = True)[1]:
            logging.debug("VBoxXPCOMIPCD is still running. Exiting")
            self.error_already_running('', 'VirtualBox')
            sys.exit(0)

    def prepare_update(self):                           
        return self.prepare_self_copy()

    def prepare_self_copy(self):
        self_copied_path = tempfile.mkdtemp(prefix="ufo-self-copied")
        os.mkdir(path.join(self_copied_path, ".data"))

        src = path.join(conf.DATA_DIR, "..")
        logging.debug("Copying " + src + " to " + self_copied_path)
        self.call([ [ "tar", "-cf", "-", "-C", src, "Mac-Intel"],
                    [ "tar", "xf", "-", "-C", self_copied_path ] ], output = True)[1]
        self.call([ [ "tar", "-cf", "-", "-C", conf.DATA_DIR, "images" ],
                    [ "tar", "xf", "-", "-C", path.join(self_copied_path, ".data") ] ], output = True)[1]
        self.call([ [ "tar", "-cf", "-", "-C", conf.DATA_DIR, "locale" ],
                    [ "tar", "xf", "-", "-C", path.join(self_copied_path, ".data") ] ], output = True)[1]
        self.call([ [ "tar", "-cf", "-", "-C", conf.DATA_DIR, "settings" ],
                    [ "tar", "xf", "-", "-C", path.join(self_copied_path, ".data") ] ], output = True)[1]

        return path.join(self_copied_path, "Mac-Intel", conf.MACEXE)

    def get_model(self, dev):
        medianame = utils.grep(self.call(["/usr/sbin/diskutil", "info", dev], output=True)[1], "Media Name:")
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

    def get_free_space(self, path):
        stats = os.statvfs(path)
        return stats.f_bavail * stats.f_bsize

    def get_dvd_device(self):
        pass

    def get_host_shares(self):
        return [{ 'sharename' : "machosthome",
                  'sharepath' : path.expanduser('~'),
                  'displayed' : _("My Mac documents") }]
    
    def get_usb_devices(self):
        disks = []
        try: 
            for device in glob.glob("/dev/disk[0-9]s[0-9]"):
                infos = self.call([ "diskutil", "info", device ], output=True, log=False)[1]
                if utils.grep(infos, "Protocol:").split()[1] == "USB" and \
                   len(utils.grep(infos, "Volume Name:").split()) > 2 and \
                   len(utils.grep(infos, "Mount Point:").split()) > 2:
                    disks.append((utils.grep(infos, "Mount Point:").split()[2],
                                  ":".join(utils.grep(infos, "Volume Name:").split(":")[1:]).lstrip(),
                                  utils.grep(infos, "Device Node:").split()[2][:-2]))
        except: return []
        return disks

    def get_usb_sticks(self):
        disks = []
        try: 
            for device in glob.glob("/dev/disk[0-9]"):
                infos = self.call([ "diskutil", "info", device ], output=True, log=False)[1]
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

    def get_disk_geometry(self, device):
        import re
        output = self.call(["fdisk", device], output=True)[1]
        regexp = re.compile(r"Disk: /dev/disk[0-9]\tgeometry: (\d+)/(\d+)/(\d+) \[(\d+) sectors\]")
        cylinders, heads, sectors, sectors_nb = map(int, regexp.search(output).groups())
        return cylinders, heads, sectors

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
                                        msg=_('Unable to unmount the volume ') + str(volname), 
                                        error=True)
                        return retcode
            return 0
        return 0

    def execv(self, cmd, root=False):
        if root:
            tries = 0
            while tries < 3:
                logging.debug("Asking user password")
                remember = False
                password = gui.dialog_password(remember=False)
                if password == None:
                    ret = -1
                    break

                self.call([ "sudo", "-k" ])
                ret = self.call([ [ "echo", str(password)],
                                  [ "sudo", "-S", "touch", sys.executable ] ], log=False)[0]
                if ret == 0:
                    if remember:
                        output = self.call( [ "sudo", "-l" ], output=True)[1]
                        if not "NOPASSWD: /Volumes/UFO/Mac-Intel/UFO.app/Contents/MacOS/UFO" in output:
                            sudoline = os.environ["USER"] + " ALL=(ALL) NOPASSWD: /Volumes/UFO/Mac-Intel/UFO.app/Contents/MacOS/UFO"
                            self.call([ "sudo", "-n", "-s", "echo -e " + sudoline + " >> /etc/sudoers" ])
                    break
                else:
                    gui.dialog_info(title=_("Error"),
                                    msg=_("Sorry, couldn't authenticate. Please check your password."),
                                    error=True)
                    tries += 1

            if ret == 0:
                cmd = [ "sudo" ] + cmd
            else:
                return 
        logging.debug("Environment: " + str(os.environ))
        logging.debug("execv: " + " ".join(cmd))
        logging.shutdown()

        #os.execv(cmd[0], cmd)
        self.call(cmd, spawn=True)

    def is_admin(self):
        return os.geteuid() == 0;

    def umount_device(self, device):
        if self.call([ "diskutil", "unmountDisk", device ]) != 0:
            return False
        return True

    def get_kernel_modules(self):
        if self.OS_VERSION < "9":
            modules = [ "VBoxDrvTiger.kext" ]
        else:
            modules = [ "VBoxDrv.kext", "VBoxNetFlt.kext" ]
        return modules

    def load_kexts(self):
        # loading kernel extentions
        KEXTS = path.join(conf.BIN, self.KEXTS)
        self.tmpdir = tempfile.mkdtemp()

        modules = self.get_kernel_modules()

        for module in modules:
            modulepath = path.join(self.tmpdir, module)
            shutil.copytree(path.join(KEXTS, module), modulepath)
            self.call(["chmod", "-R", "644", modulepath ])
            self.call(["chown", "-R", "0:0", modulepath ])

        self.call(["/sbin/kextload"] + map(lambda x: path.join(self.tmpdir, x), modules))

    def unload_kexts(self):
        modules = self.get_kernel_modules()
        modules.reverse()
        self.call(["/sbin/kextunload"] + map(lambda x: path.join(self.tmpdir, x), modules))

    def kill_resilient_vbox(self):
        # Kill resident com server
        self.call([ "killall", "-9", "VBoxXPCOMIPCD" ])
        self.call([ "killall", "-9", "VBoxSVC" ])

    def prepare(self):
        if not self.is_admin():
            if path.basename(sys.executable) == "python":
                cmd = [ path.join(path.dirname(sys.executable), path.basename(conf.MACEXE)) ]
            else:
                cmd = [ sys.executable ] + sys.argv
            cmd += [ "--respawn" ]

            self.execv(cmd, True)
            sys.exit(1)

        if not conf.VBOX_INSTALLED:
            if os.path.islink("/Applications/VirtualBox.app"):
                os.unlink("/Applications/VirtualBox.app")

            # Restore permissions
            # self.call([ "/usr/sbin/chown", "-R", "0:0", conf.APP_PATH ])
            # self.call([ "chmod", "-R", "755", "/Applications/VirtualBox.app/Contents" ])
            # for f in glob.glob("/Applications/VirtualBox.app/Contents/*.*"):
            #     self.call([ "chmod", "-R", "644", f ])

            self.load_kexts()
        else:
            self.installed_vbox_error()

        if "x86_64" in os.uname()[-1]:
            self.unsupported_platform(arch="Mac OS X 64 bits")

        os.chdir(path.join(conf.BIN, "..", "Frameworks"))

    def cleanup(self):
        if conf.MOBILE and conf.PARTS == "all":
            self.restore_fstab()
        
        if conf.PARTS == "all":
            self.call([ "diskutil", "mountDisk", conf.DEV ])

        self.unload_kexts()

        if self.tmpdir:
            shutil.rmtree(self.tmpdir)

    def run_vbox(self, command, env):
        self.call(command, env = env)

    def find_resolution(self):
        if gui.backend == "PyQt":
            return str(gui.screenRect.width()) + "x" + str(gui.screenRect.height())
        
        return ""

    def onExtraDataCanChange(self, key, value):
        # xpcom only return the both out parameters
        return True, ""
