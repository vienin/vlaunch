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


from setuptools import setup
import sys

NAME = 'ufo'
VERSION = '1.0'

plist = dict(
    CFBundleIconFile=NAME
)

sys.path.append("..")
sys.path.append("../src")
sys.path.append("../sdk/bindings/xpcom/python/")

APP = [ "../src/UFO.py" ]
DATA_FILES = [ ]
OPTIONS = {'argv_emulation' : False,
           'iconfile' : '../graphics/ufo.icns',
           'includes': ['xpcom', 'xpcom.vboxxpcom', 'sip'],}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
