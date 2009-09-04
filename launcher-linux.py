#!/usr/bin/python

import sys
from os.path import realpath, join, dirname

bindir = join(realpath(dirname(sys.argv[0])), "bin")
sys.path.insert(0, bindir)         
execfile(join(bindir, "launcher.py"))
