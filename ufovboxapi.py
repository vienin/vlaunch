#!/usr/bin/env python
# -*- coding: utf-8 -*-

# export VBOX_PROGRAM_PATH=/usr/lib/virtualbox/ PYTHONPATH=..:$VBOX_PROGRAM_PATH

import uuid as uuid_lib

from vboxapi import VirtualBoxManager
from vboxapi import VirtualBoxReflectionInfo

class Host:

    def get_total_ram(self):
        pass
    def get_free_ram(self):
        pass

class Hypervisor:

    def create_machine(self, machine_name, os_type, base_dir = ''):
        pass
    def open_machine(self, machine_name):
        pass
    def close_session(self):
        pass
    def close_machine(self):
        pass
    def get_machines(self):
        pass
    def add_harddisk(self):
        pass
    def add_dvd(self, location, uuid):
        pass
    def add_floppy(self, location, uuid):
        pass
    def set_extra_data(self, key, value):
        pass

class VirtualMachine:

    def start(self):
        pass
    def set_variable(self, variable_expr, variable_value):
        pass
    def attach_harddisk(self, location, disk_rank):
        pass
    def attach_dvd(self, location, host_drive):
        pass
    def attach_floppy(self, location, host_drive):
        pass
    def add_shared_folder(self, name, host_path, writable):
        pass
    def remove_shared_folder(self, name):
        pass
    def set_boot_device(self, device_type):
        pass
    def set_boot_logo(self, image_path, fade_in, fade_out, display_time):
        pass
    def set_bios_params(self, acpi_enabled, ioapic_enabled):
        pass
    def disable_boot_menu(self):
        pass
    def set_ram_size(self, ram_size):
        pass
    def set_vram_size(self, vram_size):
        pass
    def set_resolution(self, resolution):
        pass
    def set_fullscreen(self):
        pass
    def set_guest_property(self, key, value):
        pass
    def set_network_adapter(self, attach_type, adapter_type, mac_address):
        pass
    def set_audio_adapter(self, audio_driver, audio_controller):
        pass
    def set_extra_data(self, key, value):
        pass

class VBoxHypervisor(Hypervisor):

    def __init__(self):
        self.vm_manager = VirtualBoxManager(None, None)
        self.mgr  = self.vm_manager.mgr
        self.vbox = self.vm_manager.vbox
        self.host = VBoxHost(self.vm_manager.vbox.host)
        
        self.current_machine = None
        self.session = None

    def __del__(self):
        self.vbox.saveSettings()
        self.vm_manager.deinit()
        del self.vm_manager

    def create_machine(self, machine_name, os_type, base_dir = ''):
        try:
            self.vbox.getGuestOSType(os_type)
        except Exception, e:
            print 'Unknown OS type:',os_type
            return 1
        try:
            self.vbox.registerMachine(self.vbox.createMachine(machine_name, os_type, base_dir, ""))
        except Exception, e:
            print e
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
        return self.vm_manager.getArray(self.vm_manager.vbox, 'machines')

    def add_harddisk(self, location):
        try:
            disk = self.vbox.openHardDisk(location, 
                VirtualBoxReflectionInfo().AccessMode_ReadOnly, False, '', False, '')
        except Exception, e:
            print e
            return None
        return disk

    def add_dvd(self, location):
        uuid = str(uuid_lib.uuid4())
        try:
            dvd = self.vbox.openDVDImage(location, uuid)
        except Exception, e:
            print e
            return None
        return dvd

    def add_floppy(self, location):
        uuid = str(uuid_lib.uuid4())
        try:
            floppy = self.vbox.openFloppyImage(location, uuid)
        except Exception, e:
            print e
            return None
        return floppy

    def set_extra_data(self, key, value, save = False):
        self.vbox.setExtraData(key, value)
        if save:
            self.vbox.saveSettings()
        return 0

    def license_agreed(self):
        return self.vbox.getExtraData("GUI/LicenseAgreed") == "7"

