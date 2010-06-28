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
from ConfigParser import ConfigParser
import gui
import tempfile
from conf import conf
import socket
import utils

def get_latest_version():
    socket.setdefaulttimeout(5)
    latest_version = urllib.urlopen(conf.UPDATEURL + "/latest").read()
    latest_version = map(int, latest_version.split('.'))
    string_version = ".".join(map(str, latest_version))
    latest_size = int(urllib.urlopen(conf.UPDATEURL + "/launcher-" + string_version + ".tar.bz2").headers.get("content-length"))
    latest_real_size = int(urllib.urlopen(conf.UPDATEURL + "/size-" + string_version).read())
    
    logging.debug("Available version on the Net : " + str(string_version) + " (" + str(latest_size / 1024) + " k)")
    return latest_version, latest_size, latest_real_size
 
def check_update(backend):
    logging.debug("Using launcher version : " + str(conf.VERSION))
    try:
        logging.debug("Checking updates")
        local_version = map(int, conf.VERSION.split('.'))
        latest_version, latest_size, latest_real_size = get_latest_version()
        if local_version < latest_version :
            logging.debug("Updating to new version. Asking to user...")
            input = gui.dialog_question(title=_("Update available"),
                msg=_("A more recent version of the U.F.O launcher is available,"
                      "do you want to install it ? (%s Mo to download) ?") % (latest_size / (1024*1024),),
                button1=_("Yes"), button2=_("No"))
            logging.debug("Got : " + str(input))
            if input == _("Yes"):

                # Check available space
                removed_space = 0
                for file in open(os.path.join(conf.DATA_DIR, "launcher.filelist")).readlines():
                    try:
                        size = os.stat(path.join(path.dirname(conf.DATA_DIR), file.strip())).st_size
                    except:
                        continue
                    removed_space = removed_space + size

                while True:
                    available_space = backend.get_free_space(conf.DATA_DIR)
                    if available_space + removed_space < latest_real_size:
                        input = gui.dialog_error_report(_("Insufficient free space"),
                                                        _("The available space on your UFO key is insufficient for the update.<br><br>"
                                                          "Please remove more than <b>%s Mo</b> in the <b>\"Public\"</b> directory and retry.") %
                                                          ((latest_real_size - (available_space + removed_space)) / (1024*1024),),
                                                        _("Retry"),
                                                        error=False)
                        if not input:
                            return
                    else:
                        break

                # Run Updater and close launcher
                backend.checking_pyqt()
                executable = backend.prepare_update()

                cmd = [ executable,
                        "--update",
                        path.dirname(conf.DATA_DIR), ".".join(map(str, latest_version)),
                        "--relaunch", conf.SCRIPT_PATH ]
                logging.debug("Launching updater : " + " ".join(cmd))
                logging.shutdown()
                os.execv(executable, cmd)
                sys.exit(0)

    except SystemExit:
        sys.exit(0)

    except:
        import traceback
        info = sys.exc_info()
        logging.debug("Unexpected error: " + str(info[1]))
        logging.debug("".join(traceback.format_tb(info[2])))
        logging.debug("Exception while updating")

def remove_deprecated_files(tar, old, dest):
    if os.path.exists(old):
        files = list(set(map(str.strip, open(old).readlines())) - set(tar.getnames()))
        for f in [ os.path.join(dest, f) for f in files ]:
            if os.path.islink(f) or os.path.isfile(f):
                try: os.unlink(f)
                except: logging.debug("Could not remove file " + f)
        for d in [ os.path.join(dest, d) for d in files ]:
            if os.path.isdir(d):
                try: os.rmdir(d)
                except: logging.debug("Could not remove directory " + d)

def self_update(ufo_dir, relaunch):
    try:
        latest_version, x, x = get_latest_version()
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

        url = conf.UPDATEURL + "/launcher-" + latest_version + ".tar.bz2"

        filename = tempfile.mkstemp()[1]
        logging.debug("Downloading " + url + " to " + filename)
        retcode  = gui.download_file(url, filename, title=_("Downloading update"),
                                     msg=_("Please wait while the update is being downloaded"),
                                     success_msg=_("Your key will now be updated.<br>"
                                                   "This operation can take a few minutes<br><br>\n"
                                                   "<b>The USB key absolutely must not be unplugged during this process.</b>"))
        if retcode:
            raise Exception("Download was canceled")

        logging.debug("Extracting update " + filename + " to " + ufo_dir)

        import tarfile
        tar = tarfile.open(filename)
        filelist = path.join(ufo_dir, ".data", "launcher.filelist")

        gui.wait_command(cmd=[remove_deprecated_files, tar, filelist, os.path.normcase(ufo_dir)],
                         title=_("Removing old files"),
                         msg=_("Please wait while the old files are being removed"))

        if sys.platform == "darwin":
            retcode = gui.wait_command(cmd=[ "tar", "-C", ufo_dir, "-xjf", filename ],
                                       title=_("Installing update"),
                                       msg=_("Please wait while the update is being installed.<br><br>"
                                             "<b>The USB key absolutely must not be unplugged.</b>"))

            mount = utils.grep(utils.call([ "mount" ], output=True)[1], ufo_dir)
            if mount:
                dev = mount.split()[0]
                utils.call([ "diskutil", "unmount", dev ])
                utils.call([ "diskutil", "mount", dev ])

        else:
            retcode = gui.extract_tar(tgz=tar,
                                      dest=os.path.normcase(ufo_dir),
                                      title=_("Installing update"),
                                      msg=_("Please wait while the update is being installed.<br><br>"
                                        "<b>The USB key absolutely must not be unplugged.</b>"))

        tar.close()
        if not retcode:
            raise Exception("Installation has failed")

        logging.debug("Updating settings.conf")
        cp = ConfigParser()
        cp.read([ conf.conf_file ])
        cp.set("launcher", "VERSION", latest_version)
        cp.write(open(conf.conf_file, "w"))

        gui.dialog_info(title=_("Information"),
                        msg=_("Your UFO launcher is up to date (v" + latest_version + ") !"))

        try:
            os.remove(filename)
        except:
            pass

    except:
        gui.dialog_info(title=_("Error"),
                        msg=_("An error occurred. You key could not be updated."))

        import traceback
        info = sys.exc_info()
        logging.debug("Unexpected error: " + str(info[1]))
        logging.debug("".join(traceback.format_tb(info[2])))
        logging.debug("Exception while updating")
        logging.debug("Restarting UFO launcher : " + relaunch)

    logging.shutdown()
    os.execv(relaunch, [ relaunch, "--respawn" ] )
