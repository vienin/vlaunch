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

path.supports_unicode_filenames = True

args = [ arg for arg in sys.argv[1:] if not arg.startswith("-psn_") ]
parser = OptionParser()
parser.add_option("-u", "--update", dest="update",
                  help="update a UFO launcher located in ", metavar="FOLDER")
parser.add_option("-d", "--dd", dest="dd", default=False,
                  action="store_true", help="Launch the UFO creator")
parser.add_option("-r", "--respawn", dest="respawn", default=False,
                  action="store_true", help="tells the launcher that it has been respawned ")
parser.add_option("--relaunch", dest="relaunch", default="",
                  help="tells the launcher about the program to relaunch")
parser.add_option("-s", "--settings", dest="settings", default=False,
                  action="store_true", help="launch only settings dialog")

(options, args) = parser.parse_args(args=args)

class GuestProperty:
    def __init__(self, default, name, value=None):
        self.default = default
        self.name = name
        if value:
            self.value = value
        else:
            self.value = default

    def get_default(self):
        return self.default

    def get_name(self):
        return self.name

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def __repr__(self):
        if type(self.value) == bool:
            return str(int(self.value))
        else:
            return str(self.value)

class Conf(object):
    AUTO_INTEGER = -1
    AUTO_STRING  = "auto"

    STATUS_NORMAL = 0
    STATUS_IGNORE = 1
    STATUS_GUEST  = 2
    STATUS_EXIT   = 3

    NET_HOST  = 1
    NET_NAT   = 2

    resolutionValues     = { '4:3'  : ['1400x1050', '1280x1024', '1024x768', '800x600', '640x480'],
                              '16:9' : ['1680x1050', '1280x960', '832x624', '700x525', '512x384'] }
    reintegrationValues  = [ 'overlay=ext4=UUID=b07ac827-ce0c-4741-ae81-1f234377b4b5',
                             'overlay=tmpfs',
                             'overlay=' ]
    languageValues       = [ 'fr_FR', 'en_US' ]
    guiValues            = [ "gnome", "cairo-dock", "moblin" ]

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
          "imgurl" : "http://downloads.agorabox.org/img/latest",
          "isourl" : "http://downloads.agorabox.org/iso/latest",
          "updateurl" : "http://downloads.agorabox.org/launcher/",
          "vboxdrivers" : "drivers\\VBoxDrv",
          "livecd" : 0,
          "hostkey" : 0,
          "autofullscreen" : False,
          "autominimize" : True,
          "defaultlanguage" : "en_US",
          "language" : AUTO_STRING,
          "ballooncolor" : "#FFFFE7",
          "ballooncolorgradient" : "#FFFFE7",
          "ballooncolortext" : "#000000",
          "smartkey" : False,
          "lockatexit" : False,
          "voice" : False,
          "ejectatexit" : False,
          "proxyhttp" : GuestProperty(AUTO_STRING, "/UFO/Proxy/HTTP"),
          "proxyhttps" : GuestProperty(AUTO_STRING, "/UFO/Proxy/HTTPS"),
          "proxyftp" : GuestProperty(AUTO_STRING, "/UFO/Proxy/FTP"),
          "proxysocks" : GuestProperty(AUTO_STRING, "/UFO/Proxy/SOCKS"),
          "linuxexe" : "Gdium Mobile PC",
          "windowsexe" : "Gdium Mobile PC.exe",
          "macexe" : "Gdium Mobile PC.app/Contents/MacOS/UFO",
          "productname" : "Gdium Mobile PC",
          "publicpartname" : "MOBILEPC",
          "firstlaunch" : True
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
          "vm" : "Gdium Mobile PC",
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
          "cmdline" : "rhgb ro quiet 4",
          "reintegration" : reintegrationValues[2],
          "guestdebug" : GuestProperty(False, "/UFO/Debug"),
          "guestmode" : False,
          "guestuser" : "guest",
          "gui" : GuestProperty(guiValues[0], "/UFO/GUI")
        },
      "guest" :
        {
          "user" : ""
        }
    }

    def __init__(self):
        self.handlers = []
        if sys.platform == "darwin" and getattr(sys, "frozen", None):
            self.SCRIPT_PATH = path.realpath(path.join(path.dirname(sys.argv[0]), "..", "MacOS", "UFO"))
        else:
            self.SCRIPT_PATH = path.realpath(sys.argv[0])
        self.SCRIPT_NAME = path.basename(sys.argv[0])
        self.SCRIPT_DIR  = path.dirname(path.realpath(sys.argv[0]))

        print "SCRIPT_PATH", self.SCRIPT_PATH

        self.load()

    def make_path(self, base, value):
        if value:
            return path.normpath(path.join(base,path.expanduser(value)))
        else:
            return ""

    def register_handler(self, handler):
        self.handlers.append(handler)
        
    def unregister_handler(self, handler):
        self.handlers.remove(handler)

    def __getattribute__(self, attr):
        value = None
        for k, v in Conf.config.items():
            if attr.lower() in v:
                value = v[attr.lower()]
        if isinstance(value, GuestProperty):
            return object.__getattribute__(self, attr.lower()).get_value()
        try:
            return object.__getattribute__(self, attr)
        except:
            return object.__getattribute__(self, attr.lower())

    def __setattr__(self, attr, value):
        attr = attr.lower()
        prop = None
        for k, v in Conf.config.items():
            if attr.lower() in v:
                prop = v[attr.lower()]
        if isinstance(prop, GuestProperty):
            if isinstance(value, GuestProperty):
                value = value.get_value()
            newprop = GuestProperty(prop.default, prop.name, value)
            self.__dict__[attr] = newprop
            for handler in self.handlers:
                handler(prop.name, str(newprop))
        else:
            self.__dict__[attr] = value

    def find_data_directory(self, initial_path):
        try:
            last_path = ""
            current_path = initial_path
            while current_path != last_path:
                if os.path.exists(os.path.join(current_path, ".data")):
                    return os.path.join(current_path, ".data")
                last_path = current_path
                current_path = os.path.dirname(current_path)
        except:
            return ""
 
    def load(self):
        # Searching data directory
        self.DATA_DIR = self.find_data_directory(self.SCRIPT_DIR)

        # Searching settings file
        self.cp = ConfigParser()
        self.options = options
        try:
            files = [path.join(self.SCRIPT_DIR, "settings.conf"), # Used on Mac OS LiveCD
                     path.join(self.DATA_DIR, "settings", "settings.conf")] # Linux - Normal case
            if os.environ.has_key("_MEIPASS2"): # Used on Windows & Linux Live
                files.append(path.join(os.environ["_MEIPASS2"], "settings.conf"))
            if options.update:
                files.append(path.join(options.update, ".data", "settings", "settings.conf"))
            settings = self.cp.read(files)
            self.conf_file = settings[0]
        except:
            print "Could not read settings.conf"
            # This file will be created if needed
            self.conf_file = path.join(self.SCRIPT_DIR, "settings.conf")

        print "Using configuration file:", self.conf_file

        for section, keys in self.config.items():
            if not self.cp.has_section(section):
                self.cp.add_section(section)
            for key, default in keys.items():
                if isinstance(default, GuestProperty):
                    default = default.default
                try:
                    if type(default) == bool:
                        setattr(self, key.upper(), type(default)(int(self.cp.get(section, key))))
                    else:
                        setattr(self, key.upper(), type(default)(self.cp.get(section, key)))
                except NoOptionError, err:
                    setattr(self, key.upper(), default)

        # Adjusting paths as operating system type
        self.BIN = ""
        if sys.platform == "linux2":
            if self.LIVECD:
                self.DATA_DIR = os.environ["_MEIPASS2"]
                # no BIN as the livecd always provides a settings.conf
            else:
                vbox_path = utils.call(["which", "VirtualBox"], output=True, log=False)[1].strip()
                if not path.lexists(vbox_path): self.BIN = ""
                else: self.BIN = path.dirname(vbox_path)

        elif sys.platform == "darwin":
            if self.LIVECD:
                self.DATA_DIR = path.join(path.dirname(self.SCRIPT_PATH), "..", "Resources", ".data")
            self.BIN = path.join(self.SCRIPT_DIR, "..", "Resources", "VirtualBox.app", "Contents", "MacOS")

        else:
            if self.LIVECD or os.environ.has_key("_MEIPASS2"):
                self.DATA_DIR = os.environ["_MEIPASS2"]
                # no BIN as the livecd always provides a settings.conf
            else:
                self.BIN = path.join(self.SCRIPT_DIR)

        if not self.DATA_DIR:
            print "Could not find data directory, creating one at " + str(os.path.join(self.SCRIPT_DIR, ".data"))
            os.mkdir(os.path.join(self.SCRIPT_DIR, ".data"))
            self.DATA_DIR = os.path.join(self.SCRIPT_DIR, ".data")

        # Searching locale files
        try:
            gettext.translation('vlaunch', path.join(self.DATA_DIR, "locale"), languages=[self.LANGUAGE]).install(unicode=True)
        except:
            print "Could find a translation for " + self.LANGUAGE
            print "Available translations", gettext.find("vlaunch", localedir=path.join(self.DATA_DIR, "locale"), all=1), "in", path.join(self.DATA_DIR, "locale")
            gettext.install('vlaunch')

        self.setup()

    def reload(self):
        self.load()

    def get_auto_value(self, type_instance):
        assert type(type_instance) != bool

        if type(type_instance) == int:
            return self.AUTO_INTEGER
        elif type(type_instance) == str:
            return self.AUTO_STRING

    def get_all_guestprops(self):
        guestprops = []
        for k, v in self.config.items():
            for name, value in v.items():
                if isinstance(value, GuestProperty):
                    guestprops.append(object.__getattribute__(self, name))
        return guestprops

    def get_default_value(self, id):
        for k, v in self.config.items():
            if id in v:
                return v[id]

    def write_value_to_file(self, section, id, value):
        cp = ConfigParser()
        cp.read(self.conf_file)
        if not cp.has_section(section):
            cp.add_section(section)
        cp.set(section, id, value)
        cp.write(open(self.conf_file, "w"))

    def setup(self):
        """
        Here is a dictionary based model to represent settings dialog window.

        Available settings are organized in many main tabs (categories),
        each one contains a list of settings or group of settings (one setting
        for one configuration variable)
        """

        self.reintegrationStrings = [ _('Host disk'), _('Memory'), _('Direct') ]
        self.languageStrings      = [ _('French'), _('English') ]
        self.guiStrings           = [ _('GNOME'), _('Cairo-dock'), _("Moblin") ]

        self.settings = [ \
          { 'tabname'  : _("Behavior"),
            'iconfile' : "behavior.png",
            'settings' :
              [
                { 'confid' : "resolution",
                  'sectid' : "vm",
                  'short'  : _("Window resolution"),
                  'label'  : _("Choose the starting resolution of the window. "
                               "Note that if the chosen resolution is higher or equal than the "
                               "computer one, the window will be displayed in fullscreen mode."),
                  'values' : self.resolutionValues
                },
                { 'confid' : "voice",
                  'sectid' : "launcher",
                  'short'  : _("Activate voice"),
                  'label'  : _("Enable this option if you want to turn on voice synthesis."),
                  'hide'   : True
                },
                { 'confid' : "autofullscreen",
                  'sectid' : "launcher",
                  'short'  : _("Fullscreen automatic"),
                  'label'  : _("Enable this option if you want the window switch to fullscreen "
                               "mode at login.")
                },
                { 'confid' : "autominimize",
                  'sectid' : "launcher",
                  'short'  : _("Minimize automatic"),
                  'label'  : _("Enable this option if you want the window switch to minimized "
                               "mode at startup and shutdown.")
                },
                { 'confid' : "ejectatexit",
                  'sectid' : "launcher",
                  'short'  : _("Eject key at shutdown"),
                  'label'  : _("Enable this option if you want to eject the key at shutdown.")
                },
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
                  'values' : self.languageValues,
                  'strgs'  : self.languageStrings,
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
                  'label'  : _("Customize colors of the balloon message window. Use different "
                               "collors for top and bottom to get a color gradient.")
                },
                { 'confid' : "gui",
                  'sectid' : "vm",
                  'short'  : _("User interface"),
                  'label'  : _("Select a graphical interface."),
                  'values' : self.guiValues,
                  'strgs'  : self.guiStrings,
                },
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
                  'range'  : [self.MINRAM, 4096],
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
                  'label'  : _("Set the 3D acceleration capability. Even if 3D is enabled, "
                               "availability of this feature depends of the host computer 3D"
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
                  'label'  : _("Set the virtualization extentions. Even if virtualizatuion "
                               "extentions are enabled, availability of this feature depends "
                               "of the host computer cpu properties."),
                  'reboot' : True
                },
              ]
          },
          { 'tabname'  : _("Network"),
            'iconfile' : "proxy.png",
            'settings' :
              [
                { 'grpid'  : "proxies",
                  'group'  : [
                               { 'confid' : "proxyhttp",
                                 'sectid' : "launcher",
                                 'short'  : _("Web proxy"),
                                 'autocb' : True,
                               },
                               { 'confid' : "proxyhttps",
                                 'sectid' : "launcher",
                                 'short'  : _("Secure Web proxy"),
                                 'autocb' : True,
                               },
                               { 'confid' : "proxyftp",
                                 'sectid' : "launcher",
                                 'short'  : _("FTP proxy"),
                                 'autocb' : True,
                               },
                               { 'confid' : "proxysocks",
                                 'sectid' : "launcher",
                                 'short'  : _("SOCKS proxy"),
                                 'autocb' : True,
                               }
                             ],
                  'label'  : _("Use autodetection for proxy servers or configure them manually using <br>format <i>hostname:port</i>")
                }
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
                  'label'  : _("DANGEROUS. Select the reintegration policy. "
                               "The reintegration policy defines how system modifications "
                               "are written on the removable device."),
                  'values' : self.reintegrationValues,
                  'strgs'  : self.reintegrationStrings,
                  'reboot' : True
                },
                { 'confid' : "cmdline",
                  'sectid' : "vm",
                  'short'  : _("Kernel command line"),
                  'label'  : _("DANGEROUS. Set the kernel command line parameters. "
                               "If the following parameters already exist on the kernel "
                               "command line, they will be overwritten.")
                }
              ]
          } ]

        if self.BIN: self.BIN = path.join(self.DATA_DIR, self.BIN)
        self.LOG = path.join(self.DATA_DIR, self.LOG)
        self.IMGDIR = path.join(self.DATA_DIR, self.IMGDIR)
        self.VBOXDRIVERS = self.make_path(self.BIN, self.VBOXDRIVERS)
        self.BOOTFLOPPY = self.make_path(self.DATA_DIR, self.BOOTFLOPPY)
        self.BOOTISO = self.make_path(self.DATA_DIR, self.BOOTISO)
        self.SWAPFILE  = self.make_path(self.DATA_DIR, self.SWAPFILE)
        self.OVERLAYFILE  = self.make_path(self.DATA_DIR, self.OVERLAYFILE)
        self.BOOTDISK = self.make_path(self.DATA_DIR, self.BOOTDISK)
        self.ROOTVDI = self.make_path(self.DATA_DIR, self.ROOTVDI)

conf = Conf()

