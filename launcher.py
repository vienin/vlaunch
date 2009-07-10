﻿# -*- coding: utf-8 -*-

import sys
import logging
import tempfile
import os.path as path
import conf
import urllib
from shutil import rmtree
import socket
import subprocess

format = "%(asctime)s %(levelname)s %(message)s"
try:
    logging.basicConfig(format=format, level=logging.DEBUG, filename=path.join(conf.SCRIPT_DIR, conf.LOG))
except:
    try:
        logging.basicConfig(format=format, level=logging.DEBUG,
                            filename=path.join(tempfile.gettempdir(), "launcher.log"))
    except:
        print "Could not redirect log to file"

print "SCRIPT_DIR", conf.SCRIPT_DIR
print "SCRIPT_PATH", conf.SCRIPT_PATH
print "APP_PATH", conf.APP_PATH

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

exit = False
try:
    socket.setdefaulttimeout(5)
    svn_version = int(urllib.urlopen("http://downloads.agorabox.org/launcher/latest").read())
    logging.debug("Using launcher version : " + str(conf.VERSION))
    logging.debug("Available version on the Net : " + str(svn_version))
    if conf.VERSION < svn_version :
        logging.debug("Updating to new version. Asking to the user...")
        input = backend.dialog_question(title=u"Mise à jour",
            msg=u"Une version plus récente du lanceur U.F.O est disponible, voulez vous la télécharger (Environ 100 Mo de téléchargement) ?",
            button1=u"Oui", button2=u"Non")
        logging.debug("Got : " + str(input))
        if input == "Oui":
            # Run Updater and close launcher
            backend.prepare_update()

            logging.debug("Launching updater " + backend.shadow_updater_executable + " " + str(svn_version) + " " + backend.ufo_dir + " " + backend.shadow_updater_path )
            # For some reason, does not work on Mac OS
            # I get Operation not permitted
            # os.execv(backend.shadow_updater_executable,
            #          [backend.shadow_updater_executable, backend.ufo_dir])
            subprocess.Popen([ backend.shadow_updater_executable, str(svn_version), backend.ufo_dir, backend.shadow_updater_path ], shell=False)
            logging.debug("Exiting for good")
            exit = True
except:
    logging.debug("Exception while updating")
    print "exception while updating"

if exit : sys.exit(0)

try:
    if sys.platform == "linux2":
        shutil.rmtree(path.join(backend.shadow_updater_path, "settings"))
        print "Temporary settings file destroyed"
except: pass

backend.run()
