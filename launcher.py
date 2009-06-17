# -*- coding: utf-8 -*-

import sys
import logging
import tempfile
import os.path as path
import conf

format = "%(asctime)s %(levelname)s %(message)s"
try:
    logging.basicConfig(format=format, level=logging.DEBUG, filename=path.join(conf.SCRIPT_DIR, conf.LOG))
except:
    try:
        logging.basicConfig(format=format, level=logging.DEBUG,
                            filename=path.join(tempfile.gettempdir(), "launcher.log"))
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

print "SCRIPT_DIR", conf.SCRIPT_DIR
print "SCRIPT_PATH", conf.SCRIPT_PATH
print "APP_PATH", conf.APP_PATH

backend.run()
