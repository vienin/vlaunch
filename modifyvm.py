#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xml.dom.minidom as dom
import uuid as uuid_lib
import os
from optparse import OptionParser

# usefull api

class VirtualMachine:
	# virtual machine id
	name = ''
	xml	 = None		

	# setable attributes
	fullscreen  = True
	ram_size	= ''
	dvd_imag	= ''
	logo_image  = ''
	net_adapter = ''
	mac_address = ''
	resolution  = ''
	disks_tab   = []
	
	def __init__ (self, name, home_path, use_template = False):
		self.name = name
		self.file = os.path.join(home_path, "Machines", self.name, self.name + ".xml")
		if use_template and os.path.exists(self.file + ".template"):
			self.xml = dom.parse(self.file + ".template")
		else:
			self.xml = dom.parse(self.file)

	def set_disk_at (self, uuid, order):
		disks = self.xml.getElementsByTagName('AttachedDevice')
		if len(disks) > order:
			element = disks[order]
			image = element.getElementsByTagName('Image')[0]
			image.setAttribute('uuid', '{' + str(uuid) + '}')
		else:
			element = self.xml.getElementsByTagName('StorageController')[0]
			new_element = self.xml.createElement("AttachedDevice")
			new_image = self.xml.createElement("Image")
			new_image.setAttribute('uuid', '{' + uuid + '}')
			new_element.appendChild(new_image)
			new_element.setAttribute('type', 'HardDisk')
			new_element.setAttribute('port', '0')
			new_element.setAttribute('device', str(order))
			element.appendChild(new_element)

	def disable_dvd(self):
		share = self.xml.getElementsByTagName('DVDDrive')[0]
		while share.hasChildNodes():
			share.removeChild(share.firstChild)
	
	def set_dvd (self, uuid):
		dvddrive = self.xml.getElementsByTagName('DVDDrive')[0]
		dvds = dvddrive.getElementsByTagName('Image')
		if len(dvds) >= 1:
			element = dvds[0]
			element.setAttribute('uuid', '{' + uuid + '}')
		else:
			element = self.xml.getElementsByTagName('DVDDrive')[0]
			new_element = self.xml.createElement("Image")
			new_element.setAttribute('uuid', '{' + uuid + '}')
			element.appendChild(new_element)

	def set_dvd_direct (self, dev):
		if not dev:
			self.disable_dvd()
			return

		dvds = self.xml.getElementsByTagName('HostDrive')
		if len(dvds) >= 1:
			element = dvds[0]
			element.setAttribute('src', dev)
		else:
			element = self.xml.getElementsByTagName('DVDDrive')[0]
			new_element = self.xml.createElement("HostDrive")
			new_element.setAttribute('src', dev)
			element.appendChild(new_element)
	
	def set_floppy (self, uuid):
		floppydrive = self.xml.getElementsByTagName('FloppyDrive')[0]
		floppys = floppydrive.getElementsByTagName('Image')
		if len(floppys) >= 1:
			element = floppys[0]
			element.setAttribute('uuid', '{' + uuid + '}')
		else:
			element = self.xml.getElementsByTagName('FloppyDrive')[0]
			element.setAttribute("enabled", "true")
			new_element = self.xml.createElement("Image")
			new_element.setAttribute('uuid', '{' + uuid + '}')
			element.appendChild(new_element)
			
	def set_boot_device (self, device):
		assert device == "HardDisk" or device == "DVD" or device == "Floppy"
		for dev in self.xml.getElementsByTagName('Order'):
			if dev.getAttribute('position') == str(1):
				dev.setAttribute('device', device)
				return

	def set_ram_size (self, size):
		# TODO:
		# Check if (multiple de 4 ou je ne sais pas quoi)
		element = self.xml.getElementsByTagName('Memory')[0]
		element.setAttribute('RAMSize', str(size))

	def set_resolution (self, resolution):
		# Change resolution if node exist
		for prop in self.xml.getElementsByTagName('GuestProperty'):
			if prop.getAttribute('name') == '/VirtualBox/GuestAdd/Vbgl/Video/SavedMode':
				prop.setAttribute('value', resolution + 'x32')
				return

		# Else add this node
		element = self.xml.getElementsByTagName('GuestProperties')[0]
		new_element = self.xml.createElement("GuestProperty")
		new_element.setAttribute("name", "/VirtualBox/GuestAdd/Vbgl/Video/SavedMode")
		new_element.setAttribute("value", resolution + 'x32')
		element.appendChild(new_element)

	def set_fullscreen (self):
		for extra_data in self.xml.getElementsByTagName('ExtraDataItem'):
			if extra_data.getAttribute('name') == 'GUI/Fullscreen':
				extra_data.setAttribute('value', 'on')
				return

	def set_logo_image (self, image_path):
		element = self.xml.getElementsByTagName('Logo')[0]
		element.setAttribute("imagePath", image_path)

	def set_net_adapter_to_nat (self):
		if len(self.xml.getElementsByTagName('NAT')) == 0:
			for adapter in self.xml.getElementsByTagName('Adapter'):
				if adapter.getAttribute('slot') == str(0):
					while adapter.hasChildNodes():
						adapter.removeChild(adapter.firstChild)
					new_element = self.xml.createElement("NAT")
					adapter.appendChild(new_element)
					return

	def set_net_adapter_to_host (self, host_adapter):
		bridges = self.xml.getElementsByTagName('BridgedInterface')
		if len(bridges) == 0:
			for adapter in self.xml.getElementsByTagName('Adapter'):
				if adapter.getAttribute('slot') == str(0):
					while adapter.hasChildNodes():
						adapter.removeChild(adapter.firstChild)
					new_element = self.xml.createElement("BridgedInterface")
					new_element.setAttribute("name", host_adapter)
					adapter.appendChild(new_element)
					return
		else:
			bridges[0].setAttribute("name", host_adapter)

	def set_mac_address (self, mac_addr):
		for adapter in self.xml.getElementsByTagName('Adapter'):
			if adapter.getAttribute('slot') == str(0):
				adapter.setAttribute("MACAddress", mac_addr)
				return

	def set_guest_property (self, name, value):
		for prop in self.xml.getElementsByTagName('GuestProperty'):
			if prop.getAttribute('name') == name:
				prop.setAttribute('value', value)
				return

		element = self.xml.getElementsByTagName('GuestProperties')[0]
		new_element = self.xml.createElement("GuestProperty")
		new_element.setAttribute('name', name)
		new_element.setAttribute('value', value)
		element.appendChild(new_element)
				
	def set_shared_folder (self, share_name, host_path):
		if not host_path or host_path == "none":
			self.disable_shared_folder(share_name)
			return
			
		for share in self.xml.getElementsByTagName('SharedFolder'):
			if share.getAttribute('name') == share_name:
				share.setAttribute('hostPath', host_path)
				return

		element = self.xml.getElementsByTagName('SharedFolders')[0]
		new_element = self.xml.createElement("SharedFolder")
		new_element.setAttribute('name', share_name)
		new_element.setAttribute('hostPath', host_path)
		element.appendChild(new_element)
		
	def disable_shared_folder (self, share_name):
		for share in self.xml.getElementsByTagName('SharedFolder'):
			if share.getAttribute('name') == share_name:
				shares = share.parentNode
				shares.removeChild(share)
				return
				
	def reset_shared_folders (self):
		# beurkk...
		for share in self.xml.getElementsByTagName('SharedFolder'):
			shares = share.parentNode
			shares.removeChild(share)
				
	def reset_share_properties (self):
		for prop in self.xml.getElementsByTagName('GuestProperty'):
			if prop.getAttribute('name').startswith("share_"):
				properties = prop.parentNode
				properties.removeChild(prop)

	def write (self):
		open(self.file, 'w').write(self.xml.toxml().encode("utf-8"))

