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

def set_xml_attr (xmlfile, element, attr, value):	
	xml = dom.parse(xmlfile)
	element = xml.getElementsByTagName(element)[0]
	element.setAttribute(attr, value)
	open(xmlfile, 'w').write(xml.toxml())
	
# CREATE VM SCRIPT

usage = "%prog -v vm_name -o vbox_user_home (full path) -n vdi_name [ -s size ] [ -c configuration_file ] [ -t type_name ] [ --conf-only ]"
description = "Create a dinamic vdi file, may add it to a configuration file"
version="%prog 0.1"
    
# Define options
parser = OptionParser(usage=usage, description=description, version=version)
parser.add_option("-o", "--vbox-user-home", dest="home", default="",
                  help="virtual box home directory")
parser.add_option("-n", "--name", dest="name", default="",
                  help="vdi name")
parser.add_option("-t", "--type-name", dest="type", default="",
                  help="vdi name")
parser.add_option("-s", "--size", dest="size", default="500",
                  help="vdi size")
parser.add_option("-c", "--conf", dest="conf", default="",
                  help="ufo key configuration file")
parser.add_option("-y", "--conf-only", dest="confonly", default=False,
                  action="store_true", help="add uuid to configuration file only")
(options, args) = parser.parse_args()		
		  
if options.home == "" and options.confonly == False:
	parser.error("You must specify a vbox user home and the vdi name")
	
if options.conf and options.type == "":
	parser.error("You must specify a type name if configuration file is set")
	
if options.confonly and options.name == "":
	parser.error("You must set --uuid if --conf-only is set")

if options.confonly == False:
    # redirect vbox user home
    os.environ["VBOX_USER_HOME"] = options.home

    # create vm
    print ("VBoxManage -nologo createhd --filename " + options.name + " --size " + options.size + " --format VDI --variant Standard --remember | grep UUID")
    output = commands.getoutput("VBoxManage -nologo createhd --filename " + options.name + " --size " + options.size + " --format VDI --variant Standard --remember | grep UUID")

if options.conf:
    if options.confonly:
	    # generate a new uuid
        uuid_output = commands.getoutput("VBoxManage -nologo internalcommands sethduuid ufo_overlay.vdi")
        uuid = uuid_output[uuid_output.find("UUID changed to: ") + len("UUID changed to: "):]
    else:
        uuid = output[output.find("UUID: ") + 6:].strip()

    print ("Adding " + options.type + "uuid=" + uuid + " to " + options.conf) 
    cp = ConfigParser()
    conf = options.conf
    cp.read(conf)
    cp.set("vm", options.type + "uuid", uuid)
    cp.write(open(conf, "w"))
