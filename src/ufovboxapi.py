#!/usr/bin/env python
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


import os
import uuid as uuid_lib
import traceback
import logging
import time
import gui
import sys

class VBoxHypervisor():
                        
    def __init__(self, vbox_callback_class = None, vbox_callback_arg = None):
        from vboxapi import VirtualBoxManager
        from vboxapi import VirtualBoxReflectionInfo

        self.current_machine = None
        self.session = None
        self.cleaned = False
        
        self.vm_manager = VirtualBoxManager(None, None)
        self.constants = VirtualBoxReflectionInfo(False)
        self.mgr  = self.vm_manager.mgr
        self.vbox = self.vm_manager.vbox
        
        self.host = VBoxHost(self.vm_manager.vbox.host, self.constants)
        
        if self.vbox_version() >= "3.0.0":
            self.cb = self.vm_manager.createCallback('IVirtualBoxCallback', vbox_callback_class, vbox_callback_arg)
            self.vbox.registerCallback(self.cb)
            self.callbacks_aware = True
        else:
            self.guest_props = {}
            self.vbox_callback_obj = vbox_callback_arg
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

    def create_machine(self, machine_name, os_type, base_dir = ''):
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

    def add_harddisk(self, location):
        try:
            if self.vbox_version() >= "3.0.0":
                disk = self.vbox.openHardDisk(location, self.constants.AccessMode_ReadOnly,
                                              False, '', False, '')
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
            dvd = self.vbox.openDVDImage(location, uuid)
            if self.vbox_version() < "2.1.0":
                self.vbox.registerDVDImage(dvd)
        except Exception, e:
            logging.debug(e)
            return None
        return dvd

    def add_floppy(self, location):
        uuid = str(uuid_lib.uuid4())
        try:
            floppy = self.vbox.openFloppyImage(location, uuid)
            if self.vbox_version() < "2.1.0":
                self.vbox.registerFloppyImage(floppy)
        except Exception, e:
            logging.debug(e)
            return None
        return floppy

    def set_extra_data(self, key, value, save = False):
        self.vbox.setExtraData(key, value)
        if save and hasattr(self.vbox, "saveSettings"):
            self.vbox.saveSettings()
        return 0

    def license_agreed(self):
        if self.vbox.getExtraData("GUI/LicenseAgreed"):
            return 1
        return 0 

    def minimal_callbacks_maker_loop(self):
        try:
            names, values, x, x = self.current_machine.machine.enumerateGuestProperties("*")
    
            id = 0
            guest_props = {}
            while id < len(names):
                guest_props[names[id]] = values[id]
                    
                if not self.guest_props.has_key(names[id]) or \
                   self.guest_props[names[id]] != values[id]:
                    self.vbox_callback_obj.onGuestPropertyChange(names[id], 
                                                                 guest_props[names[id]], 
                                                                 "")
                    if names[id] == "/UFO/Boot/Progress" and guest_props[names[id]] >= "0.95":
                        self.vbox_callback_obj.onGuestPropertyChange("/VirtualBox/GuestAdd/Vbgl/Video/SavedMode", 
                                                                     self.guest_props["/VirtualBox/GuestAdd/Vbgl/Video/SavedMode"], 
                                                                     "")
                id += 1
            
            self.guest_props = guest_props
            
            state = self.current_machine.machine.state
            last_state = self.current_machine.last_state
            if self.current_machine.last_state != state:
                if state == self.constants.MachineState_Running and \
                   last_state == self.constants.MachineState_PoweredOff:
                    self.vbox_callback_obj.onMachineStateChange(self.constants.MachineState_Starting)
                if state == self.constants.MachineState_PoweredOff:
                    self.vbox_callback_obj.onMachineStateChange(self.constants.MachineState_Stopping)
                    
                self.vbox_callback_obj.onMachineStateChange(state)
        except:
            self.vbox_callback_obj.onMachineStateChange(self.constants.MachineState_Stopping)
            self.vbox_callback_obj.onMachineStateChange(self.constants.MachineState_PoweredOff)

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
            "session.close()"
            return 0
        else:
            return 1

    def set_variable(self, variable_expr, variable_value, save = False):
        expr = 'self.machine.' + variable_expr + ' = ' + variable_value
        try:
            exec expr
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def attach_harddisk(self, location, disk_rank = -1, save = False):
        if disk_rank == -1:
            disk_rank = self.current_disk_rank
            self.current_disk_rank += 1
        if disk_rank >= 3:
            logging.debug("Maximum IDE disk rank is 2, " + str(disk_rank) + " given")
            return 1
        try:
            disk = self.hypervisor.vbox.findHardDisk(location)
        except Exception, e:
            disk = self.hypervisor.add_harddisk(location)

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

    def attach_dvd(self, location = '', host_drive = False, save = False):
        if host_drive:
            dvd = self.machine.DVDDrive.captureHostDrive(self.machine.DVDDrive.getHostDrive())
        else:
            try:
                dvd = self.hypervisor.vbox.findDVDImage(location)
            except Exception, e:
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

    def attach_floppy(self, location = '', host_drive = False, save = False):
        if host_drive:
            floppy = self.machine.floppyDrive.captureHostDrive(self.machine.floppyDrive.getHostDrive())
        else:
            try:
                floppy = self.hypervisor.vbox.findFloppyImage(location)
            except Exception, e:
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

    def add_shared_folder(self, name, host_path, writable, save = False):
        try:
            self.machine.createSharedFolder(name, host_path, writable)
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0
    
    def remove_shared_folder(self, name, save = False):
        try:
            self.machine.removeSharedFolder(name)
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def set_boot_device(self, device_type, save = False):
        assert device_type == "HardDisk" or device_type == "DVD" or device_type == "Floppy"
        self.machine.setBootOrder(1, getattr(self.hypervisor.constants, "DeviceType_" + device_type))
        if save:
            self.machine.saveSettings()
        return 0

    def set_boot_logo(self, image_path, fade_in = True, fade_out = True, display_time = 0, save = False):
        self.machine.BIOSSettings.logoImagePath   = image_path
        self.machine.BIOSSettings.logoFadeIn      = fade_in
        self.machine.BIOSSettings.logoFadeOut     = fade_out
        self.machine.BIOSSettings.logoDisplayTime = display_time
        if save:
            self.machine.saveSettings()
        return 0

    def set_bios_params(self, acpi_enabled, ioapic_enabled, save = False):
        self.machine.BIOSSettings.ACPIEnabled   = acpi_enabled
        self.machine.BIOSSettings.IOAPICEnabled = ioapic_enabled
        if save:
            self.machine.saveSettings()
        return 0

    def disable_boot_menu(self, save = False):
        self.machine.BIOSSettings.bootMenuMode = \
            self.hypervisor.constants.BIOSBootMenuMode_Disabled

    def set_ram_size(self, ram_size, save = False):
        try:
            self.machine.memorySize = ram_size
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def set_vram_size(self, vram_size, save = False):
        try:
            self.machine.VRAMSize = vram_size
        except Exception, e:
            logging.debug(e)
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def set_audio_adapter(self, audio_driver, audio_controller = "AC97", save = False):
        assert audio_controller == "AC97" or audio_controller == "SB16"
        assert audio_driver == "Null" or audio_driver == "WinMM" or \
               audio_driver == "OSS" or audio_driver == "ALSA" or \
               audio_driver == "DirectSound" or audio_driver == "CoreAudio" or \
               audio_driver == "MMPM" or audio_driver == "Pulse" or \
               audio_driver == "SolAudio"

        self.machine.audioAdapter.enabled = True
        self.machine.audioAdapter.audioController = \
            getattr(self.hypervisor.constants, "AudioControllerType_" + audio_controller)
        self.machine.audioAdapter.audioDriver = \
            getattr(self.hypervisor.constants, "AudioDriverType_" + audio_driver)
        if save:
            self.machine.saveSettings()
        return 0

    def set_resolution(self, resolution, save = False):
        self.machine.setGuestProperty('/VirtualBox/GuestAdd/Vbgl/Video/SavedMode', 
                                      resolution + 'x32', '')
        if save:
            self.machine.saveSettings()
        return 0

    def set_guest_property(self, key, value, save = False):
        self.machine.setGuestProperty(key, value, '')
        if save:
            self.machine.saveSettings()
        return 0
    
    def get_guest_property(self, key):
        return self.machine.getGuestPropertyValue(key)

    def set_extra_data(self, key, value, save = False):
        self.machine.setExtraData(key, value)
        if save:
            self.machine.saveSettings()
        return 0

    def set_fullscreen(self, save = False):
        self.machine.setExtraData('GUI/Fullscreen', 'on')
        if save:
            self.machine.saveSettings()
        return 0

    def set_network_adapter(self, attach_type = '', adapter_type = '', mac_address = '', host_adapter = '', save = False):
        assert adapter_type == "Null" or adapter_type == "Am79C970A" or \
            adapter_type == "I82540EM" or adapter_type == "I82543GC" or \
            adapter_type == "I82545EM" or adapter_type == "Am79C973" or \
            adapter_type == ""
        assert attach_type == "NAT" or attach_type == "Bridged" or \
            attach_type =="None" or attach_type == ""
        
        result_code = 0
        try:
            if adapter_type != '':
                self.machine.getNetworkAdapter(0).adapterType = \
                    getattr(self.hypervisor.constants, "NetworkAdapterType_" + adapter_type)
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
            if attach_type == "NAT":
                self.machine.getNetworkAdapter(0).attachToNAT()
            elif attach_type =="Bridged":
                assert host_adapter != ''
                if mac_address:
                    self.machine.getNetworkAdapter(0).MACAddress = mac_address
                self.machine.getNetworkAdapter(0).hostInterface = host_adapter
		if self.hypervisor.vbox_version() < "2.2.0":
                    self.machine.getNetworkAdapter(0).attachToHostInterface()
                else:
                    self.machine.getNetworkAdapter(0).attachToBridgedInterface()
            elif attach_type =="None":
                self.machine.getNetworkAdapter(0).detach()
        except Exception, e:
            logging.debug(e)
            result_code = 3
        if save:
            self.machine.saveSettings()
        return result_code

    def set_procs(self, nbprocs, save = False):
        self.machine.CPUCount = nbprocs
        if save:
            self.machine.saveSettings()
        return 0

    def enable_vt(self, state):
        if self.hypervisor.vbox_version() >= "3.1.0":
            self.machine.setHWVirtExProperty(self.hypervisor.constants.HWVirtExPropertyType_Enabled, state)
        else:
            self.machine.HWVirtExEnabled = state


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

        
def test_cases():
    vm = VBoxHypervisor()
    print "-- Let's test ufovboxapi !"

    # create_machine
    created = vm.create_machine('test', 'Fedora')
    for m in vm.get_machines():
        print m.name + " : " + m.id
    if created != 0 or not 'test' in [ m.name for m in vm.get_machines() ]:
        print "-- create_machine: failed!"
    else:
        print "-- create_machine: success!"

    # open_machine
    if vm.open_machine('test') != 0 or vm.current_machine == None:
        print "-- open_machine: failed!"
    else:
        print "created : " + vm.current_machine.machine.name
        print "-- open_machine: success!"

    # set_machine_var
    if vm.current_machine.set_variable('BIOSSettings.IOAPICEnabled', 'True', save = 'False') != 0 or \
        vm.current_machine.set_variable('WRONGSettings.WRONG', 'True') == 0:
        print "-- set_machine_variable: failed!"
    else:
        print "-- set_machine_variable: success!"

    # add_dvd
    if vm.current_machine.attach_harddisk('/home/vienin/hdd.vdi', 0, save = 'False') != 0:
        print "-- attach_harddisk: failed!"
    else:
        print "-- attach_harddisk: success!"

    if vm.current_machine.attach_dvd('/home/vienin/Fedora-11-Alpha-i386-DVD.iso', save = 'False') != 0:
        print "-- attach_dvd: failed!"
    else:
        print "-- attach_dvd: success!"
    if True or vm.current_machine.attach_dvd('', True, save = 'False') != 0:
        print "-- attach_dvd, host drive: failed!"
    else:
        print "-- attach_dvd, host drive: success!"

    if vm.current_machine.attach_floppy('/home/vienin/bootfloppy.img', save = 'False') != 0:
        print "-- attach_floppy: failed!"
    else:
        print "-- attach_floppy: success!"
    if True or vm.current_machine.attach_floppy('', True, save = 'False') != 0:
        print "-- attach_floppy, host drive: failed!"
    else:
        print "-- attach_floppy, host drive: success!"

    # set_boot_device
    if vm.current_machine.set_boot_device('DVD', save = 'False') != 0:
        print "-- set_boot_device: failed!"
    else:
        print "-- set_boot_device: success!"

    if  vm.current_machine.set_ram_size("400", save = 'False') !=0:
        print "-- set_ram_size: failed!"
    else:
        print "-- set_ram_size: success!"

    if  vm.current_machine.set_vram_size("64", save = 'False') !=0:
        print "-- set_vram_size: failed!"
    else:
        print "-- set_vram_size: success!"

    if  vm.current_machine.set_resolution("17x17", save = 'False') !=0:
        print "-- set_resolution: failed!"
    else:
        print "-- set_resolution: success!"

    if  vm.current_machine.set_fullscreen(save = 'False') !=0:
        print "-- set_fullscreen: failed!"
    else:
        print "-- set_fullscreen: success!"

    if  vm.current_machine.set_boot_logo ('/rg/rg', save = 'False') !=0:
        print "-- set_boot_logo: failed!"
    else:
        print "-- set_boot_logo: success!"

    if  vm.current_machine.set_network_adapter('NAT', 'I82540EM', '002215952933', save = 'False') !=0:
        print "-- set_network_adapter: failed!"
    else:
        print "-- set_network_adapter: success!"

    if  vm.current_machine.add_shared_folder("host_home", "/home", True, save = 'False') !=0:
        print "-- add_shared_folder: failed!"
    else:
        print "-- add_shared_folder: success!"

    if  vm.current_machine.set_audio_adapter("ALSA", "AC97", save = 'False') !=0 or \
        vm.current_machine.set_audio_adapter("OSS", "AC97", save = 'False') != 0:
        print "-- set_audio_adapter: failed!"
    else:
        print "-- set_audio_adapter: success!"

    # start_machine
    vm.close_session()
    if vm.current_machine.start() != 0:
        print "-- start: failed!"
    else:
        print "-- start: success!"

    # close_machine
    if vm.close_machine() != 0:
        print "-- close_machine: failed!"
    else:
        print "-- close_machine: success!"

    print "and some infos about host machine: ram " + str(vm.host.get_total_ram()) + ", free ram " + str(vm.host.get_free_ram())
    del vm

if __name__ == '__main__':
    test_cases()