class VBoxConfiguration:
	xml	   = None
	machine   = None
	
	def __init__ (self, home_path, use_template = False):
		self.home_path = home_path
		self.file = os.path.join(home_path, "VirtualBox.xml")
		if use_template and os.path.exists(self.file + ".template"):
			self.xml = dom.parse(self.file + ".template")
		else:
			self.xml = dom.parse(self.file)

	def set_machine (self, machine_name, use_template = False):
		self.machine = VirtualMachine(machine_name, self.home_path, use_template)

	def set_dvd_image (self, image_name):
		uuid = str(uuid_lib.uuid4())
		dvds = self.xml.getElementsByTagName('Image')
		if len(dvds) >= 1:
			element = dvds[0]
			element.setAttribute('location', os.path.join(self.home_path, "Isos", image_name))
			element.setAttribute('uuid', '{' + uuid + '}')
		else:
			element = self.xml.getElementsByTagName('DVDImages')[0]
			new_element = self.xml.createElement("Image")
			new_element.setAttribute('location', os.path.join(self.home_path, "Isos", image_name))
			new_element.setAttribute('uuid', '{' + uuid + '}')
			element.appendChild(new_element)
		
		self.machine.set_dvd(uuid)

	def set_floppy_image (self, image_name):
		uuid = str(uuid_lib.uuid4())
		floppyimages = self.xml.getElementsByTagName('FloppyImages')[0]
		floppys = floppyimages.getElementsByTagName('Image')
		if len(floppys) >= 1:
			element = floppys[0]
			element.setAttribute('location', os.path.join(self.home_path, "Isos", image_name))
			element.setAttribute('uuid', '{' + uuid + '}')
		else:
			new_element = self.xml.createElement("Image")
			new_element.setAttribute('location', os.path.join(self.home_path, "Isos", image_name))
			new_element.setAttribute('uuid', '{' + uuid + '}')
			floppyimages.appendChild(new_element)
		
		self.machine.set_floppy(uuid)

	def set_raw_vmdk (self, file_name, uuid, order):
		disks = self.xml.getElementsByTagName('HardDisk')
		if len(disks) > order:
			element = disks[order]
			element.setAttribute('location', os.path.join("HardDisks", file_name))
			element.setAttribute('uuid', '{' + uuid + '}')
		elif len(disks) == order:
			element = self.xml.getElementsByTagName('HardDisks')[0]
			new_element = self.xml.createElement("HardDisk")
			new_element.setAttribute('location', os.path.join("HardDisks", file_name))
			new_element.setAttribute('uuid', '{' + uuid + '}')
			new_element.setAttribute('format', 'VMDK')
			new_element.setAttribute('type', 'Normal')
			element.appendChild(new_element)
		else:
			print "disk order error"
			return 1

		self.machine.set_disk_at(uuid, order)
		return 0

	def write (self):
		open(self.file, 'w').write(self.xml.toxml())

