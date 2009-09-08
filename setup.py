from distutils.core import setup
import py2exe
from py2exe.build_exe import py2exe as BuildExe
import os, sys
import glob

setup(zipfile = None,
      options = {'py2exe': { 'bundle_files': 1,
                              'includes': ['sip'],
                              #'excludes' : [ "Tkconstants", "Tkinter", "tcl",
                              #               "PyQt4.QtCore", "PyQt4.QtGui", "PyQt4.QtNetwork", "PyQt4" ],
                              # 'dll_excludes': [ "PyQt4\\QtCore.pyd", "PyQt4\\QtGui.pyd",
                              #                   "PyQt4\\QtNetwork.pyd",
                              #                   "QtCore4.dll", "QtGui4.dll", "QtNetwork4.dll" ],
                              "typelibs": [('{46137EEC-703B-4FE5-AFD4-7C9BBBBA0259}', 0, 1, 3)],
                }},

      windows = [{'script': "ufo.py", "icon_resources" : [(1, "UFO.ico")]}],
)
