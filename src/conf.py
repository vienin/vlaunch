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


import os, os.path as path, sys
from ConfigParser import ConfigParser, NoOptionError
from optparse import OptionParser
import utils

path.supports_unicode_filenames = True

if sys.platform == "darwin" and getattr(sys, "frozen", None):
    SCRIPT_PATH = path.realpath(path.join(path.dirname(sys.argv[0]), "..", "MacOS", "UFO"))
else:
    SCRIPT_PATH = path.realpath(sys.argv[0])
SCRIPT_NAME = path.basename(sys.argv[0])
SCRIPT_DIR  = path.dirname(path.realpath(sys.argv[0]))

print "SCRIPT_PATH", SCRIPT_PATH

args = [ arg for arg in sys.argv[1:] if not arg.startswith("-psn_") ]
parser = OptionParser()
parser.add_option("-u", "--update", dest="update",
                  help="update a UFO launcher located in ", metavar="FOLDER")
parser.add_option("-r", "--respawn", dest="respawn", default=False,
                  action="store_true", help="tells the launcher that it has been respawned ")
parser.add_option("--relaunch", dest="relaunch", default="",
                  help="tells the launcher the program to relaunch")
(options, args) = parser.parse_args(args=args)

STATUS_NORMAL = 0
STATUS_IGNORE = 1
STATUS_GUEST = 2
STATUS_EXIT = 3

NET_LOCAL = 0
NET_HOST = 1
NET_NAT = 2

config = \
    {
      "virtualbox" :
        {
          "home" : ".VirtualBox",
          "bin" : "",
          "vmdk" : ".VirtualBox/HardDisks/ufo_key.vmdk"
        },
      "launcher" :
        {
          "useservice" : 0,
          "createsrvs" : 1,
          "startsrvs" : 1,
          "startvm" : 1,
          "needdev" : 0,
          "debug" : 0,
          "reporturl" : "http://reporting.agorabox.org/services/reporting",
          "log" : "logs/launcher.log",
          "imgdir" : "images",
          "version" : "0.0",
          "license" : 0,
          "configurevm" : 1,
          "uninstalldrivers" : 0,
          "noupdate" : 0,
          "isourl" : "http://downloads.agorabox.org/launcher/latest",
          "updateurl" : "http://downloads.agorabox.org/launcher/",
          "vboxdrivers" : "drivers\\VBoxDrv",
          "livecd" : 0,
          "hostkey" : 0,
          "pae" : True,
          "vt" : True,
          "accel3d" : True
        },
      "rawdisk" :
        {
          "dev" : "",
          "parts" : "all",
          "rootuuid" : "",
          "volume" : "UFO",
          "model" : ""
        },
      "vm" :
        {
          "vm" : "UFO",
          "os" : "Fedora",
          "nettype" : 2,
          "hostnet" : "",
          "macaddr" : "",
          "ramsize" : "auto",
          "minram" : 256,
          "kioskmode" : 0,
          "driverank" : 0,
          "swapfile" : ".VirtualBox/HardDisks/ufo_swap.vdi",
          "swapsize" : 512,
          "overlayfile" : ".VirtualBox/HardDisks/ufo_overlay.vdi",
          "bootdisk" : "",
          "bootdiskuuid" : "",
          "bootfloppy" : ".VirtualBox/Images/UFO-VirtualBox-boot.img",
          "bootiso" : "",
          "cpus" : "1",
          "width" : "800",
          "height" : "600"
        },
      "guest" :
        {
          "user" : ""
        }
    }

cp = ConfigParser()
                             
try:
    files = [path.join(SCRIPT_DIR, "settings.conf"), # Used on Mac OS LiveCD
             path.join(SCRIPT_DIR, "..", ".data", "settings", "settings.conf"), # Windows & Linux - Normal case
             path.join(SCRIPT_DIR, "..", "..", "..", "..", ".data", "settings", "settings.conf")] # Mac - Normal case
    if os.environ.has_key("_MEIPASS2"): # Used on Windows & Linux Live
        files.append(path.join(os.environ["_MEIPASS2"], "settings.conf"))
    if options.update:
        files.append(path.join(options.update, ".data", "settings", "settings.conf"))
    settings = cp.read(files)
    conf_file = settings[0]
except:
    print "Could not read settings.conf"
    raise

print "Using configuration file:", conf_file

for section, keys in config.items():
    if not cp.has_section(section):   
        cp.add_section(section)
    for key, default in keys.items():
        try:
            globals()[key.upper()] = type(default)(cp.get(section, key))
        except NoOptionError, err:
            globals()[key.upper()] = default

if options.update:
    DATA_DIR = path.join(options.update, ".data")
else:
    DATA_DIR = ""
BIN = ""

if sys.platform == "linux2":
    if LIVECD:
        DATA_DIR = os.environ["_MEIPASS2"]
        # no BIN as the livecd always provides a settings.conf
    else:
        if not DATA_DIR: DATA_DIR = path.join(path.dirname(path.dirname(SCRIPT_PATH)), ".data")
        vbox_path = utils.call(["which", "VirtualBox"], output=True, log=False)[1].strip()
        if not path.lexists(vbox_path): BIN = ""
        else: BIN = path.dirname(vbox_path)

elif sys.platform == "darwin":
    if LIVECD:
        DATA_DIR = path.join(path.dirname(SCRIPT_PATH), "..", "Resources", ".data")
    else:
        if not DATA_DIR: DATA_DIR = path.join(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(SCRIPT_PATH))))), ".data")
    BIN = path.join(SCRIPT_DIR, "..", "Resources", "VirtualBox.app", "Contents", "MacOS")

else:
    if LIVECD:
        DATA_DIR = os.environ["_MEIPASS2"]
        # no BIN as the livecd always provides a settings.conf
    else:
        if not DATA_DIR: DATA_DIR = path.join(SCRIPT_DIR, "..", ".data")
        BIN = path.join(SCRIPT_DIR, "bin")

def make_path(base, value):
    if value:
        return path.normpath(path.join(base,path.expanduser(value)))
    else:
        return ""

if BIN: BIN = path.join(DATA_DIR, BIN)
LOG = path.join(DATA_DIR, LOG)
IMGDIR = path.join(DATA_DIR, IMGDIR)
VBOXDRIVERS = make_path(BIN, VBOXDRIVERS)
BOOTFLOPPY = make_path(DATA_DIR, BOOTFLOPPY)
BOOTISO = make_path(DATA_DIR, BOOTISO)
SWAPFILE  = make_path(DATA_DIR, SWAPFILE)
OVERLAYFILE  = make_path(DATA_DIR, OVERLAYFILE)
BOOTDISK = make_path(DATA_DIR, BOOTDISK)
