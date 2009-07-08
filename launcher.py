# -*- coding: utf-8 -*-

import sys
import logging
import tempfile
import os.path as path
import conf
import urllib
import os
import shutil
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

if not conf.SCRIPT_DIR.startswith("/tmp/"):
    try:
        socket.setdefaulttimeout(5)
        svn_version = int(urllib.urlopen("http://downloads.agorabox.org/launcher/latest").read())
        logging.debug("Using launcher version : " + str(conf.VERSION))
        logging.debug("Available version on the Net : " + str(svn_version))
        if conf.VERSION < svn_version :
            logging.debug("Updating to new version. Asking to the user...")
            input = backend.dialog_question(title=u"Mise à jour",
                                    msg=u"Une version plus récente du lanceur U.F.O est disponible, voulez vous la télécharger (Environ 100 Mo de téléchargement) ?",
                                    button1=u"Oui",
                                    button2=u"Non")
            logging.debug("Got : " + str(input))
            if input == "Oui":
                # Run Updater and close launcher
                logging.debug("Copying " + backend.updater_path + " to " + backend.shadow_updater_path)
                if path.isfile(backend.updater_path):
                    shutil.copyfile(backend.updater_path, backend.shadow_updater_path)
                else:
                    shutil.copytree(backend.updater_path, backend.shadow_updater_path)
                logging.debug("Launching updater " + backend.shadow_updater_executable + " " + backend.ufo_dir)
                # For some reason, does not work on Mac OS
                # I get Operation not permitted
                # os.execv(backend.shadow_updater_executable,
                #          [backend.shadow_updater_executable, backend.ufo_dir])
                subprocess.Popen([ backend.shadow_updater_executable, backend.ufo_dir ])
                sys.exit(0)
    except SystemExit:
        sys.exit(0)
    except:
        logging.debug("Exception while updating")

backend.run()
