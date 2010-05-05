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


from distutils.core import setup
import py2exe
from py2exe.build_exe import py2exe as BuildExe
import os, sys
import glob

#manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
#<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"> 
#   <assemblyIdentity version="1.0.0.0" processorArchitecture="X86" name="ufo" type="win32"/>
#      <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
#      <security>
#         <requestedPrivileges>
#            <requestedExecutionLevel level="requireAdministrator"/> 
#         </requestedPrivileges>
#      </security>
#   </trustInfo>
#</assembly>
#"""

manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.VC90.CRT" version="9.0.21022.8" processorArchitecture="amd64" publicKeyToken="1fc8b3b9a1e18e3b"></assemblyIdentity>
    </dependentAssembly>
  </dependency>
</assembly>
"""

sys.path.append("..")
sys.path.append("../src")

setup(#zipfile = "bin\\library.zip",
      options = {'py2exe': { 'bundle_files': 3,
                              'includes': ['sip', 'win32com.server.util', 'pythoncom'],
                              'excludes' : [ "Tkconstants", "Tkinter", "tcl" ],
                              #               "PyQt4.QtCore", "PyQt4.QtGui", "PyQt4.QtNetwork", "PyQt4" ],
                              # 'dll_excludes': [ "PyQt4\\QtCore.pyd", "PyQt4\\QtGui.pyd",
                              #                   "PyQt4\\QtNetwork.pyd",
                              #                   "QtCore4.dll", "QtGui4.dll", "QtNetwork4.dll" ],
                              "typelibs": [('{46137EEC-703B-4FE5-AFD4-7C9BBBBA0259}', 0, 1, 3)],
                }},

      windows = [{'script': "../src/launcher.py",
                   "icon_resources" : [(1, "../graphics/UFO.ico")],
                   "other_resources": [(24, 1, manifest)],
                  }],
)
