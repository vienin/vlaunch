#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import os
format = "%(asctime)s %(levelname)s Updater %(message)s"
try: logging.basicConfig(format=format, filename=os.path.join("logs", "ufo-updater.log"), level=logging.DEBUG)
except: logging.basicConfig(level=logging.DEBUG)
logging.debug("Current directory : " + os.getcwd())

import urllib
import sys
import tarfile
import subprocess
from ConfigParser import ConfigParser
import gui
import tempfile

logging.debug("Using " + gui.backend + " backend")

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

    gui.dialog_info(title=u"Attention",
                        msg=u"Lancement de la mise à jour. " \
                            u"NE RETIREZ PAS LA CLE. NE TOUCHEZ A " \
                            u"AUCUN FICHIER SUR LA CLE. La mise à jour peut durer plusieurs minutes")

    splash_down = gui.SplashScreen(image=os.path.join(splash_dir, "updater-download.png"))
    url = "http://downloads.agorabox.org/launcher/launcher-" + latest_version + ".tar.bz2"

    filename = tempfile.mkstemp()[1]
    retcode  = gui.download_file(url, filename, title="Téléchargement de la mise à jour", msg="Merci de bien vouloir patientier", autostart=True)
    if not splash_down == None:
        splash_down.destroy()

    splash_install = gui.SplashScreen(image=os.path.join(splash_dir, "updater-install.png"))
    logging.debug("Extracting update " + filename + " to " + ufo_dir)
    tgz = tarfile.open(filename)
    tgz.extractall(os.path.normcase(ufo_dir))
    tgz.close()
    # os.remove(filename)

    logging.debug("Updating version in settings.conf files")
    for setting in settings:
        # Updating version
        logging.debug("Updating " + setting)
        cp = ConfigParser()
        cp.read([setting])
        cp.set("launcher", "VERSION", latest_version)
        cp.write(open(setting, "w"))

    if not splash_install == None:
        splash_install.destroy()

    gui.dialog_info(title=u"Information",
                        msg=u"Votre clé est à jour.")

except:
    gui.dialog_info(title=u"Erreur",
                        msg=u"La mise à jour n'a pas été réalisée correctement.")

    import traceback
    info = sys.exc_info()
    logging.debug("Unexpected error: " + str(info[1]))
    logging.debug("".join(traceback.format_tb(info[2])))
    logging.debug("Exception while updating")
    logging.debug("Restarting UFO launcher : " + launcher)

os.execv(launcher, [ launcher ])
