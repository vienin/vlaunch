# -*- coding: iso8859-15 -*-

import logging
import commands
import glob
import shutil
import os, os.path as path
import sys
import subprocess
import modifyvm
import createrawvmdk
import os
import conf
import shutil
import tempfile
from utils import *
from Tkinter import Tk, Image, PhotoImage, Toplevel, FLAT, NW, Canvas
import Tix

def grep(input, pattern, inverse=False):
    for line in input.split("\n"):
        if inverse:
            if pattern not in line:
                return line
        else:
            if pattern in line:
                return line
    return ""

def append_to_end(filename, line):
    if not path.exists(filename):
        lines = [ ]
    else:
        lines = open(filename).readlines()
    if lines and not lines[-1].strip():
        line += "\n" + line
    open(filename, 'a').write(line)

class SplashScreen(Toplevel):
    def __init__(self, master, image=None, timeout=1000):
        """(master, image, timeout=1000) -> create a splash screen
        from specified image file.  Keep splashscreen up for timeout
        milliseconds"""
        Toplevel.__init__(self, master, relief=FLAT, borderwidth=0)
        if master == None: master = Tk()
        self.main = master
        if self.main.master != None: # Why ?
            self.main.master.withdraw()
        self.main.withdraw()
        self.overrideredirect(1)
        self.image = PhotoImage(file=image)
        self.after_idle(self.centerOnScreen)

        self.update()
        self.after(timeout, self.destroy)

    def centerOnScreen(self):
        self.update_idletasks()
        width, height = self.width, self.height = \
                        self.image.width(), self.image.height()

        xmax = self.winfo_screenwidth()
        ymax = self.winfo_screenheight()

        x0 = self.x0 = xmax/2 - width/2
        y0 = self.y0 = ymax/2 - height/2
        
        self.geometry("%dx%d+%d+%d" % (width, height, x0, y0))
        self.createWidgets()

    def createWidgets(self):
        self.canvas = Canvas(self, width=self.width, height=self.height)
        self.canvas.create_image(0,0, anchor=NW, image=self.image)
        self.canvas.pack()

    def destroy(self):
        # self.main.update()
        # self.main.deiconify()
        self.main.withdraw()
        self.withdraw()

