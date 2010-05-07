#!/usr/bin/env python
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


import os
import uuid as uuid_lib
import traceback
import logging
import time
import sys

from utils import SmartDict

try:
    import pywintypes
    COMError = pywintypes.com_error
except:
    COMError = Exception


class VBoxInterfaceWrapper:
    def __init__(self, machine):
        self.__dict__["machine"] = machine
                
    def __getattr__(self, name):
        return getattr(self.__dict__["machine"], name[0].upper() + name[1:])

    def __setattr__(self, name, value):
        return setattr(self.__dict__["machine"], name[0].upper() + name[1:])


class VBoxConstantsWrapper:
    
    """
    Here is a special wrapper method to link machine state 
    constants to proper ones when old version of virtualbox is used.
    (It should be useful on linux host only, as we provide 
    proper virtualbox version on Mac-intel and Windows hosts)
    """
    
    old_constants = {'MachineState_Null':0,
                     'MachineState_PoweredOff':1,
                     'MachineState_Saved':2,
                     'MachineState_Aborted':3,
                     'MachineState_Running':4,
                     'MachineState_Paused':5,
                     'MachineState_Stuck':6,
                     'MachineState_Starting':7,
                     'MachineState_Stopping':8 }

    def __init__(self, version):
        from vboxapi import VirtualBoxReflectionInfo
        self.constants = VirtualBoxReflectionInfo(False)
        self.version   = version
        self._Values   = self.constants._Values
        
    def __getattr__(self, attr):
        
        """
        The following code need to be updated when a new version of the
        VirtualBox_constants file is used.
        Current version: 3.1.*
        """
        
        if self.version < "3.1.0" and attr in self.old_constants:
            return self.old_constants[attr]
        
        return self.constants.__getattr__(attr)