class VBoxMachine(VirtualMachine):

    def __init__(self, hypervisor, machine):
        self.hypervisor = hypervisor
        self.machine    = machine
        self.name       = machine.name
        self.uuid       = machine.id
        self.current_disk_rank = 0
        self.machine.saveSettings()
        
    def __del__(self):
        del self.machine

    def start(self):
        session = self.hypervisor.vm_manager.mgr.getSessionObject(self.hypervisor.vm_manager.vbox)
        progress = self.hypervisor.vm_manager.vbox.openRemoteSession(session, self.uuid, "gui", "")
        progress.waitForCompletion(-1)
        completed = progress.completed
        rc = int(progress.resultCode)
        if rc == 0:
            session.close()
            return 0;
        else:
            return 1

    def set_variable(self, variable_expr, variable_value, save = False):
        expr = 'self.machine.' + variable_expr + ' = ' + variable_value
        print "Executing",expr
        try:
            exec expr
        except Exception, e:
            print 'failed: ',e
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def attach_harddisk(self, location, disk_rank = -1, save = False):
        if disk_rank == -1:
            disk_rank = self.current_disk_rank
            self.current_disk_rank += 1
        if disk_rank >= 3:
            print "Maximum IDE disk rank is 2, " + str(disk_rank) + " given"
            return 1
        try:
            disk = self.hypervisor.vbox.findHardDisk(location)
        except Exception, e:
            disk = self.hypervisor.add_harddisk(location)

        # device 1, port 0 is busy by cd-rom...
        if disk_rank >= 2:
            disk_rank += 1
        try:
            self.machine.attachHardDisk(disk.id, "IDE", disk_rank // 2, disk_rank % 2)
        except Exception, e:
            print e
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

        self.machine.DVDDrive.mountImage(dvd.id)
        if save:
            self.machine.saveSettings()
        return 0

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

        self.machine.floppyDrive.enabled = True
        self.machine.floppyDrive.mountImage(floppy.id)
        if save:
            self.machine.saveSettings()
        return 0

    def add_shared_folder(self, name, host_path, writable, save = False):
        try:
            self.machine.createSharedFolder(name, host_path, writable)
        except Exception, e:
            print e
            return 1
        if save:
            self.machine.saveSettings()
        return 0
    
    def remove_shared_folder(self, name):
        try:
            self.machine.removeSharedFolder(name)
        except Exception, e:
            print e
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def set_boot_device(self, device_type, save = False):
        assert device_type == "HardDisk" or device_type == "DVD" or device_type == "Floppy"
        self.machine.setBootOrder(1, getattr(VirtualBoxReflectionInfo(), "DeviceType_" + device_type))
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
            VirtualBoxReflectionInfo().BIOSBootMenuMode_Disabled

    def set_ram_size(self, ram_size, save = False):
        try:
            self.machine.memorySize = ram_size
        except Exception, e:
            print e
            return 1
        if save:
            self.machine.saveSettings()
        return 0

    def set_vram_size(self, vram_size, save = False):
        try:
            self.machine.VRAMSize = vram_size
        except Exception, e:
            print e
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
            getattr(VirtualBoxReflectionInfo(), "AudioControllerType_" + audio_controller)
        self.machine.audioAdapter.audioDriver = \
            getattr(VirtualBoxReflectionInfo(), "AudioDriverType_" + audio_driver)
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

    def set_network_adapter(self, attach_type = '', adapter_type = '', mac_address = '', save = False):
        assert adapter_type == "Null" or adapter_type == "Am79C970A" or \
            adapter_type == "I82540EM" or adapter_type == "I82543GC" or \
            adapter_type == "I82545EM" or adapter_type == "Am79C973" or \
            adapter_type == ""
        assert attach_type == "NAT" or attach_type == "Bridged" or \
            attach_type =="None" or attach_type == ""
        
        result_code = 0
        try:
            if adapter_type != '':
                self.machine.getNetworkAdapter(1).adapterType = \
                    getattr(VirtualBoxReflectionInfo(), "NetworkAdapterType_" + adapter_type)
        except Exception, e:
            print e
            result_code = 1
        try:
            if mac_address != '':
                self.machine.getNetworkAdapter(1).MACAddress = mac_address
        except Exception, e:
            print e
            result_code = 2
        try:
            if attach_type == "NAT":
                self.machine.getNetworkAdapter(1).attachToNAT()
            elif attach_type =="Bridged":
                self.machine.getNetworkAdapter(1).attachToBridgedInterface()
            elif attach_type =="None":
                self.machine.getNetworkAdapter(1).detach()
        except Exception, e:
            print e
            result_code = 3
        if save:
            self.machine.saveSettings()
        return result_code

class VBoxHost(Host):

    def __init__(self, host):
        self.host = host

    def __del__(self):
        del self.host

    def get_total_ram(self):
        return self.host.memorySize

    def get_free_ram(self):
        return self.host.memoryAvailable

    def get_DVD_drives(self):
        return self.host.DVDDrives

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

