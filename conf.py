import os, os.path as path, sys
from ConfigParser import ConfigParser

PWD = os.getcwd()
SCRIPT_PATH = path.realpath(sys.argv[0])
SCRIPT_DIR = path.dirname(path.realpath(sys.argv[0]))
if (len(SCRIPT_DIR)-len(SCRIPT_DIR.rsplit("bin",1)[0]) == 3):
    SCRIPT_DIR = SCRIPT_DIR.rsplit("bin",1)[0]
SCRIPT_NAME = path.basename(sys.argv[0])

APP_PATH = SCRIPT_DIR

STATUS_NORMAL = 0
STATUS_IGNORE = 1
STATUS_GUEST = 2
STATUS_EXIT = 3

NET_LOCAL = 0
NET_HOST = 1
NET_NAT = 2

READY = 0

globalsection = "virtualbox"
launchersection = "launcher"
rawdisksection = "rawdisk"
vmsection = "vm"
startvmkey = "STARTVM"
vmkey = "VM"
vmdkkey = "VMDK"
bootisokey = "BOOTISO"
nettypekey = "NETTYPE"
hostnetkey = "HOSTNET"
macaddrkey = "MACADDR"
ramsizekey = "RAMSIZE"
kioskmodekey = "KIOSKMODE"
widthkey = "WIDTH"
heightkey = "HEIGHT"
driverankkey = "DRIVERANK"
swapfile = "SWAPFILE"
swapuuid = "SWAPUUID"
needdevkey = "NEEDDEV"
debugkey = "DEBUG"
devkey = "DEV"
modelkey = "MODEL"
rootuuidkey = "ROOTUUID"
volumekey = "VOLUME"
logkey = "LOG"
versionkey = "VERSION"
configurevmkey = "CONFIGUREVM"
homekey = "HOME"
binkey = "BIN"
vmdkkey = "VMDK"
useservicekey = "USESERVICE"
createsrvskey = "CREATESRVS"
startsrvskey = "STARTSRVS"
uninstalldriverskey = "UNINSTALLDRIVERS"

cp = ConfigParser(defaults = { logkey : "launcher.log",
                               startvmkey : "1",
                               vmkey : "UFO",
                               vmdkkey : "ufo_key.vmdk",
                               bootisokey : "UFO-VirtualBox-boot.img",
                               swapuuid : "",
                               swapfile : "ufo_swap.vdi",
                               nettypekey : "2",
                               hostnetkey : "",
                               macaddrkey : "",
                               ramsizekey : "auto",
                               kioskmodekey : "0",
                               heightkey : "",
                               widthkey : "",
                               driverankkey : "0",
                               configurevmkey : "1",
                               needdevkey : "0",
                               debugkey : "0",
                               devkey : "",
                               modelkey : "",
                               volumekey : "",
                               rootuuidkey : "",
                               binkey : "",
                               homekey : "",
                               useservicekey : "0",
                               createsrvskey : "0",
                               startsrvskey : "0",
                               uninstalldriverskey : "0",
                               versionkey : "0"
                             })
cp.read([path.join(SCRIPT_DIR, "settings.conf"), path.join(SCRIPT_DIR, "settings", "settings.conf")])

HOME = cp.get(globalsection, homekey)
VMDK = cp.get(globalsection, vmdkkey)
BIN = cp.get(globalsection, binkey)

USESERVICE = int(cp.get(launchersection, useservicekey))
CREATESRVS = int(cp.get(launchersection, createsrvskey))
STARTSRVS = int(cp.get(launchersection, startsrvskey))
STARTVM = int(cp.get(launchersection, startvmkey))
NEEDDEV = int(cp.get(launchersection, needdevkey))
DEBUG = int(cp.get(launchersection, debugkey))
LOG = cp.get(launchersection, logkey)
VERSION = int(cp.get(launchersection, versionkey))
CONFIGUREVM = int(cp.get(launchersection, configurevmkey))
UNINSTALLDRIVERS = int(cp.get(launchersection, uninstalldriverskey))

DEV = cp.get(rawdisksection, devkey)
ROOTUUID = cp.get(rawdisksection, rootuuidkey)
VOLUME = cp.get(rawdisksection, volumekey)
MODEL = cp.get(rawdisksection, modelkey)

VM = cp.get(vmsection, vmkey)
BOOTISO = cp.get(vmsection, bootisokey)
NETTYPE = int(cp.get(vmsection, nettypekey))
HOSTNET = cp.get(vmsection, hostnetkey)
MACADDR = cp.get(vmsection, macaddrkey)
RAMSIZE = cp.get(vmsection, ramsizekey)
KIOSKMODE = int(cp.get(vmsection, kioskmodekey))
DRIVERANK = int(cp.get(vmsection, driverankkey))
SWAPUUID  = cp.get(vmsection, swapuuid)
SWAPFILE  = cp.get(vmsection, swapfile)

WIDTH = cp.get(vmsection, widthkey)
HEIGHT = cp.get(vmsection, heightkey)
