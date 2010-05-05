#!/usr/bin/python

# UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
#
# Copyright (c) 2008-2010 Agorabox, Inc.
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


import os
import sys
import utils

if os.environ.has_key("PROCESSOR_ARCHITEW6432"):
    bindir = "bin64"
    arch = "AMD64"
else:
    bindir = "bin"
    arch = "x86"

exe = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), bindir, "ufo." + arch + ".exe")
utils.call([exe] + sys.argv[1:], cwd=os.path.dirname(exe))