# modifyvm script
if __name__ == "__main__":
	usage = "%prog -o vbox_home -v vm_name [-d dvd_image_name] [-w vmdk_file_name] [-i vmdk_rank ] [-u vmdk_uuid] [-b (HardDisk | DVD)] [-r ram_size] [-R resolution] [-f] [-l logo_file_path] ([-n] | [-N host_net_adapter]) [-m mac_addr] [-a shared_folder_path]"
	description = "Modify given virtual machine with values given in parameters"
	version="%prog 0.1"

	parser = OptionParser(usage=usage, description=description, version=version)
	parser.add_option("-o", "--vbox-user-home", dest="home", default="",
					  help="virtual box home directory")
	parser.add_option("-v", "--virtual-machine", dest="vm", default="",
					  help="virtual machine name")
	parser.add_option("-d", "--dvd-image", dest="dvd", default="",
					  help="dvd image file name")
	parser.add_option("-w", "--raw-disk", dest="raw", default="",
					  help="raw disk vmdk file name")
	parser.add_option("-i", "--raw-disk-rank", dest="order", default=0,
					  help="raw disk vmdk ide rank")
	parser.add_option("-u", "--raw-disk-uuid", dest="uuid", default="",
					  help="raw disk vmdk uuid")
	parser.add_option("-b", "--boot", dest="boot", default="HardDisk",
					  help="indicate boot device (HardDisk or DVD)")
	parser.add_option("-r", "--ram-size", dest="ram", default="",
					  help="virtual machine ram size")
	parser.add_option("-R", "--resolution", dest="resolution", default="",
					  help="virtual machine display resolution")
	parser.add_option("-f", "--fullscreen", dest="fullscreen", default=False,
					  action="store_true", help="activate fullscreen at startup")
	parser.add_option("-l", "--logo", dest="logo", default="",
					  help="logo image fullpath")
	parser.add_option("-n", "--net-nat", dest="netnat", default="False",
					  action="store_true", help="set virtual machine net adapter to nat")
	parser.add_option("-N", "--net-host", dest="nethost", default="",
					  help="set virtual machine net adapter to host")
	parser.add_option("-m", "--mac-adress", dest="macaddr", default="",
					  help="set virtual machine mac adress")
	parser.add_option("-a", "--shared-folder", dest="shared", default="",
					  help="set host chared folder")

	(options, args) = parser.parse_args()

	# Check arguments compatibility
	if options.vm == "":
		parser.error("You must specify a virtual machine...")

	if options.home == "":
		parser.error("You must specify a home directory...")

	if options.netnat == True and options.nethost != "":
		parser.error("Can not specify nat network and host network simultaneous...")

	# Init virtual machine
	virtual_box = VBoxConfiguration(options.home)
	virtual_box.set_machine(options.vm)
	
	if options.raw != "":
		if options.uuid == "":
			parser.error("You must specify raw vmdk uuid")
		virtual_box.set_raw_vmdk (options.raw, options.uuid, int(options.order))

	if options.dvd != "":
		virtual_box.set_dvd_image (options.dvd)
	
	if options.boot != "":
		virtual_box.machine.set_boot_device (options.boot)
	
	if options.ram != "":
		virtual_box.machine.set_ram_size (options.ram)
	
	if options.resolution != "":
		virtual_box.machine.set_resolution(options.resolution)
	
	if options.fullscreen == True:
		virtual_box.machine.set_fullscreen()
	
	if options.logo != "":
		virtual_box.machine.set_logo_image(options.logo)
		
	if options.netnat == True:
		virtual_box.machine.set_net_adapter_to_nat()

	if options.nethost != "":
		virtual_box.machine.set_net_adapter_to_host (options.nethost)

	if options.macaddr != "":
		virtual_box.machine.set_mac_address (options.macaddr)
	
	if options.shared != "":
		virtual_box.machine.set_shared_folder (options.shared)

	# Write changes
	virtual_box.write()
	virtual_box.machine.write()

