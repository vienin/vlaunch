# -*- coding: utf-8 -*-

import logging
import conf
import os
import sys
import os.path as path
import tempfile
import urllib
from shutil import rmtree
import socket
import subprocess

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

if conf.LIVECD:
    if not os.path.exists(conf.BOOTISO):
        import gui_pyqt
        if gui_pyqt.download_file("http://kickstart.agorabox.org/private/UFO.iso",
                               filename=conf.BOOTISO):
            sys.exit(0)

if sys.platform == "win32":
    from windowsbackend import *
    backend = WindowsBackend()
elif sys.platform == "darwin":
    logging.debug("Adding " + conf.BIN + " to sys.path")
    sys.path.append(conf.BIN)
    logging.debug("Importing SIP")
    import sip
    logging.debug("Importing xpcom")
    import xpcom
    logging.debug("Importing xpcom.vboxxpcom")
    import xpcom.vboxxpcom
    logging.debug("Import PyQt4")
    import PyQt4.QtGui
    from macbackend import *
    backend = MacBackend()
elif sys.platform == "linux2":
    from linuxbackend import *
    backend = LinuxBackend()
else:
    raise "Unsupported platform"

print "SCRIPT_DIR", conf.SCRIPT_DIR
print "SCRIPT_PATH", conf.SCRIPT_PATH
print "APP_PATH", conf.APP_PATH

if not conf.NOUPDATE and conf.SCRIPT_DIR.startswith(tempfile.gettempdir()) and \
   not "--no-update" in sys.argv:
    try:
        socket.setdefaulttimeout(5)
        latest_version = urllib.urlopen("http://downloads.agorabox.org/launcher/latest").read()
        logging.debug("Using launcher version : " + str(conf.VERSION))
        logging.debug("Available version on the Net : " + str(latest_version))
        latest_version = map(int, latest_version.split('.'))
        local_version = map(int, conf.VERSION.split('.'))
        if local_version < latest_version :
            logging.debug("Updating to new version. Asking to user...")
            input = backend.dialog_question(title=u"Mise à jour",
                msg=u"Une version plus récente du lanceur U.F.O est disponible, voulez-vous la télécharger (Environ 100 Mo de téléchargement) ?",
                button1=u"Oui", button2=u"Non")
            logging.debug("Got : " + str(input))
            if input == "Oui":
                # Run Updater and close launcher
                backend.prepare_update()
                cmd = [ backend.shadow_updater_executable,
                        ".".join(map(str, latest_version)),
                        backend.ufo_dir, backend.shadow_updater_path ]
                logging.debug("Launching updater : " + " ".join(cmd))
                # For some reason, does not work on Mac OS
                # I get Operation not permitted
                # os.execv(backend.shadow_updater_executable,
                #          [backend.shadow_updater_executable, backend.ufo_dir])
                subprocess.Popen(cmd, shell=False)
                logging.debug("Exiting for good")
                sys.exit(0)
            else:
                backend.do_not_update = True
    except SystemExit:
        sys.exit(0)
    except:
        # raise
        import traceback
        info = sys.exc_info()
        logging.debug("Unexpected error: " + str(info[1]))
        logging.debug("".join(traceback.format_tb(info[2])))
        logging.debug("Exception while updating")

try:
    if sys.platform == "linux2":
        rmtree(path.join(conf.SCRIPT_DIR,"bin", "settings"))
        print "Temporary settings file destroyed"
except: pass

if __name__ == "__main__":
    backend.run()

