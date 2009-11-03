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
import commands
import xml.dom.minidom as dom
import uuid as uuid_lib
import os
from ConfigParser import ConfigParser, SafeConfigParser
from optparse import OptionParser
import logging
import shutil

usage = "%prog -p vdi_path [ -s size ]"
description = "Create a dinamic vdi file, may add it to a configuration file"
version="%prog 0.1"
    
# Define options
parser = OptionParser(usage=usage, description=description, version=version)
parser.add_option("-p", "--path", dest="path", default="",
                  help="vdi path")
parser.add_option("-s", "--size", dest="size", default="500",
                  help="vdi size")
(options, args) = parser.parse_args()		
	
if not options.path:
	parser.error("You must specify a vdi file path")

print ("VBoxManage -nologo createhd --filename " + options.path + " --size " + options.size + " --format VDI --variant Standard --remember")
os.system("VBoxManage -nologo createhd --filename " + options.path + " --size " + options.size + " --format VDI --variant Standard --remember")

