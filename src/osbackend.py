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


import glob
import os.path as path
import createrawvmdk
from conf import conf
import tempfile
import gui
import time
import shutil
import platform
import utils
from ufovboxapi import *
from ConfigParser import ConfigParser
from utils import RoolOverLogger

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

    log_black_list = [ "/UFO/DiskSpace", "/UFO/Debug", "/UFO/Credentials/AuthTok", "/UFO/Boot/Progress" ]

    def __init__(self, os_backend):
        VBoxMonitor.__init__(self)
        self.os_backend = os_backend
        
    def onGuestPropertyChange(self, id, name, newValue, flags):
        if name not in self.log_black_list and \
           os.path.dirname(name) not in self.log_black_list:
            logging.debug("Guest property: %s -> %s" % (name, newValue))
        if self.os_backend.vbox.current_machine.uuid == id:
            self.os_backend.onGuestPropertyChange(name, newValue, flags)
            
    def onMachineStateChange(self, id, state):
        logging.debug("Machine state changed: %d => %d" %(self.os_backend.vbox.current_machine.last_state, state))

        if self.os_backend.vbox.current_machine.uuid == id:
            self.os_backend.onMachineStateChange(state)
            
    def onExtraDataCanChange(self, id, key, value):
        return self.os_backend.onExtraDataCanChange(key, value)


