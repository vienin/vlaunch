#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import os
import urllib
import sys
import tarfile
import subprocess
from ConfigParser import ConfigParser
import gui
import tempfile
import conf
import socket
import utils

def get_latest_version():
    socket.setdefaulttimeout(5)
    latest_version = urllib.urlopen(conf.UPDATEURL + "/latest").read()
    logging.debug("Using launcher version : " + str(conf.VERSION))
    logging.debug("Available version on the Net : " + str(latest_version))
    latest_version = map(int, latest_version.split('.'))
    return latest_version
 
def check_update(backend):
    try:
        logging.debug("Checking updates")
        local_version = map(int, conf.VERSION.split('.'))
        latest_version = get_latest_version()
        if local_version < latest_version :
            logging.debug("Updating to new version. Asking to user...")
            input = gui.dialog_question(title=u"Mise à jour",
                msg=u"Une version plus récente du lanceur U.F.O est disponible, " + \
                    u"voulez-vous la télécharger (Environ 100 Mo de téléchargement) ?",
                button1=u"Oui", button2=u"Non")
            logging.debug("Got : " + str(input))
            if input == "Oui":
                # Run Updater and close launcher
                executable = backend.prepare_update()
 
                cmd = [ executable,
                        "--update",
                        conf.UFO_DIR, ".".join(map(str, latest_version)) ]
                logging.debug("Launching updater : " + " ".join(cmd))
                # For some reason, execv does not work on Mac OS
                # I get Operation not permitted
                if sys.platform == "darwin":
                    subprocess.Popen(cmd, shell=False, close_fds=True)
                    logging.debug("Exiting for good")
                    logging.shutdown()
                else:
                    os.execv(executable, cmd)
                sys.exit(0)
            else:
                backend.do_not_update = True
    except SystemExit:
        sys.exit(0)
    except:
        import traceback
        info = sys.exc_info()
        logging.debug("Unexpected error: " + str(info[1]))
        logging.debug("".join(traceback.format_tb(info[2])))
        logging.debug("Exception while updating")

def self_update():
  try:
    latest_version = ".".join(map(str, get_latest_version()))
 
    gui.dialog_info(title=u"Attention",
                    msg=u"Lancement de la mise à jour. \n" \
                        u"NE RETIREZ PAS LA CLE. NE TOUCHEZ A \n" \
                        u"AUCUN FICHIER SUR LA CLE. \n\nLa mise à jour peut durer plusieurs minutes")
 
    splash_down = gui.SplashScreen(image=os.path.join(conf.IMG_DIR, "updater-download.png"))
    url = conf.UPDATEURL + "/launcher-" + latest_version + ".tar.bz2"
 
    filename = tempfile.mkstemp()[1]
    logging.debug("Downloading " + url + " to " + filename)
    retcode  = gui.download_file(url, filename, title=u"Téléchargement de la mise à jour",
                                 msg=u"Merci de bien vouloir patientier", autostart=True)
     
    if not splash_down == None:
        splash_down.destroy()
 
    splash_install = gui.SplashScreen(image=os.path.join(conf.IMG_DIR, "updater-install.png"))
    logging.debug("Extracting update " + filename + " to " + conf.UFO_DIR)
    
    if sys.platform == "darwin":
        utils.call([ "tar", "-C", conf.UFO_DIR, "-xjf", filename ])
        mount = utils.grep(utils.call([ "mount" ], output=True)[1], conf.UFO_DIR)
        if mount:
            dev = mount.split()[0]
            utils.call([ "diskutil", "unmount", dev ])
            utils.call([ "diskutil", "mount", dev ])

    else:
        tgz = tarfile.open(filename)
        tgz.extractall(os.path.normcase(conf.UFO_DIR))
        tgz.close()
 
    logging.debug("Updating settings.conf")
    cp = ConfigParser()
    cp.read([ conf.conf_file ])
    cp.set("launcher", "VERSION", latest_version)
    cp.write(open(conf.conf_file, "w"))
 
    if not splash_install == None:
        splash_install.destroy()

    gui.dialog_info(title=u"Information",
                    msg=u"Votre clé est à jour.")
 
    try:
        os.remove(filename)
    except:
        pass
     
  except:
    gui.dialog_info(title=u"Erreur",
                    msg=u"La mise à jour n'a pas été réalisée correctement.")

    import traceback
    info = sys.exc_info()
    logging.debug("Unexpected error: " + str(info[1]))
    logging.debug("".join(traceback.format_tb(info[2])))
    logging.debug("Exception while updating")
    logging.debug("Restarting UFO launcher : " + conf.EXEC_PATH)

  logging.shutdown()
  os.execv(conf.EXEC_PATH, [ conf.EXEC_PATH ])

