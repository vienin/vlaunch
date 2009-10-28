# -*- coding: utf-8 -*-

import logging
import datetime
import conf
import os
import sys
import os.path as path
import tempfile
import urllib
import shutil
from shutil import rmtree
import socket
import subprocess
import traceback
import gui
import updater

format = "%(asctime)s %(levelname)s %(message)s"
if conf.options.update:
    log_file_name = path.join(tempfile.gettempdir(), "ufo-updater.log")
else:
    log_dir = os.path.dirname(conf.LOG)
    if not os.path.exists(log_dir):
        try: os.makedirs(log_dir)
        except: pass
    log_file_name = path.join(log_dir, str(datetime.datetime.now()).replace(' ', '_').replace(':', '-') + "_" + os.path.basename(conf.LOG))
try:
    logging.basicConfig(format=format, level=logging.DEBUG, filename=path.join(conf.SCRIPT_DIR, log_file_name))
    log_path = path.join(conf.SCRIPT_DIR, log_file_name)
    print "Logging to " + log_path
except:
    try:
        temp = path.join(tempfile.gettempdir(), log_file_name)
        #logging.basicConfig(format=format, level=logging.DEBUG,
        #                    filename=temp)
        log_path = temp
        print "Logging to " + log_path
    except:
        print "Could not redirect log to file"

if conf.LIVECD:
    download = True
    if path.exists(conf.BOOTISO):
        length = int(urllib.urlopen(conf.ISOURL).headers['content-length'])
        if length == os.stat(conf.BOOTISO).st_size or os.environ.has_key("NODOWNLOAD"):
            logging.debug("Found complete ISO file. Do not download it.")
            download = False
        else:
            logging.debug("Found incomplete file '%s' of size %d (%d expected)" % (conf.BOOTISO, os.stat(conf.BOOTISO).st_size, length))
        
    if not conf.options.respawn and download:
        sys.path.append(conf.BIN)
        res = gui.download_file(conf.ISOURL,
                                filename=conf.BOOTISO,
                                msg=u"Un live U.F.O est nécessaire pour continuer. \n"   
                                    u"Cliquez sur 'Télécharger' pour commencer le téléchargement.\n\n"
                                    u"Cette opération peut prendre de quelques minutes à plusieurs heures\n" 
                                    u"suivant la vitesse de votre connexion.")
        if not res:
            sys.exit(0)

if sys.platform == "win32":
    from windowsbackend import *
    backend = WindowsBackend()
    logging.debug("Platfrom: win32")
elif sys.platform == "darwin":
    logging.debug("Adding " + conf.BIN + " to sys.path")
    sys.path.append(conf.BIN)
    from macbackend import *
    backend = MacBackend()
    logging.debug("Platfrom: darwin")
elif sys.platform == "linux2":
    from linuxbackend import *
    backend = create_linux_distro_backend()
    logging.debug("Platfrom: linux2, distro: %s, version: %s, codename: %s" % (backend.dist, backend.version, backend.codename))
else:
    raise "Unsupported platform"

if conf.options.update and conf.options.relaunch:
    updater.self_update(conf.options.update, conf.options.relaunch)
elif not conf.NOUPDATE and not conf.options.respawn:
    updater.check_update(backend)

logging.debug("Checking for running UFO processes")
backend.check_process()

if __name__ == "__main__":
    try:
        backend.run()
    except Exception, e:
        import gui
        trace = traceback.format_exc()
        logging.debug(trace)
        if gui.dialog_error_report(u"Erreur", u"UFO à rencontré une erreur fatale et doit fermer.\n" + \
                                   u"Vous pouvez aider à la correction du problème en soumettant le rapport d'erreur.",
                                   u"Envoyer le rapport d'erreur", trace):
            import urllib
            params = urllib.urlencode({'report': open(log_path, 'r').read()})
            try:
                urllib.urlopen(conf.REPORTURL, params)
            except:
                pass

    try:
        shutil.copy(log_path, os.path.join(os.path.dirname(log_path), "last_log.log"))
    except: pass

