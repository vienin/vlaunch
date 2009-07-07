#!/usr/bin/python

import urllib
import sys
import tarfile
import os
import subprocess
from ConfigParser import ConfigParser

# ufo_dir = os.path.normpath(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), "../.."))
ufo_dir = sys.argv[1]
svn_version = urllib.urlopen("http://downloads.agorabox.org/launcher/latest").read()
url = "http://downloads.agorabox.org/launcher/launcher-" + svn_version + ".tar.bz2"

print "Downloading " + url
filename = urllib.urlretrieve(url)[0]
print "Downloaded as " + filename

print "Extracting update"
tgz = tarfile.open(filename)
tgz.extractall(os.path.normcase(ufo_dir + "/"))
tgz.close()

if sys.platform == "win32":
    launcher = os.path.normcase(ufo_dir + "\\Windows\\ufo.exe")
    settings = os.path.join(ufo_dir, "Windows", "settings", "settings.conf")
elif sys.platform == "darwin":
    launcher = os.path.normcase(ufo_dir + "/Mac-Intel/UFO.app/Contents/MacOS/UFO")
    settings = os.path.join(ufo_dir, "Mac-Intel", "UFO.app", "Contents", "Resources", "settings", "settings.conf")
elif sys.platform == "linux2":
    launcher = os.path.normcase(ufo_dir + "/Linux/ufo")
    settings = os.path.join(ufo_dir, "Linux", "settings", "settings.conf")
else:
    raise "Unsupported platform"

# Updating version
cp = ConfigParser()
print "Reading", settings
cp.read([settings])
cp.set("launcher", "VERSION", svn_version)
cp.write(open(settings, "w"))

print "Restarting UFO launcher : " + launcher
subprocess.Popen([ launcher ])
