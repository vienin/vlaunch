#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import sys
import tarfile
import os
import logging
from utils import SplashScreen
import subprocess
from ConfigParser import ConfigParser

try: logging.basicConfig(filename="updater.log", level=logging.DEBUG)
except: logging.basicConfig(level=logging.DEBUG)

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

try:
    svn_version = sys.argv[1]
    ufo_dir = sys.argv[2]
    current_dir = sys.argv[3]
    logging.debug("args : " + svn_version + " " + ufo_dir + " " + current_dir)

    if sys.platform == "win32":
        launcher = os.path.join(ufo_dir, "Windows", "ufo.exe")
        splash_dir = current_dir
    elif sys.platform == "darwin":
        launcher = os.path.join(ufo_dir, "Mac-Intel", "UFO.app", "Contents", "MacOS", "UFO")
        splash_dir = os.path.join(current_dir, ".VirtualBox")
    elif sys.platform == "linux2":
        launcher = os.path.join(ufo_dir, "Linux", "ufo")
        splash_dir = os.path.join(current_dir, "..", ".VirtualBox")
    else:
        raise "Unsupported platform"

    settings = (os.path.join(ufo_dir, "Windows", "settings", "settings.conf"),
                os.path.join(ufo_dir, "Mac-Intel", "UFO.app", "Contents", "Resources", "settings", "settings.conf"),
                os.path.join(ufo_dir, "Linux", "settings", "settings.conf"))

    backend.dialog_info(title=u"Attention",
                        msg=u"Lancement de la mise a jour. " \
                            u"NE RETIREZ PAS LA CLE. NE TOUCHEZ A " \
                            u"AUCUN FICHIER SUR LA CLE. La mise a jour peut durer plusieurs minutes")
    splash_down = SplashScreen(backend.tk, image=os.path.join(splash_dir, "updater-download.gif"), timeout=0)
    url = "http://downloads.agorabox.org/launcher/launcher-" + svn_version + ".tar.bz2"

    logging.debug("Downloading " + url)
    filename = urllib.urlretrieve(url)[0]
    logging.debug("Downloaded as " + filename)
    splash_down.destroy()

    splash_install = SplashScreen(backend.tk, image=os.path.join(splash_dir, "updater-install.gif"),timeout=0)
    logging.debug("Extracting update")
    tgz = tarfile.open(filename)
    tgz.extractall(os.path.normcase(ufo_dir + "/"))
    tgz.close()

    for setting in settings:
        # Updating version
        cp = ConfigParser()
        cp.read([setting])
        cp.set("launcher", "VERSION", svn_version)
        cp.write(open(setting, "w"))

    splash_install.destroy()
    backend.dialog_info(title=u"Information",
                        msg=u"Votre clé est à jour.")

except:
    raise
    backend.dialog_info(title=u"Erreur",
                        msg=u"La mise n'a jour n'a pas été realisée correctement.")

logging.debug("Restarting UFO launcher : " + launcher)
subprocess.Popen([ launcher ])