class VBoxHypervisor():
                        
    def __init__(self, vbox_callback_class=None, vbox_callback_arg=None):
        from vboxapi import VirtualBoxManager

        self.current_machine = None
        self.session         = None
        self.cleaned         = False
        self.network         = False
        
        self.vm_manager = VirtualBoxManager(None, None)
        self.mgr        = self.vm_manager.mgr
        self.vbox       = self.vm_manager.vbox
        self.constants  = VBoxConstantsWrapper(self.vbox_version())
        
        self.host = VBoxHost(self.vm_manager.vbox.host, self.constants)
        
        if self.vbox_version() >= "3.0.0" and vbox_callback_class:
            self.cb = self.vm_manager.createCallback('IVirtualBoxCallback',
                                                     vbox_callback_class,
                                                     vbox_callback_arg)
            self.vbox.registerCallback(self.cb)
            self.callbacks_aware = True

        else:
            self.guest_props = {}
            self.vbox_callback_obj = vbox_callback_class(vbox_callback_arg)
            self.callbacks_aware = False
            
        if hasattr(self.vbox, "saveSettings"):
            self.vbox.saveSettings()
    
    def __del__(self):
        logging.debug("Destroying VBoxHypervisor")
        if not self.cleaned:
            self.cleanup()
        if self.current_machine:
            del self.current_machine
            self.current_machine = None
        if hasattr(self.vbox, "saveSettings"):
            self.vbox.saveSettings()
        self.vm_manager.deinit()
        del self.vm_manager

    def vbox_version(self):
        return self.vbox.version.split("_")[0]
    
    def is_vbox_OSE(self):
        version = self.vbox.version.split("_")
        if len(version) > 1:
            return version[1] == "OSE"
        return False
    
    def cleanup(self):
        if self.callbacks_aware:
            logging.debug("Unregistering VirtualBox callbacks")
            self.vbox.unregisterCallback(self.cb)
        self.cleaned = True

    def create_machine(self, machine_name, os_type, base_dir=''):
        if self.vbox_version() < "2.1.0" and os_type == "Fedora":
            os_type = "fedoracore"
        try:
            self.vbox.getGuestOSType(os_type)
        except Exception, e:
            logging.debug("Unknown OS type: " + os_type)
            return 1
        try:
            if self.vbox_version() >= "2.1.0":
                self.vbox.registerMachine(
                    self.vbox.createMachine(machine_name, os_type, base_dir, 
                                            "00000000-0000-0000-0000-000000000000"))
            else:
                if base_dir == '':
                    base_dir = 'Machines'
                machine = self.vbox.createMachine(base_dir, machine_name,
                                                  "00000000-0000-0000-0000-000000000000")
                machine.OSTypeId = os_type
                self.vbox.registerMachine(machine)         
        except Exception, e:
            logging.debug(e)
            return 1
        return 0

    def open_machine(self, machine_name):
        for machine in self.get_machines():
            if machine.name == machine_name:
                self.session = self.vm_manager.openMachineSession(machine.id)
                self.current_machine = VBoxMachine(self, self.session.machine)
                return 0
        return 1
    
    def close_session(self):
        self.current_machine.machine.saveSettings()
        if hasattr(self.vbox, "saveSettings"):
            self.vbox.saveSettings()
        if self.session == None:
            return 1
        self.session.close()
        self.session = None
        return 0

    def close_machine(self):
        if self.session != None:
            self.session.close()
            self.session = None
        del self.current_machine
        self.current_machine = None
        return 0

    def get_machines(self):
        if self.vbox_version() < "2.2.0":
            attr = 'machines2'
        else:
            attr = 'machines'
        return self.vm_manager.getArray(self.vm_manager.vbox, attr)

    def find(self, location, type):
        prop = type[0].lower() + type[1:] + "s"
        if hasattr(self.vbox, prop):
            for obj in getattr(self.vbox, prop):
                if obj.location == location:
                    return obj
        else:
            try:
                return getattr(self.vbox, "find" + type[0].upper() + type[1:])(location)
            except:
                return None
                
    def find_disk(self, location):
        return self.find(location, "hardDisk")

    def find_floppy(self, location):
        return self.find(location, "floppyImage")
        
    def find_dvd(self, location):
        return self.find(location, "DVDImage")
        
    def add_harddisk(self, location):
        uuid = str(uuid_lib.uuid4())
        try:
            if self.vbox_version() >= "3.0.0":
                try:
                    disk = self.vbox.openHardDisk(location, self.constants.AccessMode_ReadOnly,
                                                  False, '', False, uuid)
                except COMError, e:
                    # Harddisk was created but it failed returning an IMedium
                    logging.debug("Got COMError exception in add_harddisk")
                    disk = self.find_disk(location)
            elif self.vbox_version() >= "2.2.0":
                disk = self.vbox.openHardDisk(location, self.constants.AccessMode_ReadOnly)
            elif self.vbox_version() >= "2.1.0":
                disk = self.vbox.openHardDisk2(location)
            else:
                disk = self.vbox.openHardDisk(location)
                self.vbox.registerHardDisk(disk)
        except Exception, e:
            logging.debug(e)
            return None
        return disk

    def add_dvd(self, location):
        uuid = str(uuid_lib.uuid4())
        try:
            try:
                dvd = self.vbox.openDVDImage(location, uuid)
            except COMError, e:
                logging.debug("Got COMError exception in add_dvd")
                dvd = self.find_dvd(location)
            if self.vbox_version() < "2.1.0":
                self.vbox.registerDVDImage(dvd)
        except Exception, e:
            logging.debug(e)
            return None
        return dvd

    def add_floppy(self, location):
        uuid = str(uuid_lib.uuid4())
        try:
            try:
                floppy = self.vbox.openFloppyImage(location, uuid)
            except COMError, e:
                # Floppy was created but it failed returning an IMedium
                logging.debug("Got COMError exception in add_floppy")
                floppy = self.find_floppy(location)
            if self.vbox_version() < "2.1.0":
                self.vbox.registerFloppyImage(floppy)
        except Exception, e:
            logging.debug(e)
            return None
        return floppy

    def set_extra_data(self, key, value, save=False):
        self.vbox.setExtraData(key, value)
        if save and hasattr(self.vbox, "saveSettings"):
            self.vbox.saveSettings()
        return 0

    def supports_3D(self):
        if self.vbox_version() < "2.1.0":
            logging.debug("This version of VirtualBox does not support 3D")
            return False
        else:
            logging.debug("Enabling 3D acceleration")
            return self.host.host.Acceleration3DAvailable

    def license_agreed(self):
        if self.vbox.getExtraData("GUI/LicenseAgreed"):
            return 1
        return 0
        
    def set_host_key(self, key):
        self.set_extra_data("GUI/Input/HostKey", str(key))

    def minimal_callbacks_maker_loop(self):
        try:
            names, values, x, x = self.current_machine.machine.enumerateGuestProperties("*")
    
            id = 0
            guest_props = {}
            while id < len(names):
                guest_props[names[id]] = values[id]

                if not self.guest_props.has_key(names[id]) or self.guest_props[names[id]] != values[id]:
                    if names[id] == "/VirtualBox/GuestAdd/Vbgl/Video/SavedMode" and not self.guest_props.has_key("/UFO/Boot/Progress"):
                        guest_props[names[id]] = "0x0x0"
                        self.current_machine.set_guest_property(names[id], guest_props[names[id]])

                    else:
                        self.vbox_callback_obj.onGuestPropertyChange(self.current_machine.uuid,
                                                                     names[id],
                                                                     guest_props[names[id]],
                                                                     "")
                id += 1
            
            self.guest_props = guest_props
            
            state = self.current_machine.machine.state
            last_state = self.current_machine.last_state
            if self.current_machine.last_state != state:
                if state == self.constants.MachineState_Running and \
                   last_state == self.constants.MachineState_PoweredOff:
                    self.vbox_callback_obj.onMachineStateChange(self.current_machine.uuid, self.constants.MachineState_Starting)
                if state == self.constants.MachineState_PoweredOff:
                    self.vbox_callback_obj.onMachineStateChange(self.current_machine.uuid, self.constants.MachineState_Stopping)
                    
                self.vbox_callback_obj.onMachineStateChange(self.current_machine.uuid, state)
        except:
            self.vbox_callback_obj.onMachineStateChange(self.current_machine.uuid, self.constants.MachineState_Stopping)
            self.vbox_callback_obj.onMachineStateChange(self.current_machine.uuid, self.constants.MachineState_PoweredOff)

    def check_network_adapters(self):
        one_least_active = self.host.is_network_active()
        if self.network != one_least_active:
            if one_least_active and \
               self.current_machine.get_network_adapter_type() == self.constants.NetworkAttachmentType_Null:
                success = self.current_machine.set_network_adapter(attach_type = self.constants.NetworkAttachmentType_NAT)
            else:
                success = self.current_machine.set_network_adapter(attach_type = self.constants.NetworkAttachmentType_Null)
            if not success:
                logging.debug("Failed setting networking to NAT")
                self.network = one_least_active
            else:
                logging.debug("Successfully set networking to NAT")

