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

import conf
import logging
import datetime
import os
import sys
import os.path as path
import tempfile
import urllib
import traceback
import glob

format = "%(asctime)s %(levelname)s %(message)s"
if conf.options.update:
    conf.LOGFILE = path.join(tempfile.gettempdir(), "ufo-updater.log")
else:
    log_dir = os.path.dirname(conf.LOG)
    if not os.path.exists(log_dir):
        try: os.makedirs(log_dir)
        except: pass
    conf.LOGFILE = path.join(log_dir, str(datetime.datetime.now()).replace(' ', '_').replace(':', '-') + "_" + os.path.basename(conf.LOG))
try:
    logging.basicConfig(format=format, level=logging.DEBUG, filename=path.join(conf.SCRIPT_DIR, conf.LOGFILE))
    log_path = path.join(conf.SCRIPT_DIR, conf.LOGFILE)
    print "Logging to " + log_path
except:
    try:
        temp = path.join(tempfile.gettempdir(), path.basename(conf.LOG))
        logging.basicConfig(format=format, level=logging.DEBUG,
                            filename=temp)
        log_path = temp
        print "Logging to " + log_path
    except:
        print "Could not redirect log to file"

import gui
import updater

if conf.LIVECD:
    download = True
    conf.BOOTISO = path.realpath(unicode(conf.BOOTISO))
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
                                msg=_("A U.F.O Live CD is required to continue.") + "\n" + \
                                    _("Press 'Download' to start downloading the U.F.O Live image.") + "\n\n" + \
                                    _("This operation can take up to a few hours, depending on your connection speed."))
        if res:
            sys.exit(1)

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

if conf.USER:
    logging.debug("Customer: " + conf.USER)
else:
    logging.debug("Customer: None")
    
if conf.options.update and conf.options.relaunch:
    updater.self_update(conf.options.update, conf.options.relaunch)
elif not conf.NOUPDATE and not conf.options.respawn:
    updater.check_update(backend)

logging.debug("Checking for running UFO processes")
backend.check_process()

if __name__ == "__main__":
    try:
        if '--settings' in sys.argv:
            settings = gui.Settings()
            settings.show()
            settings.exec_()
            sys.exit(1)

        elif conf.LANGUAGE == conf.AUTO_STRING:
            conf.LANGUAGE = conf.DEFAULTLANGUAGE
            settings = gui.Settings(tabs=_("Appearance"), fields=["language"],
                                    show_default_button=False, no_reboot=True)
            settings.show()
            if not settings.exec_():
                sys.exit(0)
            
        backend.run()

        if conf.GUESTDEBUG and backend.send_debug_rep:
            if gui.dialog_error_report(_("Debug mode"),
                                       _("UFO was run in debug mode.\n"
                                         "You can help fixing your problem by submitting the debug reports"),
                                       _("Send debug reports"),
                                       error=False):
                report_files = glob.glob(conf.LOGFILE + "*")
                reports = ""
                for file in report_files:
                    reports += "\n" + ("_" * len(file)) + "\n" + file + "\n\n"
                    reports += open(file, 'r').read()
                params = urllib.urlencode({'report': reports})
                try:
                    urllib.urlopen(conf.REPORTURL, params)
                except:
                    pass
            
    except Exception, e:
        trace = traceback.format_exc()
        logging.debug(trace)
        if gui.dialog_error_report(_("Error"),
                                   _("UFO a encountered a fatal error and will now be closed.") + "\n" + \
                                   _("You can help fixing this problem by submitting an error report"),
                                   _("Send a report"),
                                   trace):
            params = urllib.urlencode({'report': open(log_path, 'r').read()})
        try:
            urllib.urlopen(conf.REPORTURL, params)
        except:
            pass

        try:
            shutil.copy(log_path, os.path.join(os.path.dirname(log_path), "last_log.log"))
        except: pass

    # quit application
    gui.app.quit()