class Backend:
    def __init__(self):
        self.usb_devices = []

    def call(self, cmd, env = None, shell = False, cwd = None):
        logging.debug(" ".join(cmd) + " with environment : " + str(env))
        retcode = subprocess.call(cmd, env = env, shell = shell, cwd = cwd)
        logging.debug("Returned : " + str(retcode))
        return retcode

    def find_network_device(self):
        if not conf.HOSTNET:
            return conf.NET_NAT
        return conf.NET_HOST

    def write_fake_vmdk(self, dev):
        vmdk = path.join(conf.HOME, "HardDisks", conf.VMDK)
        shutil.copyfile(path.join(conf.HOME, "HardDisks", "fake.vmdk"), vmdk)

    def configure_virtual_machine(self, create_vmdk = True):
        if not conf.VMDK and not conf.CONFIGUREVM: return

        virtual_box = modifyvm.VBoxConfiguration(conf.HOME, use_template = True)            
        virtual_box.set_machine(conf.VM, use_template = True)
    
        logging.debug("VMDK = " + conf.VMDK + " create_vmdk " + str(create_vmdk))
        if conf.VMDK and create_vmdk:
            logging.debug("Getting size of " + conf.DEV)
            blockcount = self.get_device_size(conf.DEV)
        
            vmdk = path.join(conf.HOME, "HardDisks", conf.VMDK)
            logging.debug("Creating VMDK file %s with %s of size %d : " % (vmdk, conf.DEV, blockcount))
            uuid = createrawvmdk.createrawvmdk(vmdk, conf.DEV, blockcount)
            virtual_box.set_raw_vmdk(conf.VMDK, uuid, conf.DRIVERANK)
    
        if conf.CONFIGUREVM:
            # compute reasonable memory size
            if conf.RAMSIZE == "auto":
                freeram = self.get_free_ram()
                conf.RAMSIZE = 2 * freeram / 3
        
            logging.debug("Setting RAM to " + str(conf.RAMSIZE))
            virtual_box.machine.set_ram_size(conf.RAMSIZE)
        
            # check host network adapter
            conf.NETTYPE, net_name = self.find_network_device()

            if conf.NETTYPE == conf.NET_NAT:
                logging.debug(conf.SCRIPT_NAME + ": using nat networking")
                virtual_box.machine.set_net_adapter_to_nat()

            elif conf.NETTYPE == conf.NET_HOST:
                # setting network interface to host
                logging.debug("Using net bridge on " + net_name)
                virtual_box.machine.set_net_adapter_to_host(net_name)
                if conf.MACADDR:
                    virtual_box.machine.set_mac_address(conf.MACADDR)

            # attach boot iso
            if conf.BOOTISO:
                logging.debug("Using boot floppy image " + conf.BOOTISO)
                virtual_box.set_floppy_image (conf.BOOTISO)
                virtual_box.machine.set_boot_device ('Floppy')
            else:
                logging.debug("Using hard disk for booting")
                virtual_box.machine.set_boot_device ('HardDisk')
            
            dvd = self.get_dvd_device()
            logging.debug("Using dvd " + str(dvd))
            virtual_box.machine.set_dvd_direct(dvd)

            if conf.WIDTH and conf.HEIGHT:
                resolution = str(conf.WIDTH) + "x" + str(conf.HEIGHT)
                if conf.WIDTH == "full" and conf.HEIGHT == "full":
                    resolution = self.find_resolution()
                if resolution != "":
                    virtual_box.machine.set_resolution(resolution)
            
            virtual_box.machine.set_fullscreen()
            virtual_box.machine.set_logo_image(path.join(conf.HOME, "ufo.bmp"))

            # manage shared folders
            virtual_box.machine.reset_shared_folders()
            virtual_box.machine.reset_share_properties()
        
            # set host home shared folder
            if not conf.USESERVICE:
                share_name = "hosthome"
                home_path, displayed_name = self.get_host_home()
                virtual_box.machine.set_shared_folder(share_name, home_path)
                virtual_box.machine.set_guest_property("share_" + share_name, displayed_name)
                logging.debug("Setting shared folder : " + home_path + ", " + displayed_name)
                
                self.dnddir = tempfile.mkdtemp(suffix="ufodnd")
                virtual_box.machine.set_shared_folder("DnD", self.dnddir)
                logging.debug("Setting shared folder : " + self.dnddir + ", DnD")
        
            # set removable media shared folders
            usb_devices = self.get_usb_devices()
            for usb in usb_devices:
                if usb[1] == None:
                    continue
                virtual_box.machine.set_shared_folder(usb[1], usb[0])
                virtual_box.machine.set_guest_property("share_" + str(usb[1]), usb[1])
                logging.debug("Setting shared folder : " + str(usb[0]) + ", " + str(usb[1]))
            self.usb_devices = usb_devices

        # Write changes
        virtual_box.write()
        virtual_box.machine.write()

    def find_device(self):
        found = 0
        try_times = 10

        # use user defined device
        if conf.DEV: return conf.STATUS_NORMAL
    
        # no generation needed
        if not conf.MODEL and not conf.VOLUME and not conf.ROOTUUID:
            return conf.STATUS_IGNORE
    
        # research loop
        while try_times > 0:
            if conf.VOLUME:
                conf.DEV = self.find_device_by_volume(conf.VOLUME)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
                
            if conf.MODEL:
                conf.DEV = self.find_device_by_model(conf.MODEL)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
        
            if conf.ROOTUUID:
                conf.DEV = self.find_device_by_uuid(conf.ROOTUUID)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
        
            input = self.dialog_question(u"Attention",
                                         u"Aucune clé UFO n'a été trouvée, réessayer ?",
                                         u"Oui",
                                         u"Non")
        
            if input == "Non":
                if conf.NEEDDEV: return conf.STATUS_EXIT
            
                input = self.dialog_question(u"Attention",
                                             u"Utiliser un compte invité ?",
                                             u"Oui",
                                             u"Quitter")
            
                if input == "Oui": return conf.STATUS_GUEST
                return conf.STATUS_EXIT
        
            try_times -= 1
    
        return conf.STATUS_EXIT

    def add_shared_folder(self, share_name, host_path):
        self.call([ path.join(conf.BIN, "VBoxManage"), "sharedfolder", "add", conf.VM,
                     "--name", share_name, "--hostpath", host_path, "--transient" ], env = self.env)
                     
    def set_guest_property(self, name, value):
        self.call([ path.join(conf.BIN, "VBoxManage"), "guestproperty", "set", conf.VM,
                     name, value ], env = self.env)

    def check_usb_devices(self):
        # set removable media shared folders
        usb_devices = self.get_usb_devices()
        for usb in usb_devices:
            if usb[1] == None:
                continue
            if usb in self.usb_devices:
                continue
            self.add_shared_folder(usb[1], usb[0])
            self.set_guest_property("share_" + str(usb[1]), usb[1])
            logging.debug("Setting shared folder : " + str(usb[0]) + ", " + str(usb[1]))
        self.usb_devices = usb_devices

    def run(self):
        if not path.isabs(conf.HOME):
            conf.HOME = path.join(conf.SCRIPT_DIR, conf.HOME)
    
        if not path.isabs(conf.BIN):
            conf.BIN = path.join(conf.SCRIPT_DIR, conf.BIN)

        logging.debug("APP path: " + conf.APP_PATH)
        logging.debug("BIN path: " + conf.BIN)
        logging.debug("HOME path: " + conf.HOME)

        logging.debug("Killing resilient VirtualBox")
        self.kill_resilient_vbox()

        logging.debug("Preparing environment")
        self.prepare()

        # check virtualbox binaries
        logging.debug("Checking VirtualBox binaries")
        if not path.exists(path.join(conf.BIN, self.VIRTUALBOX_EXECUTABLE)) or \
           not path.exists(path.join(conf.BIN, self.VBOXMANAGE_EXECUTABLE)):
             logging.debug("Missing binaries in " + conf.BIN)
             self.dialog_info(u"Les fichiers binaires de VirtualBox sont introuvables\n" + \
                              u"Vérifiez votre PATH ou télecharger VirtualBox en suivant ce lien http://downloads.virtualbox.org/virtualbox/",
                              u"Binaires manquants")
             sys.exit(1)

        # redirect VBOX HOME directory
        self.env = env = os.environ.copy()
        env.update({ "VBOX_USER_HOME" : conf.HOME, "VBOX_PROGRAM_PATH" : conf.BIN })

        command = self.build_command()
        logging.debug("preparing to spawn command: " + " ".join(command) + " with environment " + str(env))

        # generate raw vmdk for usb key
        create_vmdk = False
        logging.debug("Searching device...")
        ret = self.find_device()
        if ret == conf.STATUS_NORMAL:
            logging.debug("awaited device found on " + str(conf.DEV))
            if self.prepare_device(conf.DEV):
                self.dialog_info("Attention", u"Impossible de démonter le volume UFO, vérifiez qu'il n'est pas en cours d'utilisation.")
                logging.debug("Unable to umount %s, exiting script" % (conf.DEV,))
                sys.exit(1)
            create_vmdk = True
        elif ret == conf.STATUS_GUEST:
            logging.debug("no device found, use guest account")
            self.write_fake_vmdk("")
        elif ret == conf.STATUS_IGNORE:
            logging.debug("no vmdk generation needed")
        elif ret == conf.STATUS_EXIT:
            logging.debug("no device found, do not start machine")
            sys.exit(1)

        logging.debug("Configuring Virtual Machine")
        self.configure_virtual_machine(create_vmdk = create_vmdk)

        # launch vm
        logging.debug("Launching Virtual Machine")
        self.run_vbox(command, env)

        logging.debug("Clean up")
        if self.dnddir:
                shutil.rmtree(self.dnddir)
        self.cleanup(command)