class VBoxMachine():

    def __init__(self, hypervisor, machine):
        self.hypervisor = hypervisor
        self.machine    = machine
        self.name       = machine.name
        self.uuid       = machine.id
        self.window     = None
        self.winid      = 0
        self.overlay_data_size = 0
        
        self.is_booting   = False
        self.is_booted    = False
        self.is_finished  = False

        self.last_state   = self.hypervisor.constants.MachineState_PoweredOff
        
        self.current_disk_rank = 0
        self.machine.saveSettings()

        self.usb_attachmnts = SmartDict()
        self.usb_master     = None
        
    def __del__(self):
        del self.machine
        
    def get_winid(self):
        if self.winid == 0:
            try:
                self.winid = self.machine.showConsoleWindow()
            except:
                self.winid = 0
        return self.winid
    
    def show_fullscreen(self, toggle, rwidth=0, rheigth=0):
        self.machine.showConsoleFullscreen(toggle, rwidth, rheigth)
    
    def show_normal(self):
        self.machine.showConsoleNormal()
        
    def show_minimized(self):
        self.machine.showConsoleMinimized()
        
    def start(self):
        self.hypervisor.session = self.hypervisor.vm_manager.mgr.getSessionObject(self.hypervisor.vm_manager.vbox)
        progress = self.hypervisor.vm_manager.vbox.openRemoteSession(self.hypervisor.session, self.uuid, "gui", "")
        progress.waitForCompletion(-1)
        completed = progress.completed
        rc = int(progress.resultCode)
        if rc == 0:
            self.machine = self.hypervisor.session.machine
            return 0

        else:
            return 1

    def power_down(self, force=False):
        try:
            console = self.hypervisor.session.console
            if force:
                console.powerDown()

            else:
                if not console.getGuestEnteredACPIMode():
                    return 1

                console.powerButton()
                return 0

        except:
           return 2

    def is_running(self):
       try:
            state = self.machine.state
            if state != self.hypervisor.constants.MachineState_Aborted and \
               state != self.hypervisor.constants.MachineState_PoweredOff and \
               state != self.hypervisor.constants.MachineState_Null:
                return True
       except:
            pass

       return False

    def set_variable(self, variable_expr, variable_value, save=False):
        expr = 'self.machine.' + variable_expr + ' = ' + variable_value
        try:
            exec expr
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def attach_harddisk(self, location, disk_rank=-1, save=False):
        if disk_rank == -1:
            disk_rank = self.current_disk_rank
            self.current_disk_rank += 1
        if disk_rank >= 3:
            logging.debug("Maximum IDE disk rank is 2, " + str(disk_rank) + " given")
            return 1
        disk = self.hypervisor.find_disk(location)
        if disk == None:
            disk = self.hypervisor.add_harddisk(location)
        if disk == None:
            return 1

        # device 1, port 0 is busy by cd-rom...
        if disk_rank >= 2:
            disk_rank += 1
        try:
            if self.hypervisor.vbox_version() >= "3.1.0":
                controller = self.get_controller("IDE")
                self.machine.attachDevice(controller.name, disk_rank // 2, disk_rank % 2,
                                          self.hypervisor.constants.DeviceType_HardDisk, disk.id)
            elif self.hypervisor.vbox_version() >= "2.2.0":
                self.machine.attachHardDisk(disk.id, "IDE", 
                                            disk_rank // 2, disk_rank % 2)
            elif self.hypervisor.vbox_version() >= "2.1.0":
                self.machine.attachHardDisk2(disk.id, self.hypervisor.constants.StorageBus_IDE, 
                                             disk_rank // 2, disk_rank % 2)
            else:
                self.machine.attachHardDisk(disk.id, self.hypervisor.constants.StorageBus_IDE, 
                                            disk_rank // 2, disk_rank % 2)
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def attach_dvd(self, location='', host_drive=False, save=False):
        if host_drive:
            dvd = self.machine.DVDDrive.captureHostDrive(self.machine.DVDDrive.getHostDrive())
        else:
            dvd = self.vbox.find_dvd(location)
            if dvd == None:
                dvd = self.hypervisor.add_dvd(location)
            if dvd == None:
                return 1

        if self.hypervisor.vbox_version() >= "3.1.0":
            controller = self.get_controller("DVD")
            self.machine.attachDevice(controller.name, 0, 0, self.hypervisor.constants.DeviceType_DVD, dvd.id)
            self.machine.mountMedium(controller.name, 0, 0, dvd.id, False)
        else:
            self.machine.DVDDrive.mountImage(dvd.id)
        if save:
            self.machine.saveSettings()
        return 0

    def get_controller(self, kind):
        buses = { "Floppy" : self.hypervisor.constants.StorageBus_Floppy,
                  "IDE" : self.hypervisor.constants.StorageBus_IDE }
        if not buses.has_key(kind):
            logging.debug("Unknown type of controller")
            return None
        try:
            controller = self.machine.getStorageControllerByName(kind + " Controller")
        except:
            controller = self.machine.addStorageController(kind + " Controller", buses[kind])
        return controller

    def attach_floppy(self, location='', host_drive=False, save=False):
        if host_drive:
            floppy = self.machine.floppyDrive.captureHostDrive(self.machine.floppyDrive.getHostDrive())
        else:
            floppy = self.hypervisor.find_floppy(location)
            if floppy == None:
                floppy = self.hypervisor.add_floppy(location)
            if floppy == None:
                return 1

        if self.hypervisor.vbox_version() >= "3.1.0":
            controller = self.get_controller("Floppy")
            self.machine.attachDevice(controller.name, 0, 0, self.hypervisor.constants.DeviceType_Floppy, floppy.id)
            self.machine.mountMedium(controller.name, 0, 0, floppy.id, False)
        elif self.hypervisor.vbox_version() >= "2.1.0":
            self.machine.floppyDrive.enabled = True
            self.machine.floppyDrive.mountImage(floppy.id)
        else:
            self.machine.FloppyDrive.enabled = True
            self.machine.FloppyDrive.mountImage(floppy.id)
        if save:
            self.machine.saveSettings()
        return 0

    def attach_usb(self, usb, attach=True):
        if attach:
            logging.debug("Attaching usb device: " + str(usb['path']) + ", " + str(usb['name']))
            self.add_shared_folder(usb['name'], usb['path'], writable = True)
            self.set_guest_property("/UFO/Com/HostToGuest/Shares/ReadyToMount/" + str(usb['name']), 
                                    str(usb['name']))
        else:
            logging.debug("Detaching usb device: " + str(usb['path']) + ", " + str(usb['name']))
            self.remove_shared_folder(str(usb['name']))
            self.set_guest_property("/UFO/Com/HostToGuest/Shares/Remove/" + str(usb['name']), 
                                    str(usb['path']))
        usb['attach'] = attach

    def add_shared_folder(self, name, host_path, writable, save=False):
        try:
            self.machine.createSharedFolder(name, host_path, writable)
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0
    
    def remove_shared_folder(self, name, save=False):
        try:
            self.machine.removeSharedFolder(name)
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def set_boot_device(self, device_type, save=False):
        assert device_type == "HardDisk" or device_type == "DVD" or device_type == "Floppy"
        self.machine.setBootOrder(1, getattr(self.hypervisor.constants, "DeviceType_" + device_type))
        if save:
            self.machine.saveSettings()
        return 0

    def set_boot_logo(self, image_path, fade_in=True, fade_out=True, display_time=0, save=False):
        self.machine.BIOSSettings.logoImagePath   = image_path
        self.machine.BIOSSettings.logoFadeIn      = fade_in
        self.machine.BIOSSettings.logoFadeOut     = fade_out
        self.machine.BIOSSettings.logoDisplayTime = display_time
        if save:
            self.machine.saveSettings()
        return 0

    def set_bios_params(self, acpi_enabled, ioapic_enabled, save=False):
        self.machine.BIOSSettings.ACPIEnabled   = acpi_enabled
        self.machine.BIOSSettings.IOAPICEnabled = ioapic_enabled
        if save:
            self.machine.saveSettings()
        return 0

    def disable_boot_menu(self, save=False):
        self.machine.BIOSSettings.bootMenuMode = \
            self.hypervisor.constants.BIOSBootMenuMode_Disabled

    def set_ram_size(self, ram_size, save=False):
        try:
            self.machine.memorySize = ram_size
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def set_vram_size(self, vram_size, save=False):
        try:
            self.machine.VRAMSize = vram_size
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def set_audio_adapter(self, audio_driver, audio_controller=None, save=False):
        if not audio_controller:
            audio_controller = self.hypervisor.constants.AudioControllerType_AC97

        assert audio_controller in self.hypervisor.constants._Values['AudioControllerType'].values()
        assert audio_driver in self.hypervisor.constants._Values['AudioDriverType'].values()

        self.machine.audioAdapter.enabled = True
        self.machine.audioAdapter.audioController = audio_controller
        self.machine.audioAdapter.audioDriver = audio_driver
        if save:
            self.machine.saveSettings()
        return 0

    def set_resolution(self, resolution, save=False):
        self.machine.setGuestProperty('/VirtualBox/GuestAdd/Vbgl/Video/SavedMode', 
                                     resolution + 'x32', '')
        if save:
            self.machine.saveSettings()
        return 0

    def set_guest_property(self, key, value, save=False):
        self.machine.setGuestProperty(key, value, '')
        if save:
            self.machine.saveSettings()
        return 0
    
    def get_guest_property(self, key):
        return self.machine.getGuestPropertyValue(key)

    def set_extra_data(self, key, value, save=False):
        self.machine.setExtraData(key, value)
        if save:
            self.machine.saveSettings()
        return 0

    def set_fullscreen(self, save=False):
        self.machine.setExtraData('GUI/Fullscreen', 'on')
        if save:
            self.machine.saveSettings()
        return 0

    def set_network_adapter(self, attach_type=None, adapter_type=None, mac_address='', host_adapter='', save=False):
        assert adapter_type in self.hypervisor.constants.constants._Values['NetworkAdapterType'].values() or \
               adapter_type == None
        assert attach_type in self.hypervisor.constants._Values['NetworkAttachmentType'].values() or \
               attach_type == None
        
        result_code = 0
        try:
            if adapter_type != None:
                self.machine.getNetworkAdapter(0).adapterType = adapter_type
        except Exception, e:
            logging.debug(e)
            result_code = 1
        try:
            if mac_address != '':
                self.machine.getNetworkAdapter(0).MACAddress = mac_address
        except Exception, e:
            logging.debug(e)
            result_code = 2

        try:
            if attach_type == self.hypervisor.constants.NetworkAttachmentType_NAT:
                self.machine.getNetworkAdapter(0).attachToNAT()
                self.machine.getNetworkAdapter(0).cableConnected = True

            elif attach_type == self.hypervisor.constants.NetworkAttachmentType_Bridged:
                assert host_adapter != ''
                if mac_address:
                    self.machine.getNetworkAdapter(0).MACAddress = mac_address
                self.machine.getNetworkAdapter(0).hostInterface = host_adapter
                if self.hypervisor.vbox_version() < "2.2.0":
                    self.machine.getNetworkAdapter(0).attachToHostInterface()
                else:
                    self.machine.getNetworkAdapter(0).attachToBridgedInterface()

            elif attach_type == self.hypervisor.constants.NetworkAttachmentType_Null:
                self.machine.getNetworkAdapter(0).detach()
                self.machine.getNetworkAdapter(0).cableConnected = False

        except Exception, e:
            logging.debug(e)
            result_code = 3
        if save:
            self.machine.saveSettings()
        return result_code
    
    def get_network_adapter_type(self):
        return self.machine.getNetworkAdapter(0).attachmentType

    def get_mac_addr(self):
        return self.machine.getNetworkAdapter(0).MACAddress

    def set_procs(self, nbprocs, save=False):
        self.machine.CPUCount = nbprocs
        if save:
            self.machine.saveSettings()
        return 0

    def enable_vt(self, state):
        if self.hypervisor.vbox_version() >= "3.1.0":
            self.machine.setHWVirtExProperty(self.hypervisor.constants.HWVirtExPropertyType_Enabled, state)
        else:
            self.machine.HWVirtExEnabled = state

    def enable_pae(self, state):
        if self.hypervisor.vbox_version() >= "3.1.0":
            self.machine.setCpuProperty(self.hypervisor.constants.CpuPropertyType_PAE, state)
        else:
            self.machine.PAEEnabled = state
            
    def enable_nested_paging(self, state):
        if self.hypervisor.vbox_version() >= "3.1.0":
            self.machine.setHWVirtExProperty(self.hypervisor.constants.HWVirtExPropertyType_NestedPaging, state)
        else:
            self.machine.HWVirtExNestedPagingEnabled = state

    def set_cpu_capabilities(self, PAE=False, VT=False, nested_paging=False):
        self.enable_vt(VT)
        self.enable_pae(PAE)
        self.enable_nested_paging(nested_paging)

    def enable_3D(self, state):
        if self.hypervisor.vbox_version() >= "2.1.0":
            self.machine.accelerate3DEnabled = state


class VBoxHost():

    def __init__(self, host, constants):
        self.host = host
        self.constants = constants

    def __del__(self):
        del self.host

    def is_virt_ex_available(self):
        return self.host.getProcessorFeature(self.constants.ProcessorFeature_HWVirtEx)
    
    def get_nb_procs(self):
        return self.host.processorCount
    
    def get_total_ram(self):
        return self.host.memorySize

    def get_free_ram(self):
        return self.host.memoryAvailable

    def get_DVD_drives(self):
        return self.host.DVDDrives
    
    def is_network_active(self):
        from PyQt4 import QtNetwork
        for interface in QtNetwork.QNetworkInterface.allInterfaces():
            flags = interface.flags()
            if int(flags & QtNetwork.QNetworkInterface.IsRunning) and not int(flags & QtNetwork.QNetworkInterface.IsLoopBack):
                return True
        return False

class VBoxMonitor:
    def __init__(self):
        pass
    
    def onMachineStateChange(self, id, state):
        pass
        
    def onMachineDataChange(self,id):
        pass

    def onExtraDataCanChange(self, id, key, value):
        pass

    def onExtraDataChange(self, id, key, value):
        pass

    def onMediaRegistred(self, id, type, registred):
        pass

    def onMachineRegistered(self, id, registred):
        pass

    def onSessionStateChange(self, id, state):
        pass

    def onSnapshotTaken(self, mach, id):
        pass

    def onSnapshotDiscarded(self, mach, id):
        pass

    def onSnapshotChange(self, mach, id):
        pass

    def onGuestPropertyChange(self, id, name, newValue, flags):
        pass


