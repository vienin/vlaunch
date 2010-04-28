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

manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"> 
   <assemblyIdentity version="1.0.0.0" processorArchitecture="X86" name="ufo" type="win32"/>
      <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
      <security>
         <requestedPrivileges>
            <requestedExecutionLevel level="requireAdministrator"/> 
         </requestedPrivileges>
      </security>
   </trustInfo>
</assembly>
"""

sys.path.append("..")
sys.path.append("../src")

setup(zipfile = "bin\\library.zip",
      options = {'py2exe': { 'bundle_files': 2,
                              'includes': ['sip', 'win32com.server.util', 'pythoncom'],
                              'excludes' : [ "Tkconstants", "Tkinter", "tcl" ],
                }},

      console = [{'script': "../src/ufo-dd.py",
                   "icon_resources" : [(1, "../graphics/UFO.ico")],
                   "other_resources": [(24, 1, manifest)],
                  }],
)
