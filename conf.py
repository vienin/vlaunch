import os, os.path as path, sys
from ConfigParser import ConfigParser

SCRIPT_PATH = path.realpath(sys.argv[0])
SCRIPT_DIR  = path.dirname(path.realpath(sys.argv[0]))
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

cp = ConfigParser(defaults = { logkey : "launcher.log",
                               startvmkey : "1",
                               vmkey : "UFO",
                               oskey : "Fedora",
                               vmdkkey : "ufo_key.vmdk",
                               partskey : "all",
                               bootfloppykey : "",
                               bootisokey : "",
                               swapfile : "ufo_swap.vdi",
                               swapsize : "512",
                               overlayfile : "ufo_overlay.vdi",
                               nettypekey : "2",
                               hostnetkey : "",
                               macaddrkey : "",
                               ramsizekey : "auto",
                               minramkey : "256",
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
                               reporturlkey : "http://reporting.agorabox.org/services/reporting",
                               homekey : "",
                               useservicekey : "0",
                               createsrvskey : "0",
                               startsrvskey : "0",
                               uninstalldriverskey : "0",
                               versionkey : "0",
                               licensekey : "0",
                               noupdatekey : "0",
                               livecdkey : "0",
                               bootdiskuuidkey : "",
                               bootdiskkey : "",
                               isourlkey : "http://downloads.agorabox.org/launcher/latest",
                               updateurlkey : "http://downloads.agorabox.org/launcher/"
                             })
                             
try:
    files = [path.join(SCRIPT_DIR, "settings.conf"),
             path.join(SCRIPT_DIR, "settings", "settings.conf"),
             path.join(SCRIPT_DIR, "..", "settings", "settings.conf")]
    if os.environ.has_key("_MEIPASS2"):
        files.append(path.join(os.environ["_MEIPASS2"], "settings.conf"))
    settings = cp.read(files)
    conf_file = settings[0]
except:
    print "Could not read settings.conf"
    raise

print "Using configuration file:", conf_file

HOME = cp.get(globalsection, homekey)
BIN  = cp.get(globalsection, binkey)
VMDK = cp.get(globalsection, vmdkkey)

USESERVICE = int(cp.get(launchersection, useservicekey))
CREATESRVS = int(cp.get(launchersection, createsrvskey))
STARTSRVS = int(cp.get(launchersection, startsrvskey))
STARTVM = int(cp.get(launchersection, startvmkey))
NEEDDEV = int(cp.get(launchersection, needdevkey))
DEBUG = int(cp.get(launchersection, debugkey))
REPORTURL = cp.get(launchersection, reporturlkey)
LOG = cp.get(launchersection, logkey)
VERSION = cp.get(launchersection, versionkey)
LICENSE = int(cp.get(launchersection, licensekey))
CONFIGUREVM = int(cp.get(launchersection, configurevmkey))
UNINSTALLDRIVERS = int(cp.get(launchersection, uninstalldriverskey))
NOUPDATE = int(cp.get(launchersection, noupdatekey))
LIVECD = int(cp.get(launchersection, livecdkey))
ISOURL = cp.get(launchersection, isourlkey)
UPDATEURL = cp.get(launchersection, updateurlkey)

DEV = cp.get(rawdisksection, devkey)
PARTS = cp.get(rawdisksection, partskey)
ROOTUUID = cp.get(rawdisksection, rootuuidkey)
VOLUME = cp.get(rawdisksection, volumekey)
MODEL = cp.get(rawdisksection, modelkey)

VM = cp.get(vmsection, vmkey)
OS = cp.get(vmsection, oskey)
BOOTFLOPPY = cp.get(vmsection, bootfloppykey)
BOOTISO = cp.get(vmsection, bootisokey)
NETTYPE = int(cp.get(vmsection, nettypekey))
HOSTNET = cp.get(vmsection, hostnetkey)
MACADDR = cp.get(vmsection, macaddrkey)
RAMSIZE = cp.get(vmsection, ramsizekey)
MINRAM = int(cp.get(vmsection, minramkey))
KIOSKMODE = int(cp.get(vmsection, kioskmodekey))
DRIVERANK = int(cp.get(vmsection, driverankkey))
SWAPFILE  = cp.get(vmsection, swapfile)
SWAPSIZE  = int(cp.get(vmsection, swapsize))
OVERLAYFILE  = cp.get(vmsection, overlayfile)
BOOTDISK = cp.get(vmsection, bootdiskkey)
BOOTDISKUUID = cp.get(vmsection, bootdiskuuidkey)

WIDTH = cp.get(vmsection, widthkey)
HEIGHT = cp.get(vmsection, heightkey)
