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
import commands
import glob
import shutil
import os, os.path as path
import sys
import createrawvmdk
import os
import conf
import shutil
import tempfile
import uuid
import gui
import time
import platform
import utils
from ufovboxapi import *
from ConfigParser import ConfigParser

try:
    import keyring
    print "Using keyring backend"
except:
    try:
        import keyring_ctypes as keyring
        print "Using keyring_ctypes backend"
    except:
        keyring = None
        print "Could find a keyring backend"

class UFOVboxMonitor(VBoxMonitor):
    
    def __init__(self, os_backend):
        VBoxMonitor.__init__(self)
        self.os_backend = os_backend
        
    def onGuestPropertyChange(self, id, name, newValue, flags):
        logging.debug("Guest property: %s" % name)
        if self.os_backend.vbox.current_machine.uuid == id:
            self.os_backend.onGuestPropertyChange(name, newValue, flags)
            
    def onMachineStateChange(self, id, state):
        logging.debug("Machine state changed: %d => %d" %(self.os_backend.vbox.current_machine.last_state, state))

        if self.os_backend.vbox.current_machine.uuid == id:
            self.os_backend.onMachineStateChange(state)
            
    def onExtraDataCanChange(self, id, key, value):
        return self.os_backend.onExtraDataCanChange(key, value)


