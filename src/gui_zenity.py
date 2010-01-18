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
import time
import urllib
if sys.platform == "win32": import subprocess
else: import ufo_subprocess as subprocess
import tempfile
import signal
import utils

zenity = utils.call(["which", "zenity"], output=True, log=False)[1].strip()

if not os.path.lexists(zenity):
    raise Exception("Could not find 'zenity'")


class NoneUFOGui():
    def __init__(self, argv):
        pass

    def create_splash_screen(self):
        pass

    def destroy_splash_screen(self):
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
       
    def authentication(self, msg):
        pass

    def show_balloon_message(self, title, msg, timeout=0):
        pass
        
    def show_balloon_progress(self, title, msg, credentials=None, keyring=False):
        pass

    def hide_balloon(self):
        pass

    def set_tooltip(self, tip):
        pass

    def fullscreen_window(self, winid, toggle):
        pass

    def minimize_window(self, winid):
         pass

    def normalize_window(self, winid):
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
        def print_echo():
            print
        self.exe = utils.call([ self.cmd,
                                [ zenity, "--progress", "--auto-close", "--pulsate", u"--title=%s"%(self.titre,), u"--text=%s"%(self.msg,)]
                              ], preexec_fn=print_echo)
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

def wait_command(cmd, title=_("Please wait"), msg=_("Operation in progress"),
                 success_msg=_("Operation successfully completed"), error_msg=("An error has occurred")):
    launch = CommandLauncher(cmd, title, msg)
    launch.start()
    launch.join()
    return launch.retcode

def dialog_info(title, msg, error = False):
    utils.call([ zenity, "--info", "--title=" + title, "--text=" + msg ])

def dialog_question(title, msg, button1=None , button2=None):
    return (button1, button2)[ utils.call([ zenity, "--question", "--title=" + title, "--text=" + msg ])]

def dialog_password(root=None):
    return utils.call([ zenity, "--entry", "--title", _('Password required'),
                              "--text", _("Please enter your password:"),
                              "--entry-text", '', "--hide-text" ]).communicate()[0]

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
