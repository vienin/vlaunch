#!/usr/bin/env python

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


import sys
import xml.dom.minidom as dom
import uuid as uuid_lib
import os
from optparse import OptionParser
import logging
import shutil

def set_xml_attr (xmlfile, element, attr, value):	
	xml = dom.parse(xmlfile)
	element = xml.getElementsByTagName(element)[0]
	element.setAttribute(attr, value)
	open(xmlfile, 'w').write(xml.toxml())
	
# CREATE VM SCRIPT

usage = "%prog -v vm_name -o vbox_user_home (full path) [ -s WIN|MAC ][ -f virtual_disk_file -t virtual_disk_format (VDI|VMDK)]"
description = "Create a virtual box user home with specified vm"
version="%prog 0.1"

# Define options
parser = OptionParser(usage=usage, description=description, version=version)
parser.add_option("-o", "--vbox-user-home", dest="home", default="",
                  help="virtual box home directory")
parser.add_option("-v", "--virtual-machine", dest="vm", default="",
                  help="virtual machine name")
parser.add_option("-f", "--disk-file", dest="hd", default="",
                  help="virtual disk file path")
parser.add_option("-t", "--disk-format", dest="type", default="VMDK",
                  help="virtual disk format")
parser.add_option("-s", "--os", dest="os", default="LIN",
                  help="target os type") 
(options, args) = parser.parse_args()

if options.vm == "" or options.home == "":
	parser.error("You must specify a vbox uer home and the machine name")

# redirect vbox user home
os.environ["VBOX_USER_HOME"] = options.home

# create vm
print ("VBoxManage createvm -name " + options.vm + " -ostype Fedora -register")
os.system("VBoxManage createvm -name " + options.vm + " -ostype Fedora -register")
os.system("VBoxManage modifyvm " + options.vm + " -ioapic on -boot1 disk -boot2 none -boot3 none -vram 32 -memory 1024 -nictype1 82540EM -biosbootmenu disabled -audio pulse") # -usb on -usbehci on

# add disk
if options.hd != "":
	os.system("VBoxManage openmedium disk " + options.hd)
	os.system("VBoxManage modifyvm " + options.vm + " -hda " + options.hd)
	
	# Update virtual disk path from absolute to relative
	os.mkdir(os.path.join(options.home, "HardDisks"))
	#shutil.copy(options.hd, os.path.join(options.home, "HardDisks"))
	set_xml_attr(os.path.join(options.home, "VirtualBox.xml"), "HardDisk",
		 "location", os.path.join("HardDisks", os.path.basename(options.hd)))
	set_xml_attr(os.path.join(options.home, "VirtualBox.xml"), "HardDisk",
		 "format", os.path.basename(options.type))

# setting virtual box extradatas
os.system('VBoxManage setextradata global "GUI/MaxGuestResolution" "any"')
os.system('VBoxManage setextradata global "GUI/Input/AutoCapture" "true"')
os.system('VBoxManage setextradata global "GUI/SuppressMessages" ",remindAboutAutoCapture,confirmInputCapture,remindAboutMouseIntegrationOn,remindAboutMouseIntegrationOff,remindAboutInaccessibleMedia,remindAboutWrongColorDepth,confirmGoingFullscreen"')
os.system('VBoxManage setextradata global "GUI/TrayIcon/Enabled" "false"')
os.system('VBoxManage setextradata global "GUI/UpdateCheckCount" "2"')
os.system('VBoxManage setextradata global "GUI/UpdateDate" "never"')

# setting virtual machine extradatas
os.system('VBoxManage setextradata ' + options.vm + ' "GUI/SaveMountedAtRuntime" "false"')
os.system('VBoxManage setextradata ' + options.vm + ' "GUI/Fullscreen" "on"')
os.system('VBoxManage setextradata ' + options.vm + ' "GUI/Seamless" "off"')
os.system('VBoxManage setextradata ' + options.vm + ' "GUI/LastCloseAction" "powerOff"')
os.system('VBoxManage setextradata ' + options.vm + ' "GUI/AutoresizeGuest" "on"')

# workaround until we deploy multi-platform build infrastructure
if options.os == "WIN":
	set_xml_attr(os.path.join(options.home, "Machines", options.vm, options.vm + ".xml"), "AudioAdapter",
		 "driver", "DirectSound")
	set_xml_attr(os.path.join(options.home, "Machines", options.vm, options.vm + ".xml"), "VirtualBox",
		 "version", "1.7-windows")
	set_xml_attr(os.path.join(options.home, "VirtualBox.xml"), "VirtualBox",
		 "version", "1.7-windows")
		 
if options.os == "MAC":
	set_xml_attr(os.path.join(options.home, "Machines", options.vm, options.vm + ".xml"), "AudioAdapter",
		 "driver", "CoreAudio")
	set_xml_attr(os.path.join(options.home, "Machines", options.vm, options.vm + ".xml"), "VirtualBox",
		 "version", "1.7-macosx")
	set_xml_attr(os.path.join(options.home, "VirtualBox.xml"), "VirtualBox",
		 "version", "1.7-macosx")
