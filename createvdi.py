#!/usr/bin/env python

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

