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


import os, os.path as path, sys
from ConfigParser import ConfigParser, NoOptionError
from optparse import OptionParser
import utils
import gettext

AUTO_INTEGER = -1
AUTO_STRING  = "auto"

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
parser.add_option("-s", "--settings", dest="settings", default=False,
                  action="store_true", help="launch only settings dialog")
(options, args) = parser.parse_args(args=args)

STATUS_NORMAL = 0
STATUS_IGNORE = 1
STATUS_GUEST  = 2
STATUS_EXIT   = 3

NET_HOST  = 1
NET_NAT   = 2

resolutionValues    = { '4:3'  : ['1400x1050', '1280x1024', '1024x768', '800x600', '640x480'],
                        '16:9' : ['1680x1050', '1280x960', '832x624', '700x525', '512x384'] }
reintegrationValues = [ 'overlay=ext4=UUID=b07ac827-ce0c-4741-ae81-1f234377b4b5', 
                        'overlay=tmpfs', 
                        'overlay=' ]
languageValues      = [ 'fr_FR', 'en_US' ]

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
          "autofullscreen" : False,
          "autominimize" : True,
          "language" : AUTO_STRING,
          "ballooncolor" : "#FFFFE7",
          "ballooncolorgradient" : "#FFFFE7",
          "ballooncolortext" : "#000000",
          "smartkey" : False,
          "lockatexit" : False,
          "voice" : False,
        },
      "rawdisk" :
        {
          "dev" : "",
          "parts" : "all",
          "rootuuid" : "",
          "volume" : "",
          "model" : "",
          "compress" : False
        },
      "vm" :
        {
          "vm" : "UFO",
          "os" : "Fedora",
          "nettype" : 2,
          "hostnet" : "",
          "macaddr" : "",
          "ramsize" : AUTO_INTEGER,
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
          "cpus" : 1,
          "resolution" : resolutionValues['4:3'][3],
          "pae" : True,
          "vt" : True,
          "nestedpaging" : True,
          "accel3d" : True,
          "menubar" : False,
          "rootvdi" : "",
          "cmdline" : "ro 4",
          "reintegration" : reintegrationValues[0],
          "guestdebug" : False
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
    conf_file = ""

print "Using configuration file:", conf_file

for section, keys in config.items():
    if not cp.has_section(section):   
        cp.add_section(section)
    for key, default in keys.items():
        try:
            if type(default) == bool:
                globals()[key.upper()] = type(default)(int(cp.get(section, key)))
            else:
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
ROOTVDI = make_path(DATA_DIR, ROOTVDI)

try:
    gettext.translation('vlaunch', path.join(DATA_DIR, "locale"), languages=[LANGUAGE]).install(unicode=True)
except:
    print "Could find a translation for " + LANGUAGE
    print "Available translations", gettext.find("vlaunch", localedir=path.join(DATA_DIR, "locale"), all=1), "in", path.join(DATA_DIR, "locale")
    gettext.install('vlaunch')


"""
Here is a dictionary based model to represent settings dialog window.

Available settings are organized in many main tabs (categories),
each one contains a list of settings or group of settings (one setting
for one configuration variable)
"""

reintegrationStrings = [ _('Host disk'), _('Memory'), _('Direct') ]
languageStrings      = [ _('French'), _('English') ]

settings = \
    [ 
      { 'tabname'  : _("Behavior"),
        'iconfile' : "behavior.png",     
        'settings' : 
          [ 
            { 'confid' : "resolution",
              'sectid' : "vm",
              'short'  : _("Window resolution"),
              'label'  : _("Choose the starting resolution of the window.\n"
                           "Note that if the chosen resolution is higher or equal than the\n"
                           "computer one, the window will be displayed in fullscreen mode."),
              'values' : resolutionValues 
            },
            { 'confid' : "voice",
              'sectid' : "launcher",
              'short'  : _("Activate voice"),
              'label'  : _("Enable this option if you want to turn on voice synthesis.")
            },
            { 'confid' : "autofullscreen",
              'sectid' : "launcher",
              'short'  : _("Fullscreen automatic"),
              'label'  : _("Enable this option if you want the window switch to fullscreen\n"
                           "mode at login.")
            },
            { 'confid' : "autominimize",
              'sectid' : "launcher",
              'short'  : _("Minimize automatic"),
              'label'  : _("Enable this option if you want the window switch to minimized\n"
                           "mode at startup and shutdown.")
            }
          ]
      },
      { 'tabname'  : _("Appearance"),
        'iconfile' : "graphics.png", 
        'settings' : 
          [ 
            { 'confid' : "language",
              'sectid' : "launcher",
              'short'  : _("Language"),
              'label'  : _("Choose your language."),
              'values' : languageValues,
              'strgs'  : languageStrings,
              'reboot' : True

            },
            { 'confid' : "menubar",
              'sectid' : "vm",
              'short'  : _("Menu bar"),
              'label'  : _("Display/hide the window menu bar."),
            },
            { 'grpid'  : "ballooncolors",
              'group'  : [ 
                           { 'confid' : "ballooncolor",
                             'sectid' : "launcher",
                             'short'  : _("Balloon top color")
                           },
                           { 'confid' : "ballooncolorgradient",
                             'sectid' : "launcher",
                             'short'  : _("Balloon bottom color")
                           },
                           { 'confid' : "ballooncolortext",
                             'sectid' : "launcher",
                             'short'  : _("Balloon text color")
                           }
                         ],
              'label'  : _("Customize colors of the balloon message window. Use different\n"
                           "collors for top and bottom to get a color gradient.")
            }
          ]
      },
      { 'tabname'  : _("Advanced"),
        'iconfile' : "advanced.png",
        'settings' : 
          [ 
            { 'confid' : "ramsize",
              'sectid' : "vm",
              'short'  : _("Memory"),
              'label'  : _("Set the size of the virtual machine memory."),
              'range'  : [MINRAM, 4096],
              'autocb' : True,
              'reboot' : True
            },
            { 'confid' : "cpus",
              'sectid' : "vm",
              'short'  : _("CPU number"),
              'label'  : _("Set the number of cpus connected to the virtual machine."),
              'range'  : [1, 16],
              'autocb' : True,
              'reboot' : True
            },
            { 'confid' : "accel3d",
              'sectid' : "vm",
              'short'  : _("3D acceleration"),
              'label'  : _("Set the 3D acceleration capability. Even if 3D is enabled,\n"
                           "availability of this feature depends of the host computer 3D\n"
                           "device."),
              'reboot' : True
            },
            { 'grpid'  : "virtext",
              'group'  : [ 
                           { 'confid' : "vt",
                             'sectid' : "vm",
                             'short'  : _("VT-x/AMD-V")
                           },
                           { 'confid' : "nestedpaging",
                             'sectid' : "vm",
                             'short'  : _("Nested paging")
                           }
                         ],
              'label'  : _("Set the virtualization extentions. Even if virtualizatuion\n"
                           "extentions are enabled, availability of this feature depends\n"
                           "of the host computer cpu properties."),
              'reboot' : True
            },
          ]
      },
      { 'tabname'  : _("System"),
        'iconfile' : "system.png",
        'settings' : 
          [ 
            { 'confid' : "guestdebug",
              'sectid' : "vm",
              'short'  : _("Debug mode"),
              'label'  : _("Set debug mode to get more complete log files.")
            },
            { 'confid' : "reintegration",
              'sectid' : "vm",
              'short'  : _("Reintegration policy"),
              'label'  : _("DANGEROUS. Select the reintegration policy.\n"
                           "The reintegration policy defines how system modifications\n"
                           "are written on the removable device."),
              'values' : reintegrationValues,
              'strgs'  : reintegrationStrings,
              'reboot' : True
            },
            { 'confid' : "cmdline",
              'sectid' : "vm",
              'short'  : _("Kernel command line"),
              'label'  : _("DANGEROUS. Set the kernel command line parameters.\n"
                           "If the following parameters already exist on the kernel\n"
                           "command line, they will be overwritten.")
            }
          ]
      }
    ]
        
def get_auto_value(type_instance):
    assert type(type_instance) != bool
    
    if type(type_instance) == int:
        return AUTO_INTEGER
    elif type(type_instance) == str:
        return AUTO_STRING

def get_default_value(id):
    for k, v in config.items():
        if id in v:
            return v[id]
        
def write_value_to_file(section, id, value):
    cp = ConfigParser()
    cp.read(conf_file)
    if not cp.has_section(section):
        cp.add_section(section)
    cp.set(section, id, value)
    cp.write(open(conf_file, "w"))