class OSBackend(object):
    def __init__(self):
        self.usb_devices    = []
        self.tmp_swapdir    = ""
        self.tmp_overlaydir = ""
        self.vbox           = None
        self.puel           = False
        self.splash         = None
        self.do_not_update  = False
        self.credentials    = None
        self.keyring_valid  = False
        self.remember_pass  = None
        
        self.env = self.update_env()

    def update_env(self):
        if not path.isabs(conf.HOME):
            conf.HOME = path.join(conf.DATA_DIR, conf.HOME)
        if not path.isabs(conf.BIN):
            conf.BIN = path.join(conf.SCRIPT_DIR, conf.BIN)

        os.environ.update({ "VBOX_USER_HOME"    : conf.HOME, 
                            "VBOX_PROGRAM_PATH" : conf.BIN,
                            "PYTHONPATH"        : conf.BIN,
                            "VBOX_SDK_PATH"     : os.path.join(conf.SCRIPT_DIR, 
                                                               "bin", 
                                                               "sdk")
                          })

        sys.path.append(conf.BIN)
        sys.path.append(os.path.join(conf.SCRIPT_DIR, "bin"))

        return os.environ.copy()

    def call(self, *args, **keywords):
        return utils.call(*args, **keywords)

    def find_network_device(self):
        if not conf.HOSTNET:
            return conf.NET_NAT
        return conf.NET_HOST

    def create_splash_screen(self):
        try:
            logging.debug("Creating splash screen")
            gui.app.create_splash_screen()
        except:
            logging.debug("Failed to create splash screen")
        
    def destroy_splash_screen(self):
        gui.app.destroy_splash_screen()
        
    def init_vbox_hypervisor(self):
        logging.debug("Creating VBoxHypervisor")

        compreg = path.join(conf.HOME, "compreg.dat")
        if path.exists(compreg):
            os.unlink(compreg)

        self.vbox = VBoxHypervisor(vbox_callback_class=UFOVboxMonitor, vbox_callback_arg=self)
        logging.debug("VBoxHypervisor successfully created")
        
    def create_virtual_machine(self, create_vmdk = True):
        logging.debug("Creating VM")
        self.vbox.create_machine(conf.VM, conf.OS)
        self.vbox.open_machine(conf.VM)

        self.vbox.current_machine.set_bios_params(acpi_enabled = 1, ioapic_enabled = 1)
        self.vbox.current_machine.set_vram_size(32)
        self.vbox.current_machine.set_network_adapter(adapter_type = "I82540EM")
        self.vbox.current_machine.disable_boot_menu()
        self.vbox.current_machine.set_audio_adapter(self.HOST_AUDIO_DRIVER)

        if conf.LICENSE == 1:
            self.vbox.set_extra_data("GUI/LicenseAgreed", "7")

        self.vbox.set_extra_data("GUI/MaxGuestResolution", "any")
        self.vbox.set_extra_data("GUI/Input/AutoCapture", "true")
        self.vbox.set_extra_data("GUI/TrayIcon/Enabled", "false")
        self.vbox.set_extra_data("GUI/UpdateCheckCount", "2")
        self.vbox.set_extra_data("GUI/UpdateDate", "never")
        self.vbox.set_extra_data("GUI/RegistrationData", "triesLeft=0")
        self.vbox.set_extra_data("GUI/SUNOnlineData", "0")
        self.vbox.set_extra_data("GUI/SuppressMessages", ",remindAboutAutoCapture,confirmInputCapture," + 
                                 "remindAboutMouseIntegrationOn,remindAboutMouseIntegrationOff," + 
                                 "remindAboutInaccessibleMedia,remindAboutWrongColorDepth,confirmGoingFullscreen," +
                                 "showRuntimeError.warning.HostAudioNotResponding")

        self.vbox.current_machine.set_extra_data("GUI/SaveMountedAtRuntime", "false")
        # self.vbox.current_machine.set_extra_data("GUI/Fullscreen", "on")
        self.vbox.current_machine.set_extra_data("GUI/Seamless", "off")
        self.vbox.current_machine.set_extra_data("GUI/LastCloseAction", "shutdown")
        self.vbox.current_machine.set_extra_data("GUI/AutoresizeGuest", "on")
        
        if conf.HOSTKEY:
            self.vbox.set_host_key(conf.HOSTKEY)
        
        self.vbox.current_machine.set_guest_property("/UFO/HostPlatform", platform.platform())
        
        logging.debug("VM successfully initialized")

    def configure_virtual_machine(self, create_vmdk = True):
        if not conf.VMDK and not conf.CONFIGUREVM:
            logging.debug("Skipping configuration of the VM")
            self.vbox.close_session()
            return

        logging.debug("VMDK = " + conf.VMDK + " create_vmdk " + str(create_vmdk))
        if conf.VMDK and create_vmdk:
            rank = conf.DRIVERANK
            if conf.LIVECD:
                rank += 1
            
            vmdk = path.normpath(path.join(conf.DATA_DIR, conf.VMDK))
            if os.path.exists(vmdk):
                os.unlink(vmdk)
            if conf.PARTS == "all":
                logging.debug("Getting size of " + conf.DEV)
                blockcount = self.get_device_size(conf.DEV)
                logging.debug("Creating VMDK file %s with %s of size %d: " % (vmdk, conf.DEV, blockcount))
                createrawvmdk.createrawvmdk(vmdk, conf.DEV, blockcount)

            else:
                logging.debug("Creating vbox VMDK file %s with %s, partitions %s: " % (vmdk, conf.DEV, conf.PARTS))
                if os.path.exists(vmdk[:len(vmdk) - 5] + "-pt.vmdk"):
                    os.unlink(vmdk[:len(vmdk) - 5] + "-pt.vmdk")

                device_parts = self.get_device_parts(conf.DEV)
                for current_part in device_parts:
                    device_parts.get(current_part).append(str(current_part) in conf.PARTS.split(','))
                blockcount = self.get_device_size(conf.DEV)
                createrawvmdk.createrawvmdk(vmdk, conf.DEV, blockcount, device_parts, self.RELATIVE_VMDK_POLICY)

            self.vbox.current_machine.attach_harddisk(vmdk, rank)

        if conf.CONFIGUREVM:
            # compute reasonable memory size
            if conf.RAMSIZE == "auto":
                if self.vbox.vbox_version() >= "2.1.0":
                    freeram = self.vbox.host.get_free_ram()
                else:
                    freeram = self.get_free_ram()
                conf.RAMSIZE = max(2 * freeram / 3, conf.MINRAM)

            if int(conf.RAMSIZE) <= int(conf.MINRAM):
                gui.dialog_info(title=u"Attention", 
                                msg=u"La mémoire vive disponible est faible, \n" + \
                                    u"cela peut influer sur la vitesse d'exécution de la machine virtuelle UFO.\n\n" + \
                                    u"Fermer des applications ou redémarrer l'ordinateur peut améliorer les performances.", 
                                error=False)
        
            logging.debug("Setting RAM to " + str(conf.RAMSIZE))
            self.vbox.current_machine.set_ram_size(conf.RAMSIZE)
            
            # Set number of processors
            if self.vbox.vbox_version() >= "3.0.0" and self.vbox.host.is_virt_ex_available():
                logging.debug("Enabling virtualization extensions")
                self.vbox.current_machine.enable_vt(True)
                if conf.CPUS == "autodetect":
                    nbprocs = int(self.vbox.host.get_nb_procs())
                    logging.debug(str(nbprocs) + " processor(s) available on host")
                    if nbprocs >= 2:
                        nbprocs = max(2, nbprocs / 2)
                else:
                    try:
                        nbprocs = int(conf.CPUS)
                    except:
                        nbprocs = 1
                logging.debug("Setting number of processor to " + str(nbprocs))
                self.vbox.current_machine.set_procs(nbprocs)

            # Set 3D acceleration
            self.vbox.current_machine.enable_3D(self.vbox.supports_3D())
                
            # check host network adapter
            conf.NETTYPE, net_name = self.find_network_device()
            if conf.NETTYPE == conf.NET_NAT:
                logging.debug(conf.SCRIPT_NAME + ": using nat networking")
                self.vbox.current_machine.set_network_adapter(attach_type = 'NAT')

            elif conf.NETTYPE == conf.NET_HOST:
                # setting network interface to host
                logging.debug("Using net bridge on " + net_name)
                self.vbox.current_machine.set_network_adapter(attach_type = 'Bridged', 
                                                              host_adapter = conf.HOSTNET, 
                                                              mac_address = conf.MACADDR)
            # attach boot iso
            if conf.BOOTFLOPPY:
                logging.debug("Using boot floppy image " + conf.BOOTFLOPPY)
                self.vbox.current_machine.attach_floppy(conf.BOOTFLOPPY)
                self.vbox.current_machine.set_boot_device('Floppy')

            if conf.BOOTISO:
                logging.debug("Using boot iso image " + conf.BOOTISO)
                self.vbox.current_machine.attach_dvd(conf.BOOTISO)
                if not conf.LIVECD:
                    self.vbox.current_machine.set_boot_device('DVD') 
            else:
                logging.debug("Using host dvd drive")
                # TODO: find host DVD drive from IHost                
                # self.vbox.current_machine.attach_dvd(host_drive = True)

            if conf.LIVECD or not conf.BOOTISO and not conf.BOOTFLOPPY:
                logging.debug("Using hard disk for booting")
                self.vbox.current_machine.set_boot_device('HardDisk') 
                
            if conf.LIVECD:
                logging.debug("Setting bootdisk %s for Live CD at rank %d" % (conf.BOOTDISK, conf.DRIVERANK,))
                self.vbox.current_machine.attach_harddisk(conf.BOOTDISK, conf.DRIVERANK)
            
            if conf.WIDTH and conf.HEIGHT:
                resolution = str(conf.WIDTH) + "x" + str(conf.HEIGHT)
                if conf.WIDTH == "full" and conf.HEIGHT == "full":
                    resolution = self.find_resolution()
                if resolution != "":
                    self.vbox.current_machine.set_resolution(resolution)

            self.vbox.current_machine.set_boot_logo(glob.glob(path.join(conf.IMGDIR, "ufo-*.bmp"))[0])

            # set host home shared folder
            if not conf.USESERVICE:
                share_name = "hosthome"
                home_path, displayed_name = self.get_host_home()
                self.vbox.current_machine.add_shared_folder(share_name, home_path, writable = True)
                self.vbox.current_machine.set_guest_property("/UFO/Com/HostToGuest/Shares/ReadyToMount/" + share_name, displayed_name)
                logging.debug("Setting shared folder : " + home_path + ", " + displayed_name)
                
                self.dnddir = tempfile.mkdtemp(suffix="ufodnd")
                self.vbox.current_machine.add_shared_folder("DnD", self.dnddir, writable = True)
                logging.debug("Setting shared folder : " + self.dnddir + ", DnD")
        
            # set removable media shared folders
            usb_devices = self.get_usb_devices()
            for usb in usb_devices:
                if usb[1] == None:
                    continue
                self.vbox.current_machine.add_shared_folder(usb[1], usb[0], writable = True)
                self.vbox.current_machine.set_guest_property("/UFO/Com/HostToGuest/Shares/ReadyToMount/" + str(usb[1]), usb[1])
                logging.debug("Setting shared folder : " + str(usb[0]) + ", " + str(usb[1]))
            self.usb_devices = usb_devices

        logging.debug("conf.SWAPFILE: " + conf.SWAPFILE)
        if conf.SWAPFILE:
            try:
                if not conf.LIVECD or sys.platform != "win32":
                    self.tmp_swapdir = tempfile.mkdtemp(suffix="ufo-swap")
                    logging.debug("self.tmp_swapdir = " + self.tmp_swapdir);
                    conf.DRIVERANK += 1
                    swap_rank = conf.DRIVERANK
                    shutil.copyfile(conf.SWAPFILE, 
                                    path.join(self.tmp_swapdir, path.basename(conf.SWAPFILE)))
                else:
                    self.tmp_swapdir = conf.DATA_DIR
                self.vbox.current_machine.attach_harddisk(path.join(self.tmp_swapdir, path.basename(conf.SWAPFILE)), swap_rank)

                swap_dev = "sd" + chr(swap_rank + ord('a'))
                self.vbox.current_machine.set_guest_property("/UFO/Storages/Swap/Device", swap_dev)
                        
                free_size = self.get_free_size(self.tmp_swapdir)
                if free_size:
                    swap_size = min(conf.SWAPSIZE, free_size)
                    self.vbox.current_machine.set_guest_property("/UFO/Storages/Swap/Size", str(swap_size))
            except:
                logging.debug("Exception while creating swap")
        
        logging.debug("conf.OVERLAYFILE: " + conf.OVERLAYFILE)
        if conf.OVERLAYFILE:
            try:
                self.tmp_overlaydir = tempfile.mkdtemp(suffix="ufo-overlay")
                logging.debug("self.tmp_overlaydir = " + self.tmp_overlaydir);
                conf.DRIVERANK += 1
                overlay_rank = conf.DRIVERANK
                tmp_overlay = path.join(self.tmp_overlaydir, path.basename(conf.OVERLAYFILE))
                shutil.copyfile(conf.OVERLAYFILE, tmp_overlay)
                self.vbox.current_machine.attach_harddisk(tmp_overlay, overlay_rank)

                # TODO:
                # Set guest prop about max size of the overlay to 
                # to set appropriate quota within guest side.
                #
                # free_size = self.get_free_size(self.tmp_overlaydir)
                # if free_size:
                #     virtual_box.machine.set_guest_property("overlay_quota", ...)
            except:
                logging.debug("Exception while creating overlay")

        if keyring:
            if conf.USER:
                password = self.get_password()
                if password:
                    self.keyring_valid = True
                    self.set_credentials(password)
                else:
                    logging.debug("Found no credentials")
        else:
            self.keyring_valid = None

        self.credentials = self.set_credentials

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
            if conf.ROOTUUID:
                conf.DEV = self.find_device_by_uuid(conf.ROOTUUID)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
            if conf.VOLUME:
                conf.DEV = self.find_device_by_volume(conf.VOLUME)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
            if conf.MODEL:
                conf.DEV = self.find_device_by_model(conf.MODEL)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
            if not conf.LIVECD:
                input = gui.dialog_question(title=u"Attention",
                                         msg=u"Aucune clé UFO n'a été trouvée, réessayer ?",
                                         button1=u"Oui",
                                         button2=u"Non")
                if input == "Non":
                    if conf.NEEDDEV: return conf.STATUS_EXIT
                    return conf.STATUS_EXIT
            else:
                usb = self.get_usb_sticks()
                names = [ x[1] for x in usb ]
                ret = gui.dialog_choices(msg=u"Selectionnez le périphérique USB sur lequel vous voulez installer UFO",
                                         title=u"UFO", column=u"Périphérique", choices= [ u"Aucune clée" ] + names)
                if not ret:
                    return conf.STATUS_IGNORE
                    
                conf.DEV = usb[ret - 1][0]
                return conf.STATUS_NORMAL
                
            try_times -= 1

        return conf.STATUS_EXIT

    def checking_pyqt(self):
        logging.debug("Checking PyQt")

    def look_for_virtualbox(self):
        # Check virtualbox binaries
        logging.debug("Checking VirtualBox binaries")
        if not path.exists(path.join(conf.BIN, self.VIRTUALBOX_EXECUTABLE)):
             logging.debug("Missing binaries in " + conf.BIN)
             gui.dialog_info(msg=u"Les fichiers binaires de VirtualBox sont introuvables\n" + \
                                 u"Vérifiez votre PATH ou télecharger VirtualBox en suivant ce " + \
                                 u"lien http://downloads.virtualbox.org/virtualbox/",
                            title=u"Binaires manquants")
             sys.exit(1)

    def onGuestPropertyChange(self, name, newValue, flags):
        # Shared folder management
        if os.path.dirname(name) == "/UFO/Com/GuestToHost/Shares/UserAccept":
            share_label = os.path.basename(name)
            share_name, share_mntpt = newValue.split(";")
            self.vbox.current_machine.add_shared_folder(share_label, share_mntpt, writable = True)
            self.vbox.current_machine.set_guest_property("/UFO/Com/HostToGuest/Shares/ReadyToMount/" + share_label, 
                                                         share_name)
            
        elif os.path.dirname(name) == "/UFO/Com/HostToGuest/Shares/Remove":
            self.vbox.current_machine.remove_shared_folder(os.path.basename(name))
        
        # UFO settings management
        elif os.path.dirname(name) == "/UFO/Settings":
            cp = ConfigParser()
            cp.read(conf.conf_file)
            if not cp.has_section("guest"):
                cp.add_section("guest")
            cp.set("guest", os.path.basename(name), newValue)
            cp.write(open(conf.conf_file, "w"))
        
        # Credentials management
        elif os.path.dirname(name) == "/UFO/Credentials":
            if os.path.basename(name) == "Status":
                if newValue == "OK":
                    if self.remember_pass:
                        self.set_password(self.remember_pass)
                    gui.app.authentication(u"Ouverture de la session en cours...")
                    
                elif newValue == "FAILED" or newValue == "NO_PASSWORD":
                    if newValue == "FAILED" and self.keyring_valid:
                        self.set_password("")
                    gui.app.hide_balloon()
                    gui.app.normalize_window()
                    gui.app.set_tooltip(u"UFO: en cours d'authentification")
                
        # Boot progress management
        elif name == "/UFO/Boot/Progress":
            if not self.vbox.current_machine.is_booting:
                self.vbox.current_machine.is_booting = True
            gui.app.update_progress(gui.app.tray.progress, newValue)
        
        # Resolution changes management
        elif name == "/VirtualBox/GuestAdd/Vbgl/Video/SavedMode":
            # We NEVER receive last percent event,
            # so we use /VirtualBox/GuestAdd/Vbgl/Video/SavedMode event
            # raised at slim startup to catch end of oot progress
            if self.vbox.current_machine.is_booting and \
               not self.vbox.current_machine.is_booted:
                gui.app.update_progress(gui.app.tray.progress, str("1.000"))
                gui.app.authentication(u"Authentification en cours...")
                self.vbox.current_machine.is_booted = True
                
        # Overlay data reintegration infos
        elif name == "/UFO/Overlay/Size":
            self.vbox.current_machine.overlay_data_size = int(newValue)
            
        # Custom machine state management
        elif name == "/UFO/State":
            if newValue == "LOGGED_IN":
                # Start usb check loop
                gui.app.start_usb_check_timer(5, self.check_usb_devices)

                gui.app.hide_balloon()
                gui.app.fullscreen_window(False)
                gui.app.set_tooltip(u"UFO: en cours d'exécution")
                
            elif newValue == "CLOSING_SESSION":
                gui.app.minimize_window()
                gui.app.show_balloon_message(title=u"Sauvegarde des données", 
                                             msg=u"UFO est en train d'enregistrer les modifications du système (" + 
                                                 str(self.vbox.current_machine.overlay_data_size) + 
                                                 u" méga-octets),\nne débranchez surtout pas la clé !")
                gui.app.set_tooltip("UFO: en cours de sauvegarde")
            
            elif newValue == "HALTING":
                pass
                
            elif newValue == "REBOOTING":
                
                self.vbox.current_machine.is_booted  = False
                self.vbox.current_machine.is_booting = True
                
                # Let's show virtual machine's splash screen 2s,
                # minimize window while booting
                time.sleep(2)
                gui.app.hide_balloon()
                gui.app.show_balloon_progress(title=u"Redémarrage de UFO",
                                              msg=u"UFO est en cours de redémarrage.")
        
            elif newValue == "FIRSTBOOT":
                gui.app.fullscreen_window(False)
                
        # Fullscreen management
        elif name == "/UFO/GUI/Fullscreen":
            if newValue == "1":
                gui.app.fullscreen_window(True)
            else:
                gui.app.fullscreen_window(False)

    def onMachineStateChange(self, state):

        last_state = self.vbox.current_machine.last_state
        if state == self.vbox.constants.MachineState_Running and \
           last_state == self.vbox.constants.MachineState_Starting:
            
            # Let's show virtual machine's splash screen 2s,
            # minimize window while booting
            time.sleep(2)
            gui.app.minimize_window()
            if conf.USER != "":
                title = u"Démarrage de UFO"
            else:
                title = u"1<SUP>er</SUP> démarrage de UFO"
            gui.app.show_balloon_progress(title=title,
                                          msg=u"UFO est en cours de démarrage.",
                                          credentials_cb=self.credentials,
                                          credentials=self.keyring_valid)
            
            gui.app.set_tooltip(u"UFO: en cours de démarrage")
            
        elif state == self.vbox.constants.MachineState_PoweredOff and \
             (last_state == self.vbox.constants.MachineState_Stopping or \
              last_state == self.vbox.constants.MachineState_Aborted):
            
            if gui.app.usb_check_timer:
                gui.app.stop_usb_check_timer()
            if gui.app.callbacks_timer:
                gui.app.stop_callbacks_timer()

            gui.app.hide_balloon()
            gui.app.set_tooltip(u"UFO: terminé")
            gui.app.show_balloon_message(u"Au revoir", 
                                         u"Vous pouvez éjecter votre clé UFO en toute securité.")

            # Let's show ballon message 3s
            time.sleep(3)
            gui.app.hide_balloon()
            
            # main loop end condition
            self.vbox.current_machine.is_finished = True
            
        self.vbox.current_machine.last_state = state

    def set_credentials(self, password, remember=False):
        logging.debug("Settings guest credentials")
        self.vbox.current_machine.set_guest_property("/UFO/Credentials/AuthTok",
                                                     unicode(password))
        if remember:
            self.remember_pass = password
        
    def set_password(self, password):
        try:
            logging.debug("Storing password in the keyring")
            keyring.set_password("UFO", conf.USER, str(password))
        except: 
            logging.debug("import keyring failed, (keyring.set_password)!")

    def get_password(self):
        try:
            logging.debug("Get credentials")
            return keyring.get_password("UFO", conf.USER)
        except: 
            logging.debug("import keyring failed, (keyring.get_password)!")

    def wait_for_termination(self):
        # Destroy our own splash screen
        self.destroy_splash_screen()
        
        # As virtualbox < 3.0.0 do not provides 
        # callbacks, we pool on virtual machine's properties
        # and call corresponding callback method
        if not self.vbox.callbacks_aware:
            gui.app.start_callbacks_timer(1, self.vbox.minimal_callbacks_maker_loop)

        # Special case when Qt backend unavailale and virtualbox < 3.0.0,
        # in this case we are not able to catch termination
        if gui.backend != "PyQt":
            sys.exit(1)

        # As we use waitForEvents(interval) from vboxapi,
        # we are not able to use another type of loop, as 
        # Qt one, because we d'ont receive any vbox callbacks
        # ones the other loop is stated.
        #
        # So we handle Qt events ourself with the configurable
        # following interval value (default: 50ms)
        while not self.vbox.current_machine.is_finished:
            self.wait_for_events(0.05)

    def wait_for_events(self, interval):
        # This function is overloaded only on Windows
        if self.vbox.callbacks_aware:
            self.vbox.vm_manager.waitForEvents(int(interval * 1000))
        else:
            time.sleep(interval)

        gui.app.process_gui_events()

    def check_usb_devices(self):
        # manage removable media shared folders
        usb_devices = self.get_usb_devices()
        for usb in usb_devices:
            if usb[1] == None:
                continue
            if usb in self.usb_devices:
                continue
            if self.vbox.callbacks_aware:
                guest_prop_type = "/UFO/Com/HostToGuest/Shares/AskToUser/"
                gui.app.show_balloon_message(u"Nouveau périphérique USB", 
                                             u'"' + str(usb[1]) + 
                                             u'", vous pouvez relier ce nouveau périphérique à votre bureau UFO.', 5000)
            else:
                guest_prop_type = "/UFO/Com/HostToGuest/Shares/ReadyToMount/"
                self.vbox.current_machine.add_shared_folder(str(usb[1]), str(usb[0]), writable = True)
                
            self.vbox.current_machine.set_guest_property(guest_prop_type + str(usb[1]),
                                                         str(usb[1]) + ";" + str(usb[0]))
        for usb in self.usb_devices:
            if usb in usb_devices:
                continue
            if self.vbox.callbacks_aware:
                self.vbox.current_machine.remove_shared_folder(str(usb[1]))
            
            self.vbox.current_machine.set_guest_property("/UFO/Com/HostToGuest/Shares/Remove/" + str(usb[1]),
                                                         str(usb[0]))
        self.usb_devices = usb_devices

    def run_virtual_machine(self, env):
        if conf.STARTVM:
            self.vbox.current_machine.start()
        else:
            self.run_vbox(path.join(conf.BIN, "VirtualBox"), env)

    def remove_settings_files(self):
        if os.path.exists(path.join(conf.HOME, "VirtualBox.xml")):
            os.unlink(path.join(conf.HOME, "VirtualBox.xml"))
        if os.path.exists(path.join(conf.HOME, "Machines")):
            shutil.rmtree(path.join(conf.HOME, "Machines"))

    def global_cleanup(self):
        if self.vbox.license_agreed():
            cp = ConfigParser()
            cp.read(conf.conf_file)
            cp.set("launcher", "LICENSE", "1")
            cp.write(open(conf.conf_file, "w"))
        if self.dnddir:
            shutil.rmtree(self.dnddir)
        if self.tmp_swapdir:
            os.unlink(path.join(self.tmp_swapdir, path.basename(conf.SWAPFILE)))
        if self.tmp_overlaydir:
            os.unlink(path.join(self.tmp_overlaydir, path.basename(conf.OVERLAYFILE)))

        logging.debug("Cleaning VBoxHypervisor")
        try:
            self.vbox.cleanup()
            del self.vbox
        except: 
            pass
        self.kill_resilient_vbox()
        self.cleanup()

    def run(self):
        logging.debug("BIN path: " + conf.BIN)
        logging.debug("HOME path: " + conf.HOME)

        # prepare environement
        logging.debug("Preparing environment")
        self.prepare()
        self.create_splash_screen()
        self.checking_pyqt()
        self.look_for_virtualbox()
        self.remove_settings_files()

        logging.debug("Initializing vbox and graphics")
        self.init_vbox_hypervisor()
        gui.app.initialize(self.vbox)
        
        # generate raw vmdk for usb key
        create_vmdk = False
        logging.debug("Searching device...")
        ret = self.find_device()
        if ret == conf.STATUS_NORMAL:
            logging.debug("awaited device found on " + str(conf.DEV))
            if self.prepare_device(conf.DEV):
                sys.exit(1)
            create_vmdk = True
            
        elif ret == conf.STATUS_IGNORE:
            logging.debug("no vmdk generation needed")
            
        elif ret == conf.STATUS_EXIT:
            logging.debug("no device found, do not start machine")
            sys.exit(1)
        
        # build virtual machine as host capabilities
        logging.debug("Creating virtual machine")
        self.create_virtual_machine()
        self.configure_virtual_machine(create_vmdk = create_vmdk)

        # launch vm
        logging.debug("Launching virtual machine")
        self.run_virtual_machine(self.env)
        self.wait_for_termination()

        # clean environement
        logging.debug("Clean up")
        self.global_cleanup()

