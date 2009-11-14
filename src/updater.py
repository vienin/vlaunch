#!/usr/bin/python
# -*- coding: utf-8 -*-

# UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
#
# Copyright (c) 2008-2009 Agorabox, Inc.
#
# This is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA. 


import logging
import os, os.path as path
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
    latest_version = map(int, latest_version.split('.'))
    string_version = ".".join(map(str, latest_version))
    latest_size = int(urllib.urlopen(conf.UPDATEURL + "/launcher-" + string_version + ".tar.bz2").headers.get("content-length"))
    
    logging.debug("Using launcher version : " + str(conf.VERSION))
    logging.debug("Available version on the Net : " + str(string_version) + " (" + str(latest_size / 1000) + " k)")
    return latest_version, latest_size
 
def check_update(backend):
    try:
        logging.debug("Checking updates")
        local_version = map(int, conf.VERSION.split('.'))
        latest_version, latest_size = get_latest_version()
        if local_version < latest_version :
            logging.debug("Updating to new version. Asking to user...")
            input = gui.dialog_question(title=u"Mise à jour",
                msg=u"Une version plus récente du lanceur U.F.O est disponible, " + \
                    u"voulez-vous l'installer (" + str( latest_size / 1000000) + u" Mo de téléchargement) ?",
                button1=u"Oui", button2=u"Non")
            logging.debug("Got : " + str(input))
            if input == "Oui":
                # Run Updater and close launcher
                executable = backend.prepare_update()
 
                cmd = [ executable,
                        "--update",
                        path.dirname(conf.DATA_DIR), ".".join(map(str, latest_version)),
                        "--relaunch", conf.SCRIPT_PATH ]
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

def self_update(ufo_dir, relaunch):
  try:
    latest_version, latest_size = get_latest_version()
    latest_version = ".".join(map(str, latest_version))

    try:
        if sys.platform == "darwin":
            mount = utils.grep(utils.call([ "mount" ], output=True)[1], ufo_dir)
            if mount:
                dev = mount.split()[0]
                utils.call([ "diskutil", "unmount", dev ])
                utils.call([ "diskutil", "mount", dev ])
    except:
        pass

    gui.dialog_info(title=u"Attention",
                    msg=u"Lancement de la mise à jour.\n" \
                        u"NE RETIREZ PAS LA CLE.\n" \
                        u"NE TOUCHEZ A AUCUN FICHIER SUR LA CLE. \n\nLa mise à jour peut durer plusieurs minutes")
 
    splash_down = gui.SplashScreen(image=os.path.join(conf.IMGDIR, "updater-download.png"))
    url = conf.UPDATEURL + "/launcher-" + latest_version + ".tar.bz2"
 
    filename = tempfile.mkstemp()[1]
    logging.debug("Downloading " + url + " to " + filename)
    retcode  = gui.download_file(url, filename, title=u"Téléchargement de la mise à jour",
                                 msg=u"Merci de bien vouloir patienter", autostart=True, autoclose=True)
    if retcode:
        raise "Download was canceled"
     
    if not splash_down == None:
        splash_down.destroy()
 
    splash_install = gui.SplashScreen(image=os.path.join(conf.IMGDIR, "updater-install.png"))
    logging.debug("Extracting update " + filename + " to " + ufo_dir)

    tgz = tarfile.open(filename)
    filelist = path.join(ufo_dir, ".data", "launcher.filelist")
    if path.exists(filelist):
       files = list(set(map(str.strip, open(filelist).readlines())) - set(tgz.getnames()))
       for f in [ path.join(ufo_dir, f) for f in files if path]:
           if path.islink(f) or path.isfile(f):
               try: os.unlink(f)
               except: logging.debug("Could not remove file " + f)
       for d in [ path.join(ufo_dir, d) for d in files if path ]:
           if path.isdir(d):
               try: os.rmdir(d)
               except: logging.debug("Could not remove directory " + d)
    
    if sys.platform == "darwin":
        utils.call([ "tar", "-C", ufo_dir, "-xjf", filename ])
        mount = utils.grep(utils.call([ "mount" ], output=True)[1], ufo_dir)
        if mount:
            dev = mount.split()[0]
            utils.call([ "diskutil", "unmount", dev ])
            utils.call([ "diskutil", "mount", dev ])

    else:
        tgz.extractall(os.path.normcase(ufo_dir))
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
    logging.debug("Restarting UFO launcher : " + relaunch)

  logging.shutdown()
  os.execv(relaunch, [ relaunch ])

