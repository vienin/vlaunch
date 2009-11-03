# -*- coding: utf-8 -*-

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
import threading
import subprocess
import time
import urllib
import tempfile
import signal
import utils

zenity = subprocess.Popen(["which", "zenity"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].strip()

if not os.path.lexists(zenity):
    raise Exception("Could not find 'zenity'")


class NoneUFOGui():
    def __init__(self, argv):
        pass
    
    def initialize_tray_icon(self):
        pass
        
    def start_usb_check_timer(self, time, function):
        pass
        
    def stop_usb_check_timer(self):
        pass
    
    def start_callbacks_timer(self, time, function):
        pass
        
    def stop_callbacks_timer(self):
        pass

    def update_progress(self, progress, value):
        pass

    def show_balloon_message(self, title, msg, timeout=0):
        pass
        
    def show_balloon_progress(self, title, msg):
        pass
        
    def hide_balloon(self):
        pass
        
    def set_tooltip(self, tip):
        pass
        
    def fullscreen_window(self, winid):
        pass
        
    def minimize_window(self, winid):
        pass
    
    def process_gui_events(self):
        pass


class CommandLauncher(threading.Thread):
    def __init__(self, cmd, titre="", msg=""):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.toBeStop = False
        self.exe = None
        self.titre = titre
        self.msg = msg
        self.retcode = 0

    def run(self):
        returncode = 0
        fi = tempfile.mkstemp()
        os.write(fi[0],"\n")
        self.exe = subprocess.Popen([ zenity, "--progress", "--pulsate", u"--title=%s"%(self.titre,), u"--text=%s"%(self.msg,)], stdin=fi[0])
        t = subprocess.Popen(self.cmd)
        while t.poll() == None and self.exe.poll() == None:
            time.sleep(1)

        if t.poll() == None:
            try:
                os.kill(t.pid, signal.SIGKILL)
            except OSError, e:
                pass
        if self.exe.poll() == None:
            returncode = 1
            try:
                os.kill(self.exe.pid, signal.SIGKILL) 
            except OSError, e:
                pass

        os.remove(fi[1])
        self.retcode = returncode
        sys.exit(returncode)

class Downloader(threading.Thread):
    def __init__(self, file, dest, title, msg, autostart): 
        threading.Thread.__init__(self)
        self.file = file
        self.dest = dest
        self.toBeStop = False
        self.title = title
        self.msg = msg
        # Zenity process
        self.exe = None
        # return code of this thread (to help parent thread deciding what to do)
        self.retcode = 0

    def run(self):
        try:
            # Dirty trick, to launch zenity progress bar, if there's no \n on 
            # stdin, progress bar doesn't start her animation.
            sys.stdout.flush()
            self.fi = tempfile.mkstemp()
            os.write(self.fi[0],"\n")
            self.exe = subprocess.Popen([ zenity, "--progress", "--pulsate",
                                          "--title", self.title,
                                          "--text", self.msg ], stdin=self.fi[0])
            urllib.urlretrieve(self.file, self.dest, reporthook=self.progress)
        except Exception, e:
            print e
            self.stop(1)
        else: 
            self.stop()

    def progress(self, count, blockSize, totalSize):
        if self.exe.poll() == None and self.toBeStop == False:
            pass
        else:
            self.stop(2)

    def stop(self, ret=0):
        self.retcode = ret
        if self.exe.poll() == None:
            os.kill(self.exe.pid, signal.SIGKILL)
        if os.path.exists(self.fi[1]):
            os.remove(self.fi[1]) 
        sys.exit(self.retcode)

def download_file(url, filename, title, msg, autostart=False):
    downloader = Downloader(url, filename, title, msg, autostart=autostart)
    downloader.start()
    downloader.join()
    return downloader.retcode

def wait_command(cmd, title=u"Veuillez patienter", msg=u"Une opération est en cours"):
    launch = CommandLauncher(cmd, title, msg)
    launch.start()
    launch.join()
    return launch.retcode

def dialog_info(title, msg, error = False):
    subprocess.call([ zenity, "--info", "--title=" + title, "--text=" + msg ])

def dialog_question(title, msg, button1=None , button2=None):
    return (button1, button2)[ subprocess.call([ zenity, "--question", "--title=" + title, "--text=" + msg ])]

def dialog_password(root=None):
    return subprocess.Popen([ zenity, "--entry", "--title", u'Autorisation nécessaire',
                              "--text", 'Veuillez entrer votre mot de passe:',
                              "--entry-text", '', "--hide-text" ],
                            stdout=subprocess.PIPE).communicate()[0]

def SplashScreen(*args, **kw):
    print "Can't display a splash screen with zenity"
    return None

def dialog_error_report(title, msg, action=None, details=None):
    dialog_info(title, msg, error = True)
    return True
    
def dialog_choices(title, msg, column, choices):
    ret, output =  utils.call([ zenity, "--title", title, "--text", msg,
                                "--list", "--column", column ] + choices, output=True)
    output = output.strip()
    return choices.index(output)

app = NoneUFOGui(sys.argv)
