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

from conf import conf
import logging
import datetime
import os
import sys
import os.path as path
import tempfile
import urllib
import traceback

format = "%(asctime)s [%(levelname)s] %(message)s"
if conf.options.update or conf.options.dd:
    if conf.options.update:
        log = "ufo-updater.log"
    elif conf.options.dd:
        log = "ufo-creator.log"
    conf.LOGFILE = path.join(tempfile.gettempdir(), log)

else:
    log_dir = os.path.dirname(conf.LOG)
    if not os.path.exists(log_dir):
        try: os.makedirs(log_dir)
        except: pass
    conf.LOGFILE = path.join(log_dir, os.path.basename(conf.LOG))

try:
    from utils import RoolOverLogger
    log_path    = path.join(conf.SCRIPT_DIR, conf.LOGFILE)
    root_logger = RoolOverLogger(log_path, 10)

    logging.debug = root_logger.safe_debug
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

logging.debug(datetime.datetime.now())

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
                                msg=_("A %s Live CD is required to continue.") % (conf.PRODUCTNAME, ) + "\n" + \
                                    _("Press 'Download' to start downloading the %s Live image.") % (conf.PRODUCTNAME, ) + "\n\n" + \
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


if __name__ == "__main__":
    try:
        if conf.options.update and conf.options.relaunch:
            updater.self_update(conf.options.update, conf.options.relaunch)
        elif not conf.NOUPDATE and not conf.options.respawn:
            updater.check_update(backend)

        if conf.options.dd:
            from ufo_dd import DDWindow
            creator = DDWindow(backend, conf.options.relaunch)
            creator.prepare()
            creator.show()
            creator.exec_()
            sys.exit(1)

        if conf.options.settings:
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

        logging.debug("Checking for running UFO processes")
        backend.check_process()

        backend.run()

        if conf.GUESTDEBUG:
            if gui.dialog_error_report(_("Debug mode"),
                                       _("%s was run in debug mode.\n"
                                         "You can help fixing your problem by submitting the debug reports") % (conf.PRODUCTNAME,),
                                       _("Send debug reports"),
                                       error=False):
                report_files = glob.glob(conf.LOGFILE + "_*")
                report_files.insert(0, conf.LOGFILE)
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
        import errno
        trace = traceback.format_exc()
        logging.debug(trace)
        if isinstance(e, OSError) and e.errno == errno.ECHILD:
            msg = _("%s has encountered a minor error. Restarting the application may fix the problem.") % (conf.PRODUCTNAME,)
            error = False
        else:
            msg = _("%s has encountered a fatal error and will now be closed.") % (conf.PRODUCTNAME,)
            error = True
        if gui.dialog_error_report(_("Error"),
                                   msg + "\n\n" + \
                                   _("You can help fixing this problem by submitting an error report"),
                                   _("Send a report"),
                                   trace,
                                   error=error):
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
