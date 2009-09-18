#!/usr/bin/python

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
