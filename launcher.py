# -*- coding: utf-8 -*-

import logging
import conf
import sys
import os.path as path
import tempfile

format = "%(asctime)s %(levelname)s %(message)s"
try:
    logging.basicConfig(format=format, level=logging.DEBUG, filename=path.join(conf.SCRIPT_DIR, conf.LOG))
    logging.debug("Logging to " + path.join(conf.SCRIPT_DIR, conf.LOG))
except:
    try:
        temp = path.join(tempfile.gettempdir(), "launcher.log")
        logging.basicConfig(format=format, level=logging.DEBUG,
                            filename=temp)
        logging.debug("Logging to " + temp)
    except:
        print "Could not redirect log to file"

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

backend.check_process()

import urllib
from shutil import rmtree
import socket
import subprocess

print "SCRIPT_DIR", conf.SCRIPT_DIR
print "SCRIPT_PATH", conf.SCRIPT_PATH
print "APP_PATH", conf.APP_PATH

if not conf.SCRIPT_DIR.startswith(tempfile.gettempdir()):
    try:
        socket.setdefaulttimeout(5)
        latest_version = urllib.urlopen("http://downloads.agorabox.org/launcher/latest").read()
        logging.debug("Using launcher version : " + str(conf.VERSION))
        logging.debug("Available version on the Net : " + str(latest_version))
        latest_version = map(int, latest_version.split('.'))
        local_version = map(int, conf.VERSION.split('.'))
        if local_version < latest_version :
            logging.debug("Updating to new version. Asking to the user...")
            input = backend.dialog_question(title=u"Mise à jour",
                msg=u"Une version plus récente du lanceur U.F.O est disponible, voulez-vous la télécharger (Environ 100 Mo de téléchargement) ?",
                button1=u"Oui", button2=u"Non")
            logging.debug("Got : " + str(input))
            if input == "Oui":
                # Run Updater and close launcher
                backend.prepare_update()
                logging.debug("Launching updater : " + backend.shadow_updater_executable + " " + ".".join(latest_version) + " " + backend.ufo_dir + " " + backend.shadow_updater_path )
                # For some reason, does not work on Mac OS
                # I get Operation not permitted
                # os.execv(backend.shadow_updater_executable,
                #          [backend.shadow_updater_executable, backend.ufo_dir])
                subprocess.Popen([ backend.shadow_updater_executable, ".".join(latest_version), backend.ufo_dir, backend.shadow_updater_path ], shell=False)
                logging.debug("Exiting for good")
                sys.exit(0)
    except SystemExit:
        sys.exit(0)
    except:
        logging.debug("Exception while updating")

try:
    if sys.platform == "linux2":
        rmtree(path.join(conf.SCRIPT_DIR,"bin", "settings"))
        print "Temporary settings file destroyed"
except: pass

backend.run()