class OSBackend(object):
    def __init__(self, os_name):
        self.tmp_swapdir    = ""
        self.tmp_overlaydir = ""
        self.vbox_install   = ""
        self.debug_reports  = {}
        self.vbox           = None
        self.puel           = False
        self.splash         = None
        self.credentials    = None
        self.keyring_valid  = False
        self.remember_pass  = None
        self.os_name        = os_name
        self.eject_at_exit  = conf.EJECTATEXIT
        self.env            = self.update_env()

        if conf.VOICE:
            import voice
            self.voice = voice.create_voice_synthetizer()
        else:
            self.voice = None

        self.growing_data_files = [ "settings/settings.conf",
                                    ".VirtualBox/VirtualBox.xml",
                                    ".VirtualBox/compreg.dat",
                                    ".VirtualBox/xpti.dat",
                                    ".VirtualBox/Machines/UFO/UFO.xml",
                                    ".VirtualBox/Machines/UFO/Logs/VBox.log"
                                  ]
        self.reservation_file   = "reservationfile"
        self.reservation_size   = 512000

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
        self.vbox.current_machine.set_network_adapter(adapter_type = self.vbox.constants.NetworkAdapterType_I82540EM)
        self.vbox.current_machine.disable_boot_menu()
        self.vbox.current_machine.set_audio_adapter(self.get_default_audio_driver())

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
                                 "showRuntimeError.warning.HostAudioNotResponding," +
                                 "showRuntimeError.warning.3DSupportIncompatibleAdditions")

        if not conf.MENUBAR:
            self.vbox.set_extra_data("GUI/Customizations", "noMenuBar")
            self.vbox.set_extra_data("GUI/ShowMiniToolBar", "no")
            
        self.vbox.current_machine.set_extra_data("GUI/SaveMountedAtRuntime", "false")
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
        if conf.ROOTVDI:
            self.vbox.current_machine.attach_harddisk(conf.ROOTVDI, conf.DRIVERANK)

        elif conf.VMDK and create_vmdk:
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
            if conf.RAMSIZE == conf.AUTO_INTEGER:
                if self.vbox.vbox_version() >= "2.1.0":
                    freeram = self.vbox.host.get_free_ram()
                else:
                    freeram = self.get_free_ram()
                ram = max(2 * freeram / 3, conf.MINRAM)
            else:
                ram = conf.RAMSIZE
                
            if int(ram) <= int(conf.MINRAM):
                gui.dialog_info(title=_("Warning"), 
                                msg=_("The available memory on this computer is low.\n"
                                      "This can deeply impact the speed of the UFO virtual machine.\n\n"
                                      "Closing some applications or restarting the computer may help"),
                                error=False)
        
            logging.debug("Setting RAM to " + str(ram))
            self.vbox.current_machine.set_ram_size(ram)
            
            # Set number of processors
            if self.vbox.vbox_version() >= "3.0.0" and self.vbox.host.is_virt_ex_available():
                logging.debug("Settings CPU capabilities: VT=%s PAE=%s nested_paging=%s" % \
                              (conf.PAE, conf.VT, conf.NESTEDPAGING))
                self.vbox.current_machine.set_cpu_capabilities(PAE=conf.PAE, VT=conf.VT,
                                                               nested_paging=conf.NESTEDPAGING)
                if conf.CPUS == conf.AUTO_INTEGER:
                    nbprocs = int(self.vbox.host.get_nb_procs())
                    logging.debug(str(nbprocs) + " processor(s) available on host")
                    if nbprocs >= 2:
                        nbprocs = max(2, nbprocs / 2)
                else:
                    try:
                        nbprocs = conf.CPUS
                    except:
                        nbprocs = 1
                logging.debug("Setting number of processor to " + str(nbprocs))
                self.vbox.current_machine.set_procs(nbprocs)

            # Set 3D acceleration
            self.vbox.current_machine.enable_3D(conf.ACCEL3D and self.vbox.supports_3D())
            
            # check host network adapter
            conf.NETTYPE, adpt_name = self.find_network_device()
            if conf.NETTYPE == conf.NET_NAT:
                attach_type = self.vbox.constants.NetworkAttachmentType_Null
                host_adapter = ''
                logging.debug(conf.SCRIPT_NAME + ": using nat networking")

            elif conf.NETTYPE == conf.NET_HOST:
                attach_type = self.vbox.constants.NetworkAttachmentType_Bridged
                host_adapter = adpt_name
                logging.debug("Using net bridge on " + adpt_name)

            self.vbox.current_machine.set_network_adapter(attach_type  = attach_type,
                                                          host_adapter = host_adapter,
                                                          mac_address  = conf.MACADDR)

            if conf.MACADDR == "":
                conf.write_value_to_file("vm", "macaddr", self.vbox.current_machine.get_mac_addr())

            for protocol in [ "HTTP", "HTTPS", "FTP", "SOCKS" ]:
                proxy, port = "", 0
                confvalue = getattr(conf, "PROXY" + protocol)
                if confvalue == conf.AUTO_STRING:
                    if protocol != "socks":
                        value = self.get_proxy(protocol + "://agorabox.org")
                        if value: proxy, port = value
                else:
                    proxy, port = confvalue.split(":")
                if proxy and port:
                    setattr(conf, "PROXY" + protocol, "%s:%d" % (proxy, int(port)))

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
                self.vbox.current_machine.attach_dvd(host_drive = True, blacklist=["UFO"])

            if conf.LIVECD or not conf.BOOTISO and not conf.BOOTFLOPPY:
                logging.debug("Using hard disk for booting")
                self.vbox.current_machine.set_boot_device('HardDisk') 
                
            if conf.LIVECD:
                logging.debug("Setting bootdisk %s for Live CD at rank %d" % (conf.BOOTDISK, conf.DRIVERANK,))
                self.vbox.current_machine.attach_harddisk(conf.BOOTDISK, conf.DRIVERANK)
            
            if conf.RESOLUTION:
                self.fullscreen = False
                resolution = conf.RESOLUTION
                hostres = self.find_resolution()
                if hostres != "" and \
                    (int(hostres.split("x")[0]) <= int(conf.RESOLUTION.split("x")[0]) or \
                     int(hostres.split("x")[1]) <= int(conf.RESOLUTION.split("x")[1])):
                    resolution = hostres
                    self.fullscreen = True
                if resolution != "":
                    logging.debug("Using " + resolution + " as initial resolution")
                    self.vbox.current_machine.set_resolution(resolution)

            self.vbox.current_machine.set_boot_logo(glob.glob(path.join(conf.IMGDIR, "ufo-*.bmp"))[0])

            # set host home shared folder
            if not conf.USESERVICE:
                for host_share in self.get_host_shares():
                    self.vbox.current_machine.add_shared_folder(host_share['sharename'],
                                                                host_share['sharepath'],
                                                                writable = True)
                    self.vbox.current_machine.set_guest_property("/UFO/Com/HostToGuest/Shares/ReadyToMount/" +
                                                                 host_share['sharename'],
                                                                 host_share['displayed'])
                    logging.debug("Setting shared folder : %s, %s" %
                                  (host_share['sharepath'], host_share['displayed']))
                
                self.dnddir = tempfile.mkdtemp(suffix="ufodnd")
                self.vbox.current_machine.add_shared_folder("DnD", self.dnddir, writable = True)
                logging.debug("Setting shared folder : " + self.dnddir + ", DnD")

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

        # manage password keyring
        if keyring:
            if conf.USER:
                password = self.get_password()
                if password:
                    self.keyring_valid = True
                    self.set_credentials(conf.USER, password)
                else:
                    logging.debug("Found no credentials")
        else:
            self.keyring_valid = None

        self.credentials = self.set_credentials
        
        # build removable devices attachments
        self.check_usb_devices()

        # set debug mode
        if conf.GUESTDEBUG:
            self.vbox.current_machine.set_guest_property("/UFO/Debug", "1")
            gui.dialog_info(msg=_("UFO is running in debug mode.\n"
                                  "Be aware to disable debug mode at the next session."),
                            title=_("Debug mode"))

        for guestprop in conf.get_all_guestprops():
            self.vbox.current_machine.set_guest_property(guestprop.get_name(),
                                                         guestprop.get_value())

        self.vbox.close_session()

    def build_command_line(self):
        cmdline = conf.CMDLINE.split(" ")
        if not conf.GUESTDEBUG:
            cmdline += [ "rhgb", "quiet" ]
        logging.debug("conf.REINTEGRATION: " + conf.REINTEGRATION)
        cmdline.append(conf.REINTEGRATION)
        cmdline.append(self.get_i18n_cmdline())
        if conf.COMPRESS:
            cmdline.append("rootflags=compress")
        cmdline.append("hostos=" + self.os_name)
        return " ".join(cmdline)

    def set_command_line(self):
        cmdline = self.build_command_line()
        logging.debug("conf.CMDLINE: " + cmdline)
        self.vbox.current_machine.set_guest_property("/UFO/CommandLine", cmdline)

    def check_usb_devices(self):
        old_attachmnts = self.vbox.current_machine.usb_attachmnts.copy()

        # adding new devices, and tracking removed ones...
        for usb in self.get_usb_devices():
            if not str(usb[1]).endswith("None"):
                if conf.SCRIPT_PATH.startswith(usb[0]):

                    # handle our fat partition
                    if not self.vbox.current_machine.usb_master:
                        name = str(usb[1])
                        if name.find(':_') != -1:
                            name = name.split(':_')[1]
                        self.vbox.current_machine.usb_master = { 'name' : "UFO", 'path' : usb[0] }
                        self.vbox.current_machine.attach_usb(self.vbox.current_machine.usb_master)

                elif self.vbox.current_machine.usb_attachmnts.has_key(usb[1]):
                    del old_attachmnts[usb[1]]

                else:
                    self.vbox.current_machine.usb_attachmnts[usb[1]] = { 'name'   : usb[1],
                                                                         'path'   : usb[0],
                                                                         'attach' : False }
        # ...and so remove them
        for removed in old_attachmnts.keys():
            del self.vbox.current_machine.usb_attachmnts[removed]

    def find_device(self):
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
            if conf.VOLUME != conf.get_default_value("volume"):
                conf.DEV = self.find_device_by_volume(conf.VOLUME)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
            if conf.MODEL:
                conf.DEV = self.find_device_by_model(conf.MODEL)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
            if not conf.LIVECD:
                conf.DEV = self.find_device_by_path(conf.SCRIPT_PATH)
                if conf.DEV != "":
                    return conf.STATUS_NORMAL
                
                input = gui.dialog_question(title=_("Warning"),
                                            msg=_("Could not find an UFO key, try again ?"),
                                            button1=_("Yes"),
                                            button2=_("No"))
                if input == _("No"):
                    if conf.NEEDDEV: return conf.STATUS_EXIT
                    return conf.STATUS_EXIT
            else:
                usb = self.get_usb_sticks()
                names = [ x[1] for x in usb ]
                if not names:
                    names = [ _("No USB device found") ]
                ret = gui.dialog_choices(msg=_("Select the USB device you want to install UFO on"),
                                         title="UFO", column=_("Device"), choices=names)
                if not ret:
                    return conf.STATUS_IGNORE
                    
                conf.DEV = usb[ret - 1][0]
                return conf.STATUS_NORMAL
                
            try_times -= 1

        return conf.STATUS_EXIT

    def get_i18n_cmdline(self):
        return "LANG=%s.UTF-8 " \
               "SYSFONT=latarcyrheb-sun16 KEYBOARDTYPE=pc " \
               "KEYTABLE=%s" % (conf.LANGUAGE, self.get_keyboard_layout())

    def get_keyboard_layout(self):
        lang = str(gui.app.keyboardInputLocale().name())
        if lang == 'C':
            lang = conf.LANGUAGE
        try:
            return lang.split('_')[1].lower()
        except IndexError:
            return "us"

    def get_proxy(self, url="http://www.agorabox.org"):
        try:
            from PyQt4.QtNetwork import QNetworkProxyQuery, QNetworkProxyFactory
            from PyQt4.QtCore import QUrl

            query = QNetworkProxyQuery(QUrl(url))
            proxies = QNetworkProxyFactory.systemProxyForQuery(query)
            if proxies and proxies[0].hostName():
                return str(proxies[0].hostName()), proxies[0].port()
        except:
            logging.debug("Could not detect proxies")

    def checking_pyqt(self):
        logging.debug("Checking PyQt")

    def error_already_running(self, processes, prog="UFO"):
        logging.debug("U.F.O launched twice. Exiting")
        return gui.dialog_error_report(title=_("UFO can not be launched"),
                                       msg=_("An already running of instance %s has been found.\n"
                                             "Please close all %s windows and processes.") % (prog, prog),
                                       action=_("Force to close"), details = processes)

    def look_for_virtualbox(self):
        # Check virtualbox binaries
        logging.debug("Checking VirtualBox binaries")
        if not path.exists(path.join(conf.BIN, self.VIRTUALBOX_EXECUTABLE)):
            logging.debug("Missing binaries in " + conf.BIN)
            gui.dialog_info(msg=_("The VirtualBox binaries could not be found"),
                            title=_("Missing binaries"))
            sys.exit(1)

    def installed_vbox_error(self):
        msg = _("We have detected an existing VirtualBox installation on this computer.\n"
                "UFO is not compatible with this version of VirtualBox, please remove this VirtualBox installation to run UFO.\n\n"
                "Note that if you want to use your own VirtualBox installation, you need to reboot your computer.")
        gui.dialog_info(title=_("VirtualBox detected"), msg=msg)
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
            conf.write_value_to_file("guest", os.path.basename(name), newValue)

        # Disk space management
        elif os.path.dirname(name) == "/UFO/DiskSpace":
            gui.app.update_disk_space_progress(os.path.basename(name), newValue)

        # Credentials management
        elif os.path.dirname(name) == "/UFO/Credentials":
            if os.path.basename(name) == "Status":
                if newValue == "OK":
                    if self.remember_pass:
                        self.set_password(self.remember_pass)
                    gui.app.update_temporary_balloon(msg=_("Opening session..."))
                    
                elif newValue == "FAILED" or newValue == "NO_PASSWORD":
                    if newValue == "FAILED" and self.keyring_valid:
                        self.set_password("")
                    gui.app.destroy_temporary_balloon()

                    if self.fullscreen:
                        gui.app.fullscreen_window(False)
                    else:
                        gui.app.normalize_window()
                    gui.app.set_tooltip(_("UFO: authenticating"))

        # Boot progress management
        elif name == "/UFO/Boot/Progress":
            gui.app.update_temporary_balloon(progress=float(newValue))

        # Resolution changes management
        elif name == "/VirtualBox/GuestAdd/Vbgl/Video/SavedMode":
            # We NEVER receive last percent event,
            # so we use /VirtualBox/GuestAdd/Vbgl/Video/SavedMode event
            # raised at slim startup to catch end of boot progress
            if self.vbox.current_machine.is_booting and \
               not self.vbox.current_machine.is_booted:

                gui.app.update_temporary_balloon(progress=1.00, msg=_("Authenticating..."))
                self.vbox.current_machine.is_booted = True

        # Overlay data reintegration infos
        elif name == "/UFO/Overlay/Size":
            self.vbox.current_machine.overlay_data_size = int(newValue)

        # Custom machine state management
        elif name == "/UFO/State":
            if newValue == "LOGGED_IN":
                # Start usb check loop
                gui.app.destroy_temporary_balloon()
                gui.app.add_persistent_balloon_section(key='usb',
                                                       msg=_("Removable devices management:"),
                                                       default=_("No removable devices found"),
                                                       progress=False,
                                                       smartdict=self.vbox.current_machine.usb_attachmnts,
                                                       hlayout={ 'type' : gui.UsbAttachementLayout,
                                                                 'args' : (self.vbox.current_machine.attach_usb,)})

                gui.app.start_check_timer(gui.app.usb_check_timer, 5, self.check_usb_devices)

                if conf.AUTOFULLSCREEN or self.fullscreen:
                    gui.app.fullscreen_window(False)
                else:
                    gui.app.normalize_window()
                gui.app.set_tooltip(_("UFO: running"))
                
            elif newValue == "CLOSING_SESSION":
                gui.app.destroy_persistent_balloon_section('usb')

                if conf.AUTOMINIMIZE:
                    gui.app.minimize_window()

                if self.vbox.current_machine.overlay_data_size > 0:
                    title = _("Recording changes")
                    msg = _("Please wait while UFO is recording the system modifications (%s Mo),\n"
                            "you absolutely must not unplug the key !") % (str(self.vbox.current_machine.overlay_data_size),)
                else:
                    title = _("Shutting down")
                    msg = _("Please wait while UFO is shutting down,\n"
                            "you absolutely must not unplug the key !")

                gui.app.create_temporary_balloon(title=title, msg=msg)
                gui.app.set_tooltip(_("UFO: recording changes"))
            
            elif newValue == "HALTING":
                pass
                
            elif newValue == "REBOOTING":
                self.set_command_line()
                self.vbox.current_machine.is_booted  = False
                self.vbox.current_machine.is_booting = True
                gui.app.create_temporary_balloon(title=_("Restart UFO"),
                                                 msg=_("UFO is rebooting"),
                                                 progress=True)
        
            elif newValue == "FIRSTBOOT":
                gui.app.fullscreen_window(False)

        # Fullscreen management
        elif name == "/UFO/GUI/Fullscreen":
            if newValue == "1":
                gui.app.fullscreen_window(True)
            else:
                gui.app.fullscreen_window(False)

        # Debug management
        elif "/UFO/Debug/" in name:
            debug = os.path.basename(name)
            if not self.debug_reports.has_key(debug):
                self.debug_reports[debug] = RoolOverLogger(conf.LOGFILE + "_" + debug, 1)

            self.debug_reports[debug].safe_debug(newValue)

        elif name == "/UFO/EjectAtExit":
            self.eject_at_exit = int(newValue)

    def onMachineStateChange(self, state):
        last_state = self.vbox.current_machine.last_state
        
        # The virtual machine is starting
        if state == self.vbox.constants.MachineState_Running and \
           last_state == self.vbox.constants.MachineState_Starting:

            self.set_command_line()

            # Let's show virtual machine's splash screen 2s,
            # minimize window while booting
            if conf.AUTOMINIMIZE:
                time.sleep(2)
                gui.app.minimize_window()
                
            if conf.USER != "" or conf.GUESTMODE:
                title = _(u"UFO is starting")
            else:
                title = _("1<SUP>st</SUP> launch of UFO")

            gui.app.create_temporary_balloon(title=title,
                                             msg=_("UFO is starting."),
                                             progress=True,
                                             vlayout={ 'type' : gui.CredentialsLayout,
                                                       'args' : (self.credentials, self.keyring_valid)})
            gui.app.set_tooltip(_("UFO: starting"))

            self.vbox.current_machine.is_booting = True
        
        # The virtual machine is stopping
        elif (state == self.vbox.constants.MachineState_PoweredOff and \
              last_state == self.vbox.constants.MachineState_Stopping) or \
              state == self.vbox.constants.MachineState_Aborted:

            gui.app.destroy_persistent_balloon_sections()

            if gui.app.usb_check_timer.isActive():
                gui.app.stop_check_timer(gui.app.usb_check_timer)
            if gui.app.net_adapt_timer.isActive():
                gui.app.stop_check_timer(gui.app.net_adapt_timer)
            if gui.app.callbacks_timer.isActive():
                gui.app.stop_check_timer(gui.app.callbacks_timer)

            gui.app.set_tooltip(_("UFO: terminated"))
            gui.app.process_gui_events()
            gui.app.create_temporary_balloon(_("Goodbye"),
                                             _("You can now safely eject your UFO key."))
                                             
            gui.app.start_single_timer(gui.app.termination_timer, 3, self.termination_callback)
        
        self.vbox.current_machine.last_state = state

    def set_credentials(self, username, password, remember=False):
        logging.debug("Settings guest credentials")
        self.vbox.current_machine.set_guest_property("/UFO/Credentials/Username",
                                                     username)
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

    def termination_callback(self):
        gui.app.destroy_temporary_balloon()
        
        # main loop end condition
        self.vbox.current_machine.is_finished = True
            
    def wait_for_termination(self):
        # Destroy our own splash screen
        self.destroy_splash_screen()
        
        # As virtualbox < 3.0.0 do not provides 
        # callbacks, we pool on virtual machine's properties
        # and call corresponding callback method
        if not self.vbox.callbacks_aware:

            # Special case when Qt backend unavailable and virtualbox < 3.0.0,
            # in this case we are not able to catch termination
            if gui.backend != "PyQt":
                sys.exit(1)

            gui.app.start_check_timer(gui.app.callbacks_timer, 1, self.vbox.minimal_callbacks_maker_loop)

        gui.app.start_check_timer(gui.app.net_adapt_timer, 5, self.vbox.check_network_adapters)
        
        # As we use waitForEvents(interval) from vboxapi,
        # we are not able to use another type of loop, as 
        # Qt one, because we d'ont receive any vbox callbacks
        # ones the other loop is stated.
        #
        # So we handle Qt events ourself with the configurable
        # following interval value (default: 10ms)
        while not self.vbox.current_machine.is_finished:
            self.wait_for_events(0.01)

    def wait_for_events(self, interval):
        # This function is overloaded only on Windows
        if self.vbox.callbacks_aware:
            self.vbox.vm_manager.waitForEvents(int(interval * 1000))
        else:
            time.sleep(interval)

        gui.app.process_gui_events()

    def find_device_by_path(self, path):
        usbs = self.get_usb_devices()
        for usb in usbs:
            if path.startswith(usb[0]):
                return usb[2]
        return ""

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
        if os.path.exists(path.join(conf.DATA_DIR, self.reservation_file)):
            os.unlink(path.join(conf.DATA_DIR, self.reservation_file))

    def reserve_disk_space(self):
        used = 0
        for growing_file in self.growing_data_files:
            if os.path.exists(path.join(conf.DATA_DIR, growing_file)):
                used = used + os.stat(path.join(conf.DATA_DIR, growing_file)).st_size

        size_to_reserve = self.reservation_size - used
        available_size = utils.get_free_space(conf.DATA_DIR)

        if size_to_reserve > available_size:
            size_to_reserve = available_size

        open(path.join(conf.DATA_DIR, self.reservation_file), 'a').truncate(size_to_reserve)

    def global_cleanup(self):
        if self.vbox.license_agreed():
            conf.write_value_to_file("launcher", "LICENSE", "1")
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

        # prepare environment
        logging.debug("Preparing environment")
        self.prepare()
        self.create_splash_screen()
        self.checking_pyqt()
        self.look_for_virtualbox()
        self.remove_settings_files()

        logging.debug("Initializing vbox and graphics")
        self.init_vbox_hypervisor()
        gui.app.initialize(self.vbox, self)
        
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
        self.reserve_disk_space()

        # launch vm
        logging.debug("Launching virtual machine")
        self.run_virtual_machine(self.env)
        self.wait_for_termination()

        # clean environment
        logging.debug("Clean up")
        self.global_cleanup()
