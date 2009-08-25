# -*- coding: iso8859-15 -*-

#import modifyvm

import logging
import commands
import glob
import shutil
import os, os.path as path
import sys
import subprocess
import createrawvmdk
import os
import conf
import shutil
import tempfile
from utils import *
import uuid
from splash import SplashScreen
from ConfigParser import ConfigParser
from ufovboxapi import VBoxHypervisor

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

class Backend:
    def __init__(self):
        self.usb_devices = []
        self.tmp_swapdir = ""
        self.tmp_overlaydir = ""
        self.puel = False
        self.do_not_update = False

        # redirect VBOX HOME directory
        os.environ.update({ "VBOX_USER_HOME" : conf.HOME, "VBOX_PROGRAM_PATH" : conf.BIN })
        self.env = env = os.environ.copy()

        self.vbox = VBoxHypervisor()

    def call(self, cmd, env = None, shell = False, cwd = None, output = False):
        logging.debug(" ".join(cmd) + " with environment : " + str(env))
        if output:
            p = subprocess.Popen(cmd, env = env, shell = shell, cwd = cwd, stdout=subprocess.PIPE)
            output = p.communicate()
            logging.debug("Returned : " + str(p.returncode))
            return p.returncode, output
        else:
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

    def create_virtual_machine(self, create_vmdk = True):
        self.vbox.create_machine(conf.VM, conf.OS)
        self.vbox.open_machine(conf.VM)

        self.vbox.current_machine.set_bios_params(acpi_enabled = True, ioapic_enabled = True)
        self.vbox.current_machine.set_vram_size(32)
        self.vbox.current_machine.set_network_adapter(adapter_type = "I82540EM")
        self.vbox.current_machine.disable_boot_menu()
        self.vbox.current_machine.set_audio_adapter(self.audio_driver())
        
        if conf.LICENSE == 1:
            self.vbox.set_extra_data("GUI/LicenseAgreed", "7")

        self.vbox.set_extra_data("GUI/MaxGuestResolution", "any")
        self.vbox.set_extra_data("GUI/Input/AutoCapture", "true")
        self.vbox.set_extra_data("GUI/TrayIcon/Enabled", "false")
        self.vbox.set_extra_data("GUI/UpdateCheckCount", "2")
        self.vbox.set_extra_data("GUI/UpdateDate", "never")
        self.vbox.set_extra_data("GUI/SuppressMessages", ",remindAboutAutoCapture,confirmInputCapture," + 
                                 "remindAboutMouseIntegrationOn,remindAboutMouseIntegrationOff," + 
                                 "remindAboutInaccessibleMedia,remindAboutWrongColorDepth,confirmGoingFullscreen")

        self.vbox.current_machine.set_extra_data("GUI/SaveMountedAtRuntime", "false")
        self.vbox.current_machine.set_extra_data("GUI/Fullscreen", "on")
        self.vbox.current_machine.set_extra_data("GUI/Seamless", "off")
        self.vbox.current_machine.set_extra_data("GUI/LastCloseAction", "powerOff")
        self.vbox.current_machine.set_extra_data("GUI/AutoresizeGuest", "on")

    def configure_virtual_machine(self, create_vmdk = True):
        if not conf.VMDK and not conf.CONFIGUREVM:
            logging.debug("Skipping configuration of the VM")
            self.vbox.close_session()
            return

        #virtual_box = modifyvm.VBoxConfiguration(conf.HOME, use_template = True)            
        #virtual_box.set_machine(conf.VM, use_template = True)
    
        logging.debug("VMDK = " + conf.VMDK + " create_vmdk " + str(create_vmdk))
        if conf.VMDK and create_vmdk:
            rank = conf.DRIVERANK
            if conf.LIVECD:
                rank += 1
            
            vmdk = path.join(conf.HOME, "HardDisks", conf.VMDK)
            if conf.PARTS == "all":
                logging.debug("Getting size of " + conf.DEV)
                blockcount = self.get_device_size(conf.DEV)
                logging.debug("Creating VMDK file %s with %s of size %d: " % (vmdk, conf.DEV, blockcount))
                #vmdk_uuid = createrawvmdk.createrawvmdk(vmdk, conf.DEV, blockcount)
                createrawvmdk.createrawvmdk(vmdk, conf.DEV, blockcount)

            else:
                logging.debug("Creating vbox VMDK file %s with %s, partitions %s: " % (vmdk, conf.DEV, conf.PARTS))
                if os.path.exists(vmdk):
                    os.unlink(vmdk)
                if os.path.exists(vmdk[:len(vmdk) - 5] + "-pt.vmdk"):
                    os.unlink(vmdk[:len(vmdk) - 5] + "-pt.vmdk")

                # TODO: add this feature to createrawvmdk.createrawvmdk()
                self.create_vbox_raw_vmdk(vmdk, conf.DEV, conf.PARTS)

                #uuid_line = grep(open(vmdk).read(), "ddb.uuid.image")
                #vmdk_uuid = uuid_line[len("ddb.uuid.image= "):len(uuid_line) -1]
            #virtual_box.set_raw_vmdk(conf.VMDK, vmdk_uuid, conf.DRIVERANK)
            self.vbox.current_machine.attach_harddisk(vmdk, conf.DRIVERANK)

        if conf.CONFIGUREVM:
            # compute reasonable memory size
            if conf.RAMSIZE == "auto":
                #freeram = self.get_free_ram()
                freeram = self.vbox.host.get_free_ram()
                conf.RAMSIZE = 2 * freeram / 3
        
            logging.debug("Setting RAM to " + str(conf.RAMSIZE))
            #virtual_box.machine.set_ram_size(conf.RAMSIZE)
            self.vbox.current_machine.set_ram_size(conf.RAMSIZE)
            
            # check host network adapter
            conf.NETTYPE, net_name = self.find_network_device()
            if conf.NETTYPE == conf.NET_NAT:
                logging.debug(conf.SCRIPT_NAME + ": using nat networking")
                #virtual_box.machine.set_net_adapter_to_nat()
                self.vbox.current_machine.set_network_adapter(attach_type = 'NAT')

            elif conf.NETTYPE == conf.NET_HOST:
                # setting network interface to host
                logging.debug("Using net bridge on " + net_name)
                #virtual_box.machine.set_net_adapter_to_host(net_name)
                #if conf.MACADDR:
                #    virtual_box.machine.set_mac_address(conf.MACADDR)
                self.vbox.current_machine.set_network_adapter(attach_type = 'Bridged', mac_address = conf.MACADDR)

            # attach boot iso
            if conf.BOOTFLOPPY:
                logging.debug("Using boot floppy image " + conf.BOOTFLOPPY)
                #virtual_box.set_floppy_image (conf.BOOTFLOPPY)
                #virtual_box.machine.set_boot_device ('Floppy')
                self.vbox.current_machine.attach_floppy(os.path.join(conf.HOME, "Isos", conf.BOOTFLOPPY))
                self.vbox.current_machine.set_boot_device('Floppy') 
            if conf.BOOTISO:
                logging.debug("Using boot iso image " + conf.BOOTISO)
                #virtual_box.set_dvd_image (conf.BOOTISO)
                self.vbox.current_machine.attach_dvd(os.path.join(conf.HOME, "Isos", conf.BOOTISO))
                if not conf.LIVECD:
                    #virtual_box.machine.set_boot_device ('DVD')
                    self.vbox.current_machine.set_boot_device('DVD') 
            else:
                #dvd = self.get_dvd_device()
                logging.debug("Using host dvd drive")
                #virtual_box.machine.set_dvd_direct(dvd)
                
                # TODO: find host DVD drive from IHost                
                # self.vbox.current_machine.attach_dvd(host_drive = True)

            if conf.LIVECD or not conf.BOOTISO and not conf.BOOTFLOPPY:
                logging.debug("Using hard disk for booting")
                #virtual_box.machine.set_boot_device ('HardDisk')
                self.vbox.current_machine.set_boot_device('HardDisk') 
                
            if conf.LIVECD:
                logging.debug("Setting bootdisk for Live CD at rank %d" % (conf.DRIVERANK,))
                #virtual_box.set_vdi (conf.BOOTDISK, conf.BOOTDISKUUID, conf.DRIVERANK)
                self.vbox.current_machine.attach_harddisk(conf.BOOTDISK, conf.DRIVERANK)
                
            if conf.WIDTH and conf.HEIGHT:
                resolution = str(conf.WIDTH) + "x" + str(conf.HEIGHT)
                if conf.WIDTH == "full" and conf.HEIGHT == "full":
                    resolution = self.find_resolution()
                if resolution != "":
                    self.vbox.current_machine.set_resolution(resolution)
            
            self.vbox.current_machine.set_fullscreen()
            #virtual_box.machine.set_logo_image(glob.glob(path.join(conf.HOME, "ufo-*.bmp"))[0])
            self.vbox.current_machine.set_boot_logo(glob.glob(path.join(conf.HOME, "ufo-*.bmp"))[0])

            # manage shared folders
            #virtual_box.machine.reset_shared_folders()
            #virtual_box.machine.reset_share_properties()
        
            # set host home shared folder
            if not conf.USESERVICE:
                share_name = "hosthome"
                home_path, displayed_name = self.get_host_home()
                #virtual_box.machine.set_shared_folder(share_name, home_path)
                #virtual_box.machine.set_guest_property("share_" + share_name, displayed_name)
                self.vbox.current_machine.add_shared_folder(share_name, home_path, writable = True)
                self.vbox.current_machine.set_guest_property("share_" + share_name, displayed_name)
                logging.debug("Setting shared folder : " + home_path + ", " + displayed_name)
                
                self.dnddir = tempfile.mkdtemp(suffix="ufodnd")
                #virtual_box.machine.set_shared_folder("DnD", self.dnddir)
                self.vbox.current_machine.add_shared_folder("DnD", self.dnddir, writable = True)
                logging.debug("Setting shared folder : " + self.dnddir + ", DnD")
        
            # set removable media shared folders
            usb_devices = self.get_usb_devices()
            for usb in usb_devices:
                if usb[1] == None:
                    continue
                #virtual_box.machine.set_shared_folder(usb[1], usb[0])
                #virtual_box.machine.set_guest_property("share_" + str(usb[1]), usb[1])
                self.vbox.current_machine.add_shared_folder(usb[1], usb[0], writable = True)
                self.vbox.current_machine.set_guest_property("share_" + str(usb[1]), usb[1])
                logging.debug("Setting shared folder : " + str(usb[0]) + ", " + str(usb[1]))
            self.usb_devices = usb_devices

        logging.debug("conf.SWAPFILE: " + conf.SWAPFILE)
        if conf.SWAPFILE:
            try:
                self.tmp_swapdir = tempfile.mkdtemp(suffix="ufo-swap")
                logging.debug("self.tmp_swapdir = " + self.tmp_swapdir);
                conf.DRIVERANK += 1
                swap_rank = conf.DRIVERANK
                shutil.copyfile (path.join(conf.HOME, "HardDisks", conf.SWAPFILE), path.join(self.tmp_swapdir, conf.SWAPFILE))
                logging.debug(" shutil.copyfile ( " + path.join(conf.HOME, "HardDisks", conf.SWAPFILE) + ", " + path.join(self.tmp_swapdir, conf.SWAPFILE))
                #virtual_box.set_vdi (path.join(self.tmp_swapdir, conf.SWAPFILE), conf.SWAPUUID, swap_rank)
                self.vbox.current_machine.attach_harddisk(path.join(self.tmp_swapdir, conf.SWAPFILE), swap_rank)

                swap_dev = "sd" + chr(swap_rank + ord('a'))
                #virtual_box.machine.set_guest_property("swap", swap_dev)
                self.vbox.current_machine.set_guest_property("swap", swap_dev)
                        
                free_size = self.get_free_size(self.tmp_swapdir)
                if free_size:
                    swap_size = min(conf.SWAPSIZE, free_size)
                    #virtual_box.machine.set_guest_property("swap_size", str(swap_size))
                    self.vbox.current_machine.set_guest_property("swap_size", str(swap_size))
            except:
                logging.debug("Exception while creating swap")
        
        logging.debug("conf.OVERLAYFILE: " + conf.OVERLAYFILE)
        if conf.OVERLAYFILE:
            try:
                self.tmp_overlaydir = tempfile.mkdtemp(suffix="ufo-overlay")
                logging.debug("self.tmp_overlaydir = " + self.tmp_overlaydir);
                conf.DRIVERANK += 1
                overlay_rank = conf.DRIVERANK
                shutil.copyfile (path.join(conf.HOME, "HardDisks", conf.OVERLAYFILE), path.join(self.tmp_overlaydir, conf.OVERLAYFILE))
                logging.debug(" shutil.copyfile ( " + path.join(conf.HOME, "HardDisks", conf.OVERLAYFILE) + ", " + path.join(self.tmp_overlaydir, conf.OVERLAYFILE))
                #virtual_box.set_vdi (path.join(self.tmp_overlaydir, conf.OVERLAYFILE), conf.OVERLAYUUID, overlay_rank)
                self.vbox.current_machine.attach_harddisk(path.join(self.tmp_overlaydir, conf.OVERLAYFILE), overlay_rank)

                # TODO:
                # Set guest prop about max size of the overlay to 
                # to set apropriate quota within guest side.
                #
                # free_size = self.get_free_size(self.tmp_overlaydir)
                # if free_size:
                #     virtual_box.machine.set_guest_property("overlay_quota", ...)
            except:
                logging.debug("Exception while creating overlay")

        # Write changes
        #virtual_box.write()
        #virtual_box.machine.write()
        self.vbox.close_session()

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
        
            input = self.dialog_question(title=u"Attention",
                                         msg=u"Aucune clé UFO n'a été trouvée, réessayer ?",
                                         button1=u"Oui",
                                         button2=u"Non")
        
            if input == "Non":
                if conf.NEEDDEV: return conf.STATUS_EXIT
            
                input = self.dialog_question(title=u"Attention",
                                             msg=u"Utiliser un compte invité ?",
                                             button1=u"Oui",
                                             button2=u"Quitter")
            
                if input == "Oui": return conf.STATUS_GUEST
                return conf.STATUS_EXIT
        
            try_times -= 1
    
        return conf.STATUS_EXIT

    def look_for_virtualbox(self):
        # check virtualbox binaries
        logging.debug("Checking VirtualBox binaries")
        if not path.exists(path.join(conf.BIN, self.VIRTUALBOX_EXECUTABLE)) or \
           not path.exists(path.join(conf.BIN, self.VBOXMANAGE_EXECUTABLE)):
             logging.debug("Missing binaries in " + conf.BIN)
             self.dialog_info(msg=u"Les fichiers binaires de VirtualBox sont introuvables\n" + \
                              u"Vérifiez votre PATH ou télecharger VirtualBox en suivant ce lien http://downloads.virtualbox.org/virtualbox/",
                              title=u"Binaires manquants")
             sys.exit(1)

    def check_usb_devices(self):
        # set removable media shared folders
        usb_devices = self.get_usb_devices()
        for usb in usb_devices:
            if usb[1] == None:
                continue
            if usb in self.usb_devices:
                continue
            #self.add_shared_folder(usb[1], usb[0])
            #self.set_guest_property("share_" + str(usb[1]), usb[1])
            self.vbox.current_machine.add_shared_folder(usb[1], usb[0], writable = "True")
            self.vbox.current_machine.set_guest_property("share_" + str(usb[1]), usb[1])
            logging.debug("Setting shared folder : " + str(usb[0]) + ", " + str(usb[1]))
        self.usb_devices = usb_devices

    def run_virtual_machine(self, env):
        if self.splash:
            self.splash.destroy()
        if conf.STARTVM:
            self.vbox.current_machine.start()
        else:
            self.run_vbox(self.vbox_gui_command(), env)
        self.wait_for_termination()

    def remove_settings_files(self):
        if self.vbox.license_agreed():
            cp = ConfigParser()
            cp.read(conf.conf_file)
            cp.set("launcher", "LICENSE", "1")
            cp.write(open(conf.conf_file, "w"))
        shutil.rmtree(path.join(conf.HOME, "Machines"))
        os.unlink(path.join(conf.HOME, "VirtualBox.xml"))

    def run(self):
        if not path.isabs(conf.HOME):
            conf.HOME = path.join(conf.SCRIPT_DIR, conf.HOME)

        if not path.isabs(conf.BIN):
            conf.BIN = path.join(conf.SCRIPT_DIR, conf.BIN)

        logging.debug("Preparing environment")
        logging.debug("APP path: " + conf.APP_PATH)
        logging.debug("BIN path: " + conf.BIN)
        logging.debug("HOME path: " + conf.HOME)
        self.prepare()

        self.look_for_virtualbox()

        # generate raw vmdk for usb key
        create_vmdk = False
        logging.debug("Searching device...")
        ret = self.find_device()
        if ret == conf.STATUS_NORMAL:
            logging.debug("awaited device found on " + str(conf.DEV))
            if self.prepare_device(conf.DEV):
                self.dialog_info(title="Attention", msg=u"Impossible de démonter le volume UFO, vérifiez qu'il n'est pas en cours d'utilisation.")
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
        self.create_virtual_machine()

        logging.debug("Configuring Virtual Machine")
        self.configure_virtual_machine(create_vmdk = create_vmdk)

        # launch vm
        logging.debug("Launching Virtual Machine")
        self.run_virtual_machine(self.env)

        logging.debug("Clean up")
        self.remove_settings_files()
        self.cleanup()

        if self.dnddir:
            shutil.rmtree(self.dnddir)

        if self.tmp_swapdir:
            os.unlink(path.join(self.tmp_swapdir, conf.SWAPFILE))

        if self.tmp_overlaydir:
            os.unlink(path.join(self.tmp_overlaydir, conf.OVERLAYFILE))
