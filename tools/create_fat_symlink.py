#!/usr/bin/python

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


import os
import sys
import md5

filename = sys.argv[2]
target = sys.argv[1] # os.readlink(filename)
length = "%04d" % len(target)
buf = "XSym\n%s\n%s\n%s\n%s" % (length, md5.md5(target).hexdigest(), target, " " * (1023 - int(length)))
if os.path.exists(filename):
    os.unlink(filename)
open(filename, "w").write(buf)
