import os, os.path as path, sys
from ConfigParser import ConfigParser
from optparse import OptionParser

SCRIPT_PATH = path.realpath(sys.argv[0])
SCRIPT_NAME = path.basename(sys.argv[0])
SCRIPT_DIR  = path.dirname(path.realpath(sys.argv[0]))

print "SCRIPT_PATH", SCRIPT_PATH
print "SCRIPT_NAME", SCRIPT_NAME
print "SCRIPT_DIR", SCRIPT_DIR

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

cp = ConfigParser(defaults = { logkey : "logs/launcher.log",
                               imgdirkey : "images",
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
                               heightkey : "full",
                               widthkey : "full",
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
                               updateurlkey : "http://downloads.agorabox.org/launcher/"
                             })
                             
try:
    files = ["settings.conf", # Used on Mac OS LiveCD
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
DATA_DIR = options.update
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
        DATA_DIR = path.join(path.dirname(SCRIPT_PATH), "..", "Resources")
        # no BIN as the livecd always provides a settings.conf
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

# Is BIN overridden in settings.conf ?
bin  = cp.get(globalsection, binkey)
if bin: BIN = path.join(DATA_DIR, bin)

HOME = path.join(DATA_DIR, cp.get(globalsection, homekey))
VMDK = cp.get(globalsection, vmdkkey)

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

