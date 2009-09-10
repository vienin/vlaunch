# -*- coding: utf-8 -*-

import logging
import datetime
import conf
import os
import sys
import os.path as path
import tempfile
import urllib
from shutil import rmtree
import socket
import subprocess
import traceback

format = "%(asctime)s %(levelname)s %(message)s"
log_file_name = os.path.join(os.path.dirname(conf.LOG), str(datetime.datetime.now()).replace(' ', '_').replace(':', '-') + "_" + os.path.basename(conf.LOG))
try:
    logging.basicConfig(format=format, level=logging.DEBUG, filename=path.join(conf.SCRIPT_DIR, log_file_name))
    log_path = path.join(conf.SCRIPT_DIR, log_file_name)
    logging.debug("Logging to " + log_path)
    print "Logging to " + log_path
except:
    try:
        temp = path.join(tempfile.gettempdir(), log_file_name)
        logging.basicConfig(format=format, level=logging.DEBUG,
                            filename=temp)
        log_path = temp
        logging.debug("Logging to " + log_path)
        print "Logging to " + log_path
    except:
        print "Could not redirect log to file"

if conf.LIVECD:
    iso_url = "http://kickstart.agorabox.org/private/VBoxRT.dll" # UFO.iso"
    download = True
    if path.exists(conf.BOOTISO):
        length = int(urllib.urlopen(iso_url).headers['content-length'])
        if length == os.stat(conf.BOOTISO).st_size:
            logging.debug("Found complete ISO file. Do not download it.")
            download = False
        else:
            logging.debug("Found incomplete file '%s' of size %d (%d expected)" % (conf.BOOTISO, os.stat(conf.BOOTISO).st_size, length))
        
    if not "--respawn" in sys.argv and download:
        sys.path.append(conf.BIN)
        import gui_pyqt
        res = gui_pyqt.download_file(iso_url, # UFO.iso",
                                     filename=conf.BOOTISO)
        if not res:
            sys.exit(0)

if sys.platform == "win32":
    from windowsbackend import *
    backend = WindowsBackend()
elif sys.platform == "darwin":
    logging.debug("Adding " + conf.BIN + " to sys.path")
    sys.path.append(conf.BIN)
    from macbackend import *
    backend = MacBackend()
elif sys.platform == "linux2":
    from linuxbackend import LinuxBackend
    backend = LinuxBackend()
else:
    raise "Unsupported platform"

backend.check_process()

if not conf.NOUPDATE and not "--respawn" in sys.argv:
    try:
        socket.setdefaulttimeout(5)
        latest_version = urllib.urlopen("http://downloads.agorabox.org/launcher/latest").read()
        logging.debug("Using launcher version : " + str(conf.VERSION))
        logging.debug("Available version on the Net : " + str(latest_version))
        latest_version = map(int, latest_version.split('.'))
        local_version = map(int, conf.VERSION.split('.'))
        if local_version < latest_version :
            logging.debug("Updating to new version. Asking to user...")
            input = gui.dialog_question(title=u"Mise à jour",
                msg=u"Une version plus récente du lanceur U.F.O est disponible, " + \
                    u"voulez-vous la télécharger (Environ 100 Mo de téléchargement) ?",
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
    try:
        backend.run()
    except Exception, e:
        import gui
        trace = traceback.format_exc()
        logging.debug(trace)
        if gui.dialog_error_report(u"Erreur", u"UFO à rencontré une erreur fatale et doit fermer.\n" + \
                                   u"Vous pouvez aider à la correction du problème en soumettant le rapport d'erreur.", trace):
            import urllib
            params = urllib.urlencode({'report': open(log_path, 'r').read()})
            try:
                urllib.urlopen(conf.REPORTURL, params)
            except:
                pass

