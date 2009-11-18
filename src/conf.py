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
from ConfigParser import ConfigParser
from optparse import OptionParser

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

globalsection = "virtualbox"
launchersection = "launcher"
rawdisksection = "rawdisk"
vmsection = "vm"
guestsection = "guest"
startvmkey = "STARTVM"
vmkey = "VM"
oskey = "OS"
vmdkkey = "VMDK"
partskey = "PARTS"
bootfloppykey = "BOOTFLOPPY"
bootisokey = "BOOTISO"
nettypekey = "NETTYPE"
hostnetkey = "HOSTNET"
macaddrkey = "MACADDR"
ramsizekey = "RAMSIZE"
minramkey = "MINRAM"
kioskmodekey = "KIOSKMODE"
widthkey = "WIDTH"
heightkey = "HEIGHT"
driverankkey = "DRIVERANK"
swapfile = "SWAPFILE"
swapsize = "SWAPSIZE"
overlayfile = "OVERLAYFILE"
needdevkey = "NEEDDEV"
debugkey = "DEBUG"
devkey = "DEV"
modelkey = "MODEL"
rootuuidkey = "ROOTUUID"
volumekey = "VOLUME"
logkey = "LOG"
imgdirkey = "IMGDIR"
versionkey = "VERSION"
licensekey = "LICENSE"
configurevmkey = "CONFIGUREVM"
homekey = "HOME"
binkey = "BIN"
reporturlkey = "REPORTURL"
useservicekey = "USESERVICE"
createsrvskey = "CREATESRVS"
startsrvskey = "STARTSRVS"
uninstalldriverskey = "UNINSTALLDRIVERS"
noupdatekey = "NOUPDATE"
livecdkey = "LIVECD"
bootdiskkey = "BOOTDISK"
bootdiskuuidkey = "BOOTDISKUUID"
isourlkey = "ISOURL"
updateurlkey = "UPDATEURL"
vboxdriverskey = "VBOXDRIVERS"
cpuskey = "CPUS"
userkey = "USER"

cp = ConfigParser(defaults = { logkey : "logs/launcher.log",
                               imgdirkey : "images",
                               startvmkey : "1",
                               vmkey : "UFO",
                               oskey : "Fedora",
                               vmdkkey : ".VirtualBox/HardDisks/ufo_key.vmdk",
                               partskey : "all",
                               bootfloppykey : ".VirtualBox/Images/UFO-VirtualBox-boot.img",
                               bootisokey : "",
                               swapfile : ".VirtualBox/HardDisks/ufo_swap.vdi",
                               swapsize : "512",
                               overlayfile : ".VirtualBox/HardDisks/ufo_overlay.vdi",
                               nettypekey : "2",
                               hostnetkey : "",
                               macaddrkey : "",
                               ramsizekey : "auto",
                               minramkey : "256",
                               kioskmodekey : "0",
                               heightkey : "full",
                               widthkey : "full",
                               driverankkey : "0",
                               configurevmkey : "1",
                               needdevkey : "0",
                               debugkey : "0",
                               devkey : "",
                               modelkey : "",
                               volumekey : "UFO",
                               rootuuidkey : "",
                               binkey : "",
                               reporturlkey : "http://reporting.agorabox.org/services/reporting",
                               homekey : ".VirtualBox",
                               useservicekey : "0",
                               createsrvskey : "1",
                               startsrvskey : "1",
                               uninstalldriverskey : "0",
                               versionkey : "0",
                               licensekey : "0",
                               noupdatekey : "0",
                               livecdkey : "0",
                               bootdiskuuidkey : "",
                               bootdiskkey : "",
                               isourlkey : "http://downloads.agorabox.org/launcher/latest",
                               updateurlkey : "http://downloads.agorabox.org/launcher/",
                               vboxdriverskey : "drivers\\VBoxDrv",
                               cpuskey : "1",
                               userkey : ""
                             })
                             
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

LIVECD = int(cp.get(launchersection, livecdkey))
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
        BIN = "/usr/lib/virtualbox"

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

def make_path(base, section, key):
    value = cp.get(section, key)
    if value:
        return path.normpath(path.join(base,path.expanduser(value)))
    return ""

# Is BIN overridden in settings.conf ?
bin  = cp.get(globalsection, binkey)
if bin: BIN = path.join(DATA_DIR, bin)

HOME = path.join(DATA_DIR, cp.get(globalsection, homekey))
VMDK = cp.get(globalsection, vmdkkey)

if not cp.has_section(launchersection):
    cp.add_section(launchersection)
USESERVICE = int(cp.get(launchersection, useservicekey))
CREATESRVS = int(cp.get(launchersection, createsrvskey))
STARTSRVS = int(cp.get(launchersection, startsrvskey))
STARTVM = int(cp.get(launchersection, startvmkey))
NEEDDEV = int(cp.get(launchersection, needdevkey))
DEBUG = int(cp.get(launchersection, debugkey))
REPORTURL = cp.get(launchersection, reporturlkey)
LOG = path.join(DATA_DIR, cp.get(launchersection, logkey))
IMGDIR = path.join(DATA_DIR, cp.get(launchersection, imgdirkey))
VERSION = cp.get(launchersection, versionkey)
LICENSE = int(cp.get(launchersection, licensekey))
CONFIGUREVM = int(cp.get(launchersection, configurevmkey))
UNINSTALLDRIVERS = int(cp.get(launchersection, uninstalldriverskey))
NOUPDATE = int(cp.get(launchersection, noupdatekey))
ISOURL = cp.get(launchersection, isourlkey)
UPDATEURL = cp.get(launchersection, updateurlkey)
VBOXDRIVERS = make_path(BIN, launchersection, vboxdriverskey)

if not cp.has_section(rawdisksection):
    cp.add_section(rawdisksection)
DEV = cp.get(rawdisksection, devkey)
PARTS = cp.get(rawdisksection, partskey)
ROOTUUID = cp.get(rawdisksection, rootuuidkey)
VOLUME = cp.get(rawdisksection, volumekey)
MODEL = cp.get(rawdisksection, modelkey)

if not cp.has_section(vmsection):
    cp.add_section(vmsection)
VM = cp.get(vmsection, vmkey)
OS = cp.get(vmsection, oskey)
BOOTFLOPPY = make_path(DATA_DIR, vmsection, bootfloppykey)
BOOTISO = make_path(DATA_DIR, vmsection, bootisokey)
NETTYPE = int(cp.get(vmsection, nettypekey))
HOSTNET = cp.get(vmsection, hostnetkey)
MACADDR = cp.get(vmsection, macaddrkey)
RAMSIZE = cp.get(vmsection, ramsizekey)
MINRAM = int(cp.get(vmsection, minramkey))
KIOSKMODE = int(cp.get(vmsection, kioskmodekey))
DRIVERANK = int(cp.get(vmsection, driverankkey))
SWAPFILE  = make_path(DATA_DIR, vmsection, swapfile)
SWAPSIZE  = int(cp.get(vmsection, swapsize))
OVERLAYFILE  = make_path(DATA_DIR, vmsection, overlayfile)
BOOTDISK = make_path(DATA_DIR, vmsection, bootdiskkey)
BOOTDISKUUID = cp.get(vmsection, bootdiskuuidkey)
CPUS = cp.get(vmsection, cpuskey)

WIDTH = cp.get(vmsection, widthkey)
HEIGHT = cp.get(vmsection, heightkey)

if not cp.has_section(guestsection):
    cp.add_section(guestsection)
USER = cp.get(guestsection, userkey)
