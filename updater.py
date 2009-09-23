#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
try: logging.basicConfig(filename="/tmp/updater.log", level=logging.DEBUG)
except: 
    logging.basicConfig(level=logging.DEBUG)

import os
logging.debug("Current directory: " + os.getcwd())

import urllib
import sys
import tarfile
#from utils import SplashScreen
import subprocess
from ConfigParser import ConfigParser
import gui

if sys.platform == "win32":
    from windowsbackend import *
    backend = WindowsBackend()
elif sys.platform == "darwin":
    from macbackend import *
    backend = MacBackend()
elif sys.platform == "linux2":
    from linuxbackend import *
    backend = LinuxBackend()
else:
    raise "Unsupported platform"

if len(sys.argv) < 4:
    print "Wrong number of arguments"
    sys.exit(1)

# try:
latest_version = sys.argv[1]
ufo_dir = sys.argv[2]
current_dir = sys.argv[3]
logging.debug("args : " + latest_version + " " + ufo_dir + " " + current_dir)

if sys.platform == "win32":
    launcher = os.path.join(ufo_dir, "Windows", "ufo.exe")
    splash_dir = current_dir
elif sys.platform == "darwin":
    launcher = os.path.join(ufo_dir, "Mac-Intel", "UFO.app", "Contents", "MacOS", "UFO")
    splash_dir = os.path.join(current_dir, "Contents", "Resources", ".VirtualBox")
elif sys.platform == "linux2":
    launcher = os.path.join(ufo_dir, "Linux", "ufo")
    splash_dir = os.path.join(current_dir, "..", ".VirtualBox")
else:
    raise "Unsupported platform"

settings = (os.path.join(ufo_dir, "Windows", "settings", "settings.conf"),
            os.path.join(ufo_dir, "Mac-Intel", "UFO.app", "Contents", "Resources", "settings", "settings.conf"),
            os.path.join(ufo_dir, "Linux", "settings", "settings.conf"))

backend.dialog_info(title=u"Attention",
                    msg=u"Lancement de la mise à jour. " \
                        u"NE RETIREZ PAS LA CLE. NE TOUCHEZ A " \
                        u"AUCUN FICHIER SUR LA CLE. La mise à jour peut durer plusieurs minutes")
# splash_down = SplashScreen(backend.tk, image=os.path.join(splash_dir, "updater-download.png"), timeout=0)
splash_down = SplashScreen(image=os.path.join(splash_dir, "updater-download.png"))
url = "http://downloads.agorabox.org/launcher/launcher-" + latest_version + ".tar.bz2"

logging.debug("Downloading " + url)
gui.dialog_info(title="tamere", msg=url)
filename = urllib.urlretrieve(url)[0]
logging.debug("Downloaded as " + filename)
splash_down.destroy()

# splash_install = SplashScreen(backend.tk, image=os.path.join(splash_dir, "updater-install.png"),timeout=0)
splash_install = SplashScreen(image=os.path.join(splash_dir, "updater-install.png"))
logging.debug("Extracting update to " + ufo_dir)
tgz = tarfile.open(filename)
tgz.extractall(os.path.normcase(ufo_dir))
tgz.close()

logging.debug("Updating version in settings.conf files")
for setting in settings:
    # Updating version
    logging.debug("Updating " + setting)
    cp = ConfigParser()
    cp.read([setting])
    cp.set("launcher", "VERSION", latest_version)
    cp.write(open(setting, "w"))

splash_install.destroy()
backend.dialog_info(title=u"Information",
                    msg=u"Votre clé est à jour.")

# except:
#    logging.debug("Exception")
#    import traceback
#    info = sys.exc_info()
#    logging.debug("Error while updating: " + str(info[1]))
#    logging.debug("".join(traceback.format_tb(info[2])))
#                                            
#    backend.dialog_info(title=u"Erreur",
#                        msg=u"La mise à jour n'a pas été réalisée correctement.")

logging.debug("Restarting UFO launcher : " + launcher)
subprocess.Popen([ launcher ])

