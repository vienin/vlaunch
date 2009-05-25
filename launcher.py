# -*- coding: utf-8 -*-
         
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
from utils import *

format = "%(asctime)s %(levelname)s %(message)s"
try:
    logging.basicConfig(format=format, level=logging.DEBUG, filename=path.join(conf.SCRIPT_DIR, conf.LOG))
except:
    try:
        logging.basicConfig(format=format, level=logging.DEBUG,
                            filename=path.join(tempfile.gettempdir(), "launcher.log"))
    except:
        pass

if sys.platform == "win32":
    from windowsbackend import *
elif sys.platform == "darwin":
    from macbackend import *
elif sys.platform == "linux2":
    from linuxbackend import *
else:
    raise "Unsupported platform"

print "SCRIPT_DIR", conf.SCRIPT_DIR
print "SCRIPT_PATH", conf.SCRIPT_PATH
print "APP_PATH", conf.APP_PATH

def configure_virtual_machine(create_vmdk = True):
    if not conf.VMDK and not conf.CONFIGUREVM: return

    virtual_box = modifyvm.VBoxConfiguration(conf.HOME, use_template = True)            
    virtual_box.set_machine(conf.VM, use_template = True)
    
    logging.debug("VMDK = " + conf.VMDK + " create_vmdk " + str(create_vmdk))
    if conf.VMDK and create_vmdk:
        logging.debug("Getting size of " + conf.DEV)
        blockcount = get_device_size(conf.DEV)
        
        vmdk = path.join(conf.HOME, "HardDisks", conf.VMDK)
        logging.debug("Creating VMDK file %s with %s of size %d : " % (vmdk, conf.DEV, blockcount))
        uuid = createrawvmdk.createrawvmdk(vmdk, conf.DEV, blockcount)
        virtual_box.set_raw_vmdk(conf.VMDK, uuid, conf.DRIVERANK)
    
    if conf.CONFIGUREVM:
        # compute reasonable memory size
        if conf.RAMSIZE == "auto":
            freeram = get_free_ram()
            conf.RAMSIZE = 2 * freeram / 3
        
        logging.debug("Setting RAM to " + str(conf.RAMSIZE))
        virtual_box.machine.set_ram_size(conf.RAMSIZE)
        
        # check host network adapter
        conf.NETTYPE, net_name = find_network_device()

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
            
        dvd = get_dvd_device()
        logging.debug("Using dvd " + str(dvd))
        virtual_box.machine.set_dvd_direct(dvd)

        if conf.WIDTH and conf.HEIGHT:
            resolution = str(conf.WIDTH) + "x" + str(conf.HEIGHT)
            if conf.WIDTH == "full" and conf.HEIGHT == "full":
                resolution = find_resolution()
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
            home_path, displayed_name = get_host_home()
            virtual_box.machine.set_shared_folder(share_name, home_path)
            virtual_box.machine.set_guest_property("share_" + share_name, displayed_name)
            logging.debug("Setting shared folder : " + home_path + ", " + displayed_name)
        
        # set removable media shared folders
        paths, names = get_usb_devices()
        for usb in range(0, len(paths)):
            if names[usb] == None:
                continue
            virtual_box.machine.set_shared_folder(names[usb], paths[usb])
            virtual_box.machine.set_guest_property("share_" + str(names[usb]), names[usb])
            logging.debug("Setting shared folder : " + str(paths[usb]) + ", " + str(names[usb]))

    # Write changes
    virtual_box.write()
    virtual_box.machine.write()

def find_device():
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
            conf.DEV = find_device_by_volume(conf.VOLUME)
            if conf.DEV != "":
                return conf.STATUS_NORMAL
                
        if conf.MODEL:
            conf.DEV = find_device_by_model(conf.MODEL)
            if conf.DEV != "":
                return conf.STATUS_NORMAL
        
        if conf.ROOTUUID:
            conf.DEV = find_device_by_uuid(conf.ROOTUUID)
            if conf.DEV != "":
                return conf.STATUS_NORMAL
        
        input = dialog_question(u"Attention",
                                u"Aucune clé UFO n'a été trouvée, réessayer ?",
                                u"Oui",
                                u"Non")
        
        if input == "Non":
            if conf.NEEDDEV: return conf.STATUS_EXIT
            
            input = dialog_question(u"Attention",
                                    u"Utiliser un compte invité ?",
                                    u"Oui",
                                    u"Quitter")
            
            if input == "Oui": return conf.STATUS_GUEST
            return conf.STATUS_EXIT
        
        try_times -= 1
    
    return conf.STATUS_EXIT

if not path.isabs(conf.HOME):
    conf.HOME = path.join(conf.SCRIPT_DIR, conf.HOME)
    
if not path.isabs(conf.BIN):
    conf.BIN = path.join(conf.SCRIPT_DIR, conf.BIN)

logging.debug("APP path: " + conf.APP_PATH)
logging.debug("BIN path: " + conf.BIN)
logging.debug("HOME path: " + conf.HOME)

logging.debug("Killing resilient VirtualBox")
kill_resilient_vbox()

logging.debug("Preparing environment")
prepare()

# check virtualbox binaries
logging.debug("Checking VirtualBox binaries")
if not path.exists(path.join(conf.BIN, VIRTUALBOX_EXECUTABLE)) or \
   not path.exists(path.join(conf.BIN, VBOXMANAGE_EXECUTABLE)):
    logging.debug("Missing binaries")
    dialog_info(u"Binaires manquants",
               u"Les fichiers binaires de VirtualBox sont introuvables\n" + \
               u"Vérifiez votre PATH ou télecharger VirtualBox en suivant ce lien http://downloads.virtualbox.org/virtualbox/")
    sys.exit(1)

# redirect VBOX HOME directory
env = { "VBOX_USER_HOME" : conf.HOME, "VBOX_PROGRAM_PATH" : conf.BIN }

command = build_command()
logging.debug("preparing to spawn command: " + " ".join(command) + " with environment " + str(env))

# generate raw vmdk for usb key
create_vmdk = False
logging.debug("Searching device...")
ret = find_device()
if ret == conf.STATUS_NORMAL:
    logging.debug("awaited device found on " + str(conf.DEV))
    if prepare_device(conf.DEV):
        dialog_info("Attention", u"Impossible de démonter le volume UFO, vérifiez qu'il n'est pas en cours d'utilisation.")
        logging.debug("Unable to umount %s, exiting script" % (conf.DEV,))
        sys.exit(1)
    create_vmdk = True
elif ret == conf.STATUS_GUEST:
    logging.debug("no device found, use guest account")
    write_fake_vmdk("")
elif ret == conf.STATUS_IGNORE:
    logging.debug("no vmdk generation needed")
elif ret == conf.STATUS_EXIT:
    logging.debug("no device found, do not start machine")
    sys.exit(1)

logging.debug("Configuring Virtual Machine")
configure_virtual_machine(create_vmdk = create_vmdk)

# launch vm
logging.debug("Launching Virtual Machine")
run_vbox(command, env)

logging.debug("Clean up")
cleanup(command)
