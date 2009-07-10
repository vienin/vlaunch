#!/usr/bin/python

import urllib
import sys
import tarfile
import os
from utils import SplashScreen
import subprocess
from ConfigParser import ConfigParser
#import time

print "Updater loaded"

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

print "backend loaded"

try:
    svn_version = sys.argv[1]
    ufo_dir = sys.argv[2]
    current_dir = sys.argv[3]
    print "args : "+svn_version+" "+ufo_dir+" "+current_dir

    if sys.platform == "win32":
        launcher = os.path.join(ufo_dir, "Windows", "ufo.exe")
        settings = os.path.join(ufo_dir, "Windows", "settings", "settings.conf")
        splash_dir = current_dir
    elif sys.platform == "darwin":
        launcher = os.path.join(ufo_dir, "Mac-Intel", "UFO.app", "Contents", "MacOS", "UFO")
        settings = os.path.join(ufo_dir, "Mac-Intel", "UFO.app", "Contents", "Resources", "settings", "settings.conf")
        splash_dir = os.path.join(current_dir, ".VirtualBox")
    elif sys.platform == "linux2":
        launcher = os.path.join(ufo_dir, "Linux", "ufo")
        settings = os.path.join(ufo_dir, "Linux", "settings", "settings.conf")
        splash_dir = os.path.join(current_dir, "..", ".VirtualBox")
    else:
        raise "Unsupported platform"

    print "path saved"

    backend.dialog_info(title=u"Attention",msg=u"Lancement de la mise a jour. NE RETIREZ PAS LA CLE. NE TOUCHEZ A AUCUN FICHIER SUR LA CLE. La mise a jour peut durer plusieurs minutes")
    splash_down = SplashScreen(backend.tk, image=os.path.join(splash_dir, "ufo-update-download.gif"),timeout=0)
    # ufo_dir = os.path.normpath(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), "../.."))
    url = "http://downloads.agorabox.org/launcher/launcher-" + svn_version + ".tar.bz2"

    print "Downloading " + url
    filename = urllib.urlretrieve(url)[0]
    #time.sleep(5)
    print "Downloaded as " + filename
    splash_down.destroy()

    splash_install = SplashScreen(backend.tk, image=os.path.join(splash_dir, "ufo-update-install.gif"),timeout=0)
    print "Extracting update"
    tgz = tarfile.open(filename)
    tgz.extractall(os.path.normcase(ufo_dir + "/"))
    tgz.close()

    # Updating version
    cp = ConfigParser()
    print "Reading", settings
    cp.read([settings])
    cp.set("launcher", "VERSION", svn_version)
    cp.write(open(settings, "w"))
    #time.sleep(5)
    splash_install.destroy()

    backend.dialog_info(title=u"Information",msg=u"Votre cle est a jour.")
except :
    backend.dialog_info(title=u"Erreur",msg=u"La mise na jour n'a pas ete realise correctement.")


print "Restarting UFO launcher : " + launcher
subprocess.Popen([ launcher ])
