# -*- coding: utf-8 -*-

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


from PyQt4 import QtGui, QtCore
import threading, sys, os
from urllib import urlretrieve, urlopen
from ConfigParser import ConfigParser
from utils import SmartDict
from ufovboxapi import *
import time, utils
from conf import conf
import logging
import glob
import math


class QtUFOGui(QtGui.QApplication):
        
    def __init__(self):
        QtGui.QApplication.__init__(self, sys.argv)

        self.vbox      = None
        self.animation = None
        self.tray      = None
        self.splash    = None

        self.usb_check_timer  = QtCore.QTimer(self)
        self.net_adapt_timer  = QtCore.QTimer(self)
        self.callbacks_timer  = QtCore.QTimer(self)
        self.termination_timer  = QtCore.QTimer(self)

        self.console_window   = None
        self.settings_window  = None
        self.creator_window    = None
        self.antivirus_window = None
        self.console_winid    = 0
        self.backend          = None

        self.menu = QtGui.QMenu()
        action_about = QtGui.QAction(QtGui.QIcon(os.path.join(conf.IMGDIR, "about.png")), 
                                     QtCore.QString(_("About")), self);
        action_about.setStatusTip(_("Get informations about UFO"))
        action_settings = QtGui.QAction(QtGui.QIcon(os.path.join(conf.IMGDIR, "settings.png")), 
                                        QtCore.QString(_("Settings...")), self);
        action_settings.setStatusTip(_("Configure the UFO launcher"))
        action_creator = QtGui.QAction(QtGui.QIcon(os.path.join(conf.IMGDIR, "creator.png")),
                                        QtCore.QString(_("Creator...")), self);
        action_creator.setStatusTip(_("Create your UFO key"))
        action_quit = QtGui.QAction(QtGui.QIcon(os.path.join(conf.IMGDIR, "exit.png")),
                                        QtCore.QString(_("Quit")), self);
        action_quit.setStatusTip(_("Quit"))
        action_force_quit = QtGui.QAction(QtGui.QIcon(os.path.join(conf.IMGDIR, "force.png")),
                                        QtCore.QString(_("Force to quit")), self);
        action_force_quit.setStatusTip(_("Force to quit"))
        action_antivirus = QtGui.QAction(QtGui.QIcon(os.path.join(conf.IMGDIR, "antivirus.png")),
                                         QtCore.QString(_("Antivirus...")), self);
        action_antivirus.setStatusTip(_("Antivirus"))

        self.menu.addAction(action_settings)

        try:
            import clamavgui
            self.menu.addAction(action_antivirus)
            self.connect(action_antivirus, QtCore.SIGNAL("triggered()"), self.antivirus)
        except:
            logging.debug("Can't load clamav module")

        try:
            import ufo_dd
            self.menu.addAction(action_creator)
            self.connect(action_creator, QtCore.SIGNAL("triggered()"), self.creator)
        except:
            logging.debug("Can't load ufo-dd module")

        self.menu.addAction(action_about)
        self.menu.addAction(action_force_quit)
        self.menu.addAction(action_quit)
        self.connect(action_about, QtCore.SIGNAL("triggered()"), self.about)
        self.connect(action_settings, QtCore.SIGNAL("triggered()"), self.settings)
        self.connect(action_quit, QtCore.SIGNAL("triggered()"), self.quit)
        self.connect(action_force_quit, QtCore.SIGNAL("triggered()"), self.force_to_quit)
        
        self.setWindowIcon(QtGui.QIcon(os.path.join(conf.IMGDIR, "UFO.png")))

    def event(self, event):
        if isinstance(event, SetTrayIconEvent):
            self.tray = TrayIcon()

            if sys.platform != "darwin":
                self.tray.setContextMenu(self.menu)

        elif isinstance(event, JobFinishedEvent):
            event.callback(event.error)

        elif isinstance(event, CreateSplashEvent):
            self._create_splash_screen()

        elif isinstance(event, DestroySplashEvent):
            self._destroy_splash_screen()

        elif isinstance(event, CommandEvent):
            event.callback(event.error)

        elif isinstance(event, TemporaryBalloonEvent):
            if event.destroy:
                self.tray.destroy_temporary_balloon()

            elif not event.title:
                if event.msg:
                    self.tray.update_temporary_balloon_message(event.msg)
                if event.progress:
                    self.tray.update_temporary_balloon_progress(int(event.progress * 100))

            else:
                self.tray.create_temporary_balloon(event.title,
                                                   event.msg,
                                                   event.progress,
                                                   event.timeout,
                                                   event.vlayout)

        elif isinstance(event, PersistentBalloonEvent):
            if event.destroy:
                self.tray.destroy_persistent_balloon_section(event.key)

            elif event.update:
                if event.msg:
                    self.tray.update_persistent_balloon_message(event.key, event.msg)
                if event.progress:
                    self.tray.update_persistent_balloon_progress(event.key,
                                                                 int(event.progress * 100))

            else:
                self.tray.add_persistent_balloon_section(event.key,
                                                         event.msg,
                                                         event.default,
                                                         event.smartdict,
                                                         event.hlayout,
                                                         event.progress)

        elif isinstance(event, ToolTipEvent):
            self.tray.setToolTip(QtCore.QString(event.tip))

        elif isinstance(event, ConsoleWindowEvent):
            if event.winid != 0:
                if self.console_winid != event.winid:
                    self.console_winid = event.winid
                    self.console_window = QtGui.QWidget()
                    self.console_window.create(int(event.winid), False, False)
                    
                self.console_window.show()
                if event.type == ConsoleWindowEvent.defs.get('ShowMinimized'):
                    self.console_window.showMinimized()
                    
                if event.type == ConsoleWindowEvent.defs.get('ShowNormal'):
                    self.console_window.showNormal()
                
                if event.type == ConsoleWindowEvent.defs.get('ShowFullscreen'):
                    self.console_window.showMaximized()
                    
                elif event.type == ConsoleWindowEvent.defs.get('ToggleFullscreen'):
                    if self.console_window.isFullScreen() or self.console_window.isMaximized():
                        self.console_window.showNormal()
                    else:
                        self.console_window.showMaximized()
                else:
                    return False

        elif isinstance(event, UpdateDiskSpaceEvent):
            if event.disk == "root":
                self.tray.persistent_balloon.update_progress_root(event.progress)
            elif event.disk == "user":
                self.tray.persistent_balloon.update_progress_user(event.progress)
            elif event.disk == "public":
                self.tray.persistent_balloon.update_progress_public(event.progress)

        elif isinstance(event, TimerEvent):
            if event.stop:
                event.timer.stop()
                del event.timer
                event.timer = None
            else:
                if not event.timer.isActive():
                    self.connect(event.timer, QtCore.SIGNAL("timeout()"), event.function)
                    if event.single:
                        event.timer.setSingleShot(True)
                    event.timer.start(event.time * 1000)

        elif isinstance(event, UpdateProgressEvent):
            event.progress_bar.setValue(event.percent)

        else:
            return False

        return True
    
    def initialize(self, vbox, backend=None):
        self.vbox = vbox
        self.backend = backend
        self.postEvent(self, SetTrayIconEvent())

    def _create_splash_screen(self):
        images = glob.glob(os.path.join(conf.IMGDIR, "ufo-*.bmp"))
        if images:
            logging.debug("Creating splash screen with image " + images[0])
            self.splash = SplashScreen(images[0])
        else:
            logging.debug("Found no image for splash screen")

    def _destroy_splash_screen(self):
        if self.splash:
            logging.debug("Destroying splash screen")
            self.splash.destroy()
            self.splash = None

    def create_splash_screen(self):
        self.create_splash_event = CreateSplashEvent()
        self.sendEvent(self, self.create_splash_event)

    def destroy_splash_screen(self):
        self.sendEvent(self, DestroySplashEvent())

    def start_single_timer(self, timer, time, function):
        self.postEvent(self, TimerEvent(timer=timer,
                                        time=time,
                                        function=function,
                                        single=True))
                                        
    def start_check_timer(self, timer, time, function):
        self.postEvent(self, TimerEvent(timer=timer,
                                        time=time,
                                        function=function))

    def stop_check_timer(self, timer):
        self.postEvent(self, TimerEvent(timer=timer,
                                        time=None,
                                        function=None,
                                        stop=True))

    def create_temporary_balloon(self, title, msg, progress=False, timeout=0, vlayout=None):
        self.postEvent(self, TemporaryBalloonEvent(title=title,
                                                   msg=msg,
                                                   progress=progress,
                                                   timeout=timeout,
                                                   vlayout=vlayout))

    def update_temporary_balloon(self, msg=None, progress=None):
        assert msg != None or progress != None
        self.postEvent(self, TemporaryBalloonEvent(msg=msg, progress=progress))

    def add_persistent_balloon_section(self, key, msg=None, default=None, progress=False, smartdict=None, hlayout=None):
        self.postEvent(self, PersistentBalloonEvent(key=key,
                                                    msg=msg,
                                                    default=default,
                                                    progress=progress,
                                                    smartdict=smartdict,
                                                    hlayout=hlayout))

    def update_persistent_balloon_section(self, key, msg=None, progress=None):
        assert msg != None or progress != None
        self.postEvent(self, PersistentBalloonEvent(key=key,
                                                    msg=msg,
                                                    progress=progress,
                                                    update=True))

    def destroy_temporary_balloon(self):
        self.postEvent(self, TemporaryBalloonEvent(destroy=True))

    def destroy_persistent_balloon_section(self, key):
        self.postEvent(self, PersistentBalloonEvent(key=key, destroy=True))

    def destroy_persistent_balloon_sections(self):
        self.postEvent(self, PersistentBalloonEvent(key=None, destroy=True))

    def set_tooltip(self, tip):
        self.postEvent(self, ToolTipEvent(tip))

    def fullscreen_window(self, toggle, rwidth=0, rheigth=0):
        # We hope that is it our VirtualBox OSE
        try:
            if self.vbox.is_vbox_OSE():
                self.vbox.current_machine.show_fullscreen(toggle, rwidth, rheigth)
                return
        except:
            logging.debug("showConsoleFullscreen isn't defined in this OSE version")
        
        if toggle:
            type = 'ToggleFullscreen'
        else:
            type = 'ShowFullscreen'
        self.postEvent(self, 
                       ConsoleWindowEvent(self.vbox.current_machine.get_winid(),
                                          ConsoleWindowEvent.defs.get(type)))
        
    def minimize_window(self):
        # We hope that is it our VirtualBox OSE
        try:
            if self.vbox.is_vbox_OSE():
                self.vbox.current_machine.show_minimized()
                return
        except:
            logging.debug("showConsoleMinimized isn't defined in this OSE version")
        
        self.postEvent(self, 
                       ConsoleWindowEvent(self.vbox.current_machine.get_winid(),
                                          ConsoleWindowEvent.defs.get('ShowMinimized')))
        
    def normalize_window(self):
        # We hope that is it our VirtualBox OSE
        try:
            if self.vbox.is_vbox_OSE():
                self.vbox.current_machine.show_normal()
                return
        except:
            logging.debug("showConsoleNormal isn't defined in this OSE version")
                
        self.postEvent(self, 
                       ConsoleWindowEvent(self.vbox.current_machine.get_winid(),
                                          ConsoleWindowEvent.defs.get('ShowNormal')))
        
    def process_gui_events(self):
        self.processEvents()
    
    def about(self):
        QtGui.QMessageBox.about(None, 
                                QtCore.QString(_("About the UFO launcher")),
                                QtCore.QString(_("Version ") + str(conf.VERSION) + 
                                               "<br><br>Copyright (C) 2010 Agorabox<br><br>" +
                                               _("For more information, please visit") + 
                                               " http://ufo.agorabox.org"))
    
    def settings(self):
        if self.settings_window:
            self.settings_window.showNormal()
            return
            
        self.settings_window = Settings()
        self.settings_window.show()
        self.settings_window.exec_()
        del self.settings_window
        self.settings_window = None

    def creator(self):
        if self.creator_window:
            self.creator_window.showNormal()
            return

        while self.vbox.current_machine.is_running():
            input = dialog_error_report(_("Warning"),
                                        _("The UFO virtual machine is currently running.\n"
                                          "Please shutdown the UFO virtual machine before using the UFO creator"),
                                        _("Retry"),
                                        error=False)
            if not input:
                return
            time.sleep(0.3)

        from ufo_dd import DDWindow
        self.creator_window = DDWindow(self.backend)

        self.creator_window.show()
        self.creator_window.exec_()
        del self.creator_window
        self.creator_window = None

    def quit(self):
        if self.vbox.current_machine.is_running():
            if not self.vbox.current_machine.is_booted or \
               self.vbox.current_machine.power_down() == 1:
                dialog_info(title=_("Warning"),
                            msg=_("UFO virtual machine is currently starting.\n"
                                  "You can not shutdown the machine during startup."))

        else:
            sys.exit(0)

    def force_to_quit(self):
        if self.vbox.current_machine.is_running():
            no  = _("No")
            if dialog_question(title=_("Dangerous"),
                               msg=_("The UFO virtual machine is currently running.\n"
                                     "Forcing machine to shutdown is very DANGEROUS, "
                                     "the modification made during this session will "
                                     "be lost. You should use the \"Quit\" menu "
                                     "action to shutdown UFO properly.\n\n"
                                     "Do you really want to kill the UFO virtual machine ?"),
                               dangerous=True) == no:
                return

            self.vbox.current_machine.power_down(force=True)

        else:
            sys.exit(0)

    def antivirus(self):
        if self.antivirus_window:
            self.antivirus_window.showNormal()
            return
            
        from clamavgui import Antivirus
        self.antivirus_window = Antivirus(info_callback=self.update_antivirus_message, 
                                          progress_callback=self.update_antivirus_progress)
        self.add_persistent_balloon_section(key='antivirus',
                                            msg=_("Antivirus"),
                                            default=_("No virus found"),
                                            progress=True,
                                            smartdict=self.antivirus_window.virus_found,
                                            hlayout={ 'type' : VirusFoundLayout,
                                                      'args' : (self.antivirus_window.virus_attitude,)})
        self.antivirus_window.show()
        self.antivirus_window.exec_()
        del self.antivirus_window
        self.antivirus_window = None
        self.destroy_persistent_balloon_section(key='antivirus')

    def update_antivirus_message(self, msg):
        self.update_persistent_balloon_section(key='antivirus', msg="Antivirus: " + msg)

    def update_antivirus_progress(self, progress):
        self.update_persistent_balloon_section(key='antivirus', progress=float(progress))

    def update_disk_space_progress(self, disk, progress):
        self.postEvent(self, UpdateDiskSpaceEvent(disk, progress))

class NoneEvent(QtCore.QEvent):
    def __init__(self, size, total):
        super(NoneEvent, self).__init__(QtCore.QEvent.None)
        self.size = size
        self.total = total

class UpdateDiskSpaceEvent(QtCore.QEvent):
    def __init__(self, disk, progress):
        super(UpdateDiskSpaceEvent, self).__init__(QtCore.QEvent.None)
        self.disk = disk
        self.progress = progress

class SetTrayIconEvent(QtCore.QEvent):
    def __init__(self):
        super(SetTrayIconEvent, self).__init__(QtCore.QEvent.None)

class CreateSplashEvent(QtCore.QEvent):
    def __init__(self):
        super(CreateSplashEvent, self).__init__(QtCore.QEvent.None)

class DestroySplashEvent(QtCore.QEvent):
    def __init__(self):
        super(DestroySplashEvent, self).__init__(QtCore.QEvent.None)

class TemporaryBalloonEvent(QtCore.QEvent):
    def __init__(self, title=None, msg=None, progress=None, timeout=None, vlayout=None, destroy=None):
        super(TemporaryBalloonEvent, self).__init__(QtCore.QEvent.None)
        self.title    = title
        self.msg      = msg
        self.timeout  = timeout
        self.progress = progress
        self.vlayout  = vlayout
        self.destroy  = destroy

class PersistentBalloonEvent(QtCore.QEvent):
    def __init__(self, key=None, msg=None, default=None, progress=None, smartdict=None, hlayout=None, destroy=None, update=None):
        super(PersistentBalloonEvent, self).__init__(QtCore.QEvent.None)
        self.key       = key
        self.msg       = msg
        self.default   = default
        self.progress  = progress
        self.update    = update
        self.hlayout   = hlayout
        self.smartdict = smartdict
        self.destroy   = destroy

class TimerEvent(QtCore.QEvent):
    def __init__(self, timer, time, function, stop=False, single=False):
        super(TimerEvent, self).__init__(QtCore.QEvent.None)
        self.timer    = timer
        self.time     = time
        self.function = function
        self.stop     = stop
        self.single   = single

class ToolTipEvent(QtCore.QEvent):
    def __init__(self, tip):
        super(ToolTipEvent, self).__init__(QtCore.QEvent.None)
        self.tip = tip

class ConsoleWindowEvent(QtCore.QEvent):
    defs = {'ShowMinimized':0,
            'ShowNormal':1,
            'ShowFullscreen':2,
            'ToggleFullscreen':3}
    
    def __init__(self, winid, type):
        super(ConsoleWindowEvent, self).__init__(QtCore.QEvent.None)
        self.winid = winid
        self.type  = type

class JobFinishedEvent(QtCore.QEvent):
    def __init__(self, callback, error=False):
        super(JobFinishedEvent, self).__init__(QtCore.QEvent.None)
        self.callback = callback
        self.error = error

class CommandEvent(QtCore.QEvent):
    def __init__(self, callback, error=False):
        super(CommandEvent, self).__init__(QtCore.QEvent.None)
        self.callback = callback
        self.error = error

class UpdateProgressEvent(QtCore.QEvent):
    def __init__(self, progress_bar, percent):
        super(UpdateProgressEvent, self).__init__(QtCore.QEvent.None)
        self.progress_bar = progress_bar
        self.percent      = percent


class TrayIcon(QtGui.QSystemTrayIcon):

    def __init__(self):
        QtGui.QSystemTrayIcon.__init__(self)

        self.setIcon(QtGui.QApplication.windowIcon())
        self.setVisible(True)

        self.temporary_balloon  = None
        self.persistent_balloon = MultiSmartDictBalloonMessage(title=_("UFO informations balloon"),
                                                               rearrange_callback=self.rearrange_balloons)
        self.balloons = [ self.persistent_balloon ]
        
        self.minimized = False
        self.on_top    = self.geometry().y() < screenRect.height() / 2

        self.connect(self, QtCore.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"),
                                         self.activate)
        self.show()

    def create_temporary_balloon(self, title, msg, progress, timeout, vlayout):
        if self.temporary_balloon:
            self.destroy_temporary_balloon()

        if timeout:
            self.destroytimer = QtCore.QTimer(self)
            self.connect(self.destroytimer, QtCore.SIGNAL("timeout()"), self.destroy_temporary_balloon)
            self.destroytimer.start(timeout)

        self.temporary_balloon = BalloonMessage(title=title,
                                                msg=msg,
                                                progress=progress,
                                                vlayout=vlayout,
                                                rearrange_callback=self.rearrange_balloons)
        self.balloons.insert(0, self.temporary_balloon)
        self.temporary_balloon.show()

    def update_temporary_balloon_message(self, msg):
        if self.temporary_balloon:
            self.temporary_balloon.set_message(msg)
            self.temporary_balloon.show()

    def update_temporary_balloon_progress(self, progress):
        if self.temporary_balloon and self.temporary_balloon.progress_bar:
            self.temporary_balloon.set_progress(progress)

    def destroy_temporary_balloon(self):
        if self.temporary_balloon:
            self.balloons.remove(self.temporary_balloon)
            self.temporary_balloon.hide()
            self.temporary_balloon.close()
            del self.temporary_balloon
            self.temporary_balloon = None

    def add_persistent_balloon_section(self, key, msg, default, smartdict, hlayout, progress):
        self.persistent_balloon.add_section(key, msg, default, smartdict, hlayout, progress)

    def destroy_persistent_balloon_section(self, key):
        if not key:
            sections = self.persistent_balloon.sections.keys()
            for section in sections:
                self.persistent_balloon.remove_section(section)
        else:
            self.persistent_balloon.remove_section(key)

    def update_persistent_balloon_message(self, key, msg):
        if self.persistent_balloon.sections.has_key(key):
            self.persistent_balloon.sections[key].set_message(msg)
            self.persistent_balloon.show()

    def update_persistent_balloon_progress(self, key, progress):
        if self.persistent_balloon.sections.has_key(key):
            self.persistent_balloon.sections[key].set_progress(progress)
        
    def rearrange_balloons(self):
        self.on_top = self.geometry().y() < screenRect.height() / 2
        if self.on_top:
            balloon_y = self.geometry().bottom() + 10
        else:
            balloon_y = self.geometry().top()
        
        for balloon in self.balloons:
            if balloon.isVisible():
                on_top_changed = self.on_top != balloon.on_top
                if not self.on_top:
                    balloon_y = balloon_y - balloon.height() - 10

                if not on_top_changed and \
                   ((self.on_top and balloon_y < balloon.y()) or \
                   (not self.on_top and balloon_y > balloon.y())):
                    balloon.move(screenRect.width() - balloon.width() - 10, balloon.y())
                    balloon.vertical_shift(balloon_y)
                else:
                    balloon.move(screenRect.width() - balloon.width() - 10, balloon_y)

                if self.on_top:
                    balloon_y = balloon_y + balloon.height() + 10
                balloon.on_top = self.on_top
        
    def activate(self, reason):
        if reason == QtGui.QSystemTrayIcon.DoubleClick:
            if self.minimized:
                app.normalize_window()
                self.minimized = False

            else:
                app.minimize_window()
                self.minimized = True

        elif reason != QtGui.QSystemTrayIcon.Context:
            if self.temporary_balloon:
                self.temporary_balloon.show()
                
            if len(self.persistent_balloon.sections):
                self.persistent_balloon.show()


class BalloonMessage(QtGui.QWidget):

    """
    Build a basic balloon message, customizable with
    a progress bar and a personnal widget.
    """

    DEFAULT_HEIGHT = 80
    DEFAULT_WIDTH  = 350

    def __init__(self, title, msg=None, progress=False, vlayout=None, fake=False, rearrange_callback=None):
        if sys.platform == "win32":
            flags = QtCore.Qt.WindowStaysOnTopHint | \
                    QtCore.Qt.ToolTip
        elif sys.platform == "linux2":
            flags = QtCore.Qt.WindowStaysOnTopHint | \
                    QtCore.Qt.X11BypassWindowManagerHint | \
                    QtCore.Qt.Popup
        else:
            flags = QtCore.Qt.WindowStaysOnTopHint | \
                    QtCore.Qt.Popup

        QtGui.QWidget.__init__(self, None, flags)

        self.title    = title
        self.msg      = msg
        self.fake     = fake
        self.progress = progress
        self.icon     = os.path.join(conf.IMGDIR, "UFO.png")
        self.colors   = { 'ballooncolor'         : conf.BALLOONCOLOR,
                          'ballooncolorgradient' : conf.BALLOONCOLORGRADIENT,
                          'ballooncolortext'     : conf.BALLOONCOLORTEXT }

        self.rearrange_callback = rearrange_callback

        self.show_timer = QtCore.QTimer(self)
        self.connect(self.show_timer, QtCore.SIGNAL("timeout()"), self.opacity_timer)
        self.move_timer = QtCore.QTimer(self)
        self.connect(self.move_timer, QtCore.SIGNAL("timeout()"), self.shift_timer)

        # Build basic balloon features: icon, title, msg
        self.baloon_layout   = QtGui.QHBoxLayout(self)
        self.contents_layout = QtGui.QVBoxLayout()

        image = QtGui.QLabel(self)
        image.setScaledContents(False)
        image.setPixmap(QtGui.QIcon(self.icon).pixmap(64, 64))
        self.baloon_layout.addWidget(image, 0, QtCore.Qt.AlignTop)

        self.title_layout = QtGui.QHBoxLayout()

        close_icon = QtGui.QIcon(os.path.join(conf.IMGDIR, "close.png"))
        self.close_button = QtGui.QPushButton(close_icon, "", self)
        self.close_button.setFlat(True)

        if self.fake:
            self.close_button.setDisabled(True)
        else:
            self.connect(self.close_button, QtCore.SIGNAL("clicked()"), self.hide)

        self.title_label = QtGui.QLabel("<b><font color=%s>%s</font></b>" % \
                                        (self.colors['ballooncolortext'], self.title))
        self.title_label.setPalette(QtGui.QToolTip.palette())
        self.title_label.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.title_layout.addWidget(self.title_label)

        if self.fake:
            self.title_layout.addSpacing(100)
        else:
            self.title_label.setMinimumWidth(250)

        self.title_layout.addWidget(self.close_button, 0, QtCore.Qt.AlignRight)
        self.contents_layout.addLayout(self.title_layout)

        if self.msg:
            self.text_label = QtGui.QLabel("<font color=%s>%s</font>" % \
                                           (self.colors['ballooncolortext'], msg))
            self.text_label.setPalette(QtGui.QToolTip.palette())
            self.text_label.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
            self.contents_layout.addWidget(self.text_label)
        else:
            self.text_label = None

        self.baloon_layout.addLayout(self.contents_layout)

        self.setAutoFillBackground(True)
        self.currentAlpha = 0
        self.setWindowOpacity(0.0)

        # Possibly add a progress bar
        if self.progress:
            self.progress_bar = QtGui.QProgressBar()
            self.contents_layout.addWidget(self.progress_bar)
            self.progress_bar.hide()
        else:
            self.progress_bar = None

        # Possibly add a custom widget (inherit QVBoxLayout)
        if vlayout:
            self.vlayout = vlayout['type'](*vlayout['args'])
            self.vlayout.set_parent(self)
            self.contents_layout.addLayout(self.vlayout)

        self.on_top = None

    def set_message(self, msg):
        self.msg = "<font color=%s>%s</font>" % (self.colors['ballooncolortext'], msg)
        self.text_label.setText(self.msg)

    def set_progress(self, progress):
        if self.progress_bar:
            progress = int(progress)
            if progress > 100:
                progress = 100
            if not self.progress_bar.isVisible() and int(progress) > 0:
                self.progress_bar.show()
            if progress == 100 and self.progress_bar.value() < 100:
                self.progress_timer = QtCore.QTimer(self)
                self.progress_timer.setSingleShot(True)
                self.connect(self.progress_timer, QtCore.SIGNAL("timeout()"), self.destroy_progress)
                self.progress_timer.start(3000)
            
            self.progress_bar.setValue(int(progress))
            
    def destroy_progress(self):
        if self.progress_bar and self.progress_bar.value() == 100:
            self.progress_bar.hide()
            self.resize_to_minimum()
            self.rearrange_callback()

    def opacity_timer(self):
        if self.currentAlpha <= 255:
            self.currentAlpha += 10
        else:
            self.show_timer.stop()
        self.setWindowOpacity(1. / 255. * self.currentAlpha)

    def shift_timer(self):
        self.shift = 5
        if self.current_shift != 0:
            if self.current_shift < 0:
                if self.current_shift + self.shift > 0:
                    diff = self.current_shift + self.shift
                    self.shift = self.shift - diff

                self.move(self.x(), self.y() - self.shift)
                self.current_shift = self.current_shift + self.shift

            else:
                if self.current_shift - self.shift < 0:
                    diff = self.current_shift - self.shift
                    self.shift = self.shift + diff

                self.move(self.x(), self.y() + self.shift)
                self.current_shift = self.current_shift - self.shift
        else:
            self.move_timer.stop()
    
    def resizeEvent(self, evt):
        if self.fake:
            return

        self.setMask(self.draw())
        self.resize_to_minimum()
        self.rearrange_callback()

    def hideEvent(self, evt):
        if self.fake:
            return

        self.currentAlpha = 0
        self.setWindowOpacity(0.0)
        self.rearrange_callback()
            
    def closeEvent(self, evt):
        if self.fake:
            return

        self.rearrange_callback()

    def paintEvent(self, evt):
        self.draw(event=True)

    def showEvent(self, event):
        if self.fake:
            return

        self.show_timer.start(1)
        self.resize_to_minimum()
        self.rearrange_callback()

    def resize_to_minimum(self):
        self.contents_layout.layout().activate()
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

    def vertical_shift(self, new_y):
        self.current_shift = new_y - self.y()
        self.move_timer.start(1)

    def draw(self, event=False):
        self.title_label.setText("<b><font color=%s>%s</font></b>" % \
                                 (self.colors['ballooncolortext'], self.title))
        if self.text_label:
            self.text_label.setText("<font color=%s>%s</font>" % \
                                    (self.colors['ballooncolortext'], self.msg))

        path = QtGui.QPainterPath()
        if hasattr(path, "addRoundedRect"):
            path.addRoundedRect(QtCore.QRectF(0, 0, self.width(), self.height()), 7, 7)
        else:
            path.addRect(QtCore.QRectF(0, 0, self.width(), self.height()))

        if event:
            painter = QtGui.QPainter(self)
        else:
            pixmap = QtGui.QPixmap(self.size())
            painter = QtGui.QPainter()
            painter.begin(pixmap)

        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2, QtCore.Qt.SolidLine))
        painter.setClipPath(path)
        gradient = QtGui.QLinearGradient(0, 0, 0, 100);
        gradient.setColorAt(0.0, QtGui.QColor(self.colors['ballooncolor']));
        gradient.setColorAt(1.0, QtGui.QColor(self.colors['ballooncolorgradient']));
        painter.setBrush(gradient);
        painter.drawPath(path)
        mask = painter.clipRegion()
        if not event:
            painter.end()
        return mask


class MultiSmartDictBalloonMessage(BalloonMessage):
    def __init__(self, title, rearrange_callback=None):
        BalloonMessage.__init__(self, title=title, rearrange_callback=rearrange_callback)

        self.progress_bar_root = QtGui.QProgressBar()
        self.progress_bar_user = QtGui.QProgressBar()
        self.progress_bar_public = QtGui.QProgressBar()
        self.progress_bar_root.setMaximumHeight(50)
        self.progress_bar_user.setMaximumHeight(50)
        self.progress_bar_user.setMaximumHeight(50)
        self.layout_root = QtGui.QHBoxLayout()
        self.layout_user = QtGui.QHBoxLayout()
        self.layout_public = QtGui.QHBoxLayout()
        self.label_space = QtGui.QLabel(_("Free space available:"))
        self.label_root = QtGui.QLabel("<i>" + _("Applications") + "</i>")
        self.label_user = QtGui.QLabel("<i>" + str(conf.USER) + "</i>")
        self.label_public = QtGui.QLabel("<i>" + _("Public") + "</i>")
        self.label_root.setMinimumWidth(160)
        self.label_user.setMinimumWidth(160)
        self.label_public.setMinimumWidth(160)
        self.layout_root.addWidget(self.label_root)
        self.layout_user.addWidget(self.label_user)
        self.layout_public.addWidget(self.label_public)
        self.layout_root.addWidget(self.progress_bar_root)
        self.layout_user.addWidget(self.progress_bar_user)
        self.layout_public.addWidget(self.progress_bar_public)
        self.contents_layout.addWidget(self.label_space)
        self.contents_layout.addLayout(self.layout_root)
        self.contents_layout.addLayout(self.layout_user)
        self.contents_layout.addLayout(self.layout_public)
        self.label_space.hide()
        self.label_root.hide()
        self.label_user.hide()
        self.label_public.hide()
        self.progress_bar_root.hide()
        self.progress_bar_user.hide()
        self.progress_bar_public.hide()
        self.sections = {}

    def add_section(self, key, msg, default, smartdict, hlayout, progress=False):
        if not self.sections.has_key(key):
            assert isinstance(smartdict, SmartDict)

            self.sections[key] = SmartDictLayout(self, msg, default, smartdict, hlayout, progress)
            self.contents_layout.addLayout(self.sections[key])
            self.sections[key].refresh()
            self.resize_to_minimum()
            self.rearrange_callback()

    def remove_section(self, key):
        if not self.sections.has_key(key):
            logging.debug("Failed to remove balloon section '%s'" % (key,))
        else:
            self.sections[key].hide()
            del self.sections[key]
            self.resize_to_minimum()
            if not len(self.sections):
                self.hide()
            self.rearrange_callback()

    def update_progress_root(self, percent):
        self.progress_bar_root.setValue(int(percent))
        self.progress_bar_root.show()
        self.label_root.show()
        self.label_space.show()

    def update_progress_user(self, percent):
        self.progress_bar_user.setValue(int(percent))
        self.progress_bar_user.show()
        self.label_user.show()
        self.label_space.show()

    def update_progress_public(self, percent):
        self.progress_bar_public.setValue(int(percent))
        self.progress_bar_public.show()
        self.label_public.show()
        self.label_space.show()


class SmartDictLayout(QtGui.QVBoxLayout):
    def __init__(self, parent, msg, default, smartdict, hlayout, progress):
        QtGui.QVBoxLayout.__init__(self)

        self.parent    = parent
        self.smartdict = smartdict
        self.hlayout   = hlayout

        # Restering callback to handle updates on the dict
        self.smartdict.register_on_set_item_callback(self.refresh)
        self.smartdict.register_on_del_item_callback(self.refresh)
        
        # Registring callbck to resize balloon
        self.smartdict.register_on_set_item_callback(self.resize_smartdisct_balloon)
        self.smartdict.register_on_del_item_callback(self.resize_smartdisct_balloon)

        self.hline = QtGui.QFrame()
        self.hline.setFrameShape(QtGui.QFrame.HLine)
        self.hline.setFrameShadow(QtGui.QFrame.Sunken)

        self.text_label = QtGui.QLabel("<font color=%s>%s</font>" % \
                                                     (self.parent.colors['ballooncolortext'], msg))
        self.text_label.setPalette(QtGui.QToolTip.palette())
        self.text_label.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        self.addWidget(self.hline)
        self.addWidget(self.text_label)

        if progress:
            self.progress_bar = QtGui.QProgressBar()
            self.addWidget(self.progress_bar)
            self.progress_bar.hide()
        else:
            self.progress_bar = None

        self.default = QtGui.QLabel("<i>" + default + "</i>")
        self.addWidget(self.default)

        self.diplayed_hlayouts = {}

    def resize_smartdisct_balloon(self, key=None, value=None):
        self.layout().activate()
        self.parent.resize_to_minimum()
        self.parent.rearrange_callback()

    def set_message(self, msg):
        self.text_label.setText(QtCore.QString("<font color=%s>%s</font>" % \
                                              (self.parent.colors['ballooncolortext'], msg)))

    def set_progress(self, progress):
        if self.progress_bar:
            progress = int(progress)
            if progress > 100:
                progress = 100
            if not self.progress_bar.isVisible() and int(progress) > 0:
                self.progress_bar.show()
            if progress == 100 and self.progress_bar.value() < 100:
                self.progress_timer = QtCore.QTimer(self)
                self.progress_timer.setSingleShot(True)
                self.connect(self.progress_timer, QtCore.SIGNAL("timeout()"), self.destroy_progress)
                self.progress_timer.start(3000)
            
            self.progress_bar.setValue(int(progress))
            
    def destroy_progress(self):
        if self.progress_bar and self.progress_bar.value() == 100:
            self.progress_bar.hide()
            self.layout().activate()
            self.parent.resize_to_minimum()
            self.parent.rearrange_callback()
            
    def refresh(self, key=None, value=None):
        self.old_displayed_hlayouts = self.diplayed_hlayouts.copy()

        # Handle new elements
        for item in self.smartdict:
            if not self.diplayed_hlayouts.has_key(item):
                self.diplayed_hlayouts[item] = \
                    self.hlayout['type'](*((self.smartdict[item],) + self.hlayout['args']))
                self.addLayout(self.diplayed_hlayouts[item])
                self.parent.show()

            else:
                del self.old_displayed_hlayouts[item]

        # And then remove deprecated ones
        for item in self.old_displayed_hlayouts:
            self.diplayed_hlayouts[item].hide()
            del self.diplayed_hlayouts[item]
        
        if len(self.diplayed_hlayouts):
            self.default.hide()
            self.removeWidget(self.default)

        else:
            self.addWidget(self.default)
            self.default.show()

    def hide(self):
        if len(self.diplayed_hlayouts):
            for item in self.diplayed_hlayouts:
                self.diplayed_hlayouts[item].hide()
            del self.diplayed_hlayouts[item]

        else:
            self.default.hide()
            self.removeWidget(self.default)

        self.hline.hide()
        self.text_label.hide()
        self.removeWidget(self.hline)
        self.removeWidget(self.text_label)

        if self.progress_bar:
            self.progress_bar.hide()
            self.removeWidget(self.progress_bar)
            del self.progress_bar

        del self.hline
        del self.text_label
        self.parent.rearrange_callback()


class UsbAttachementLayout(QtGui.QHBoxLayout):
    def __init__(self, usb, callback):
        QtGui.QHBoxLayout.__init__(self)

        self.usb      = usb
        self.callback = callback

        self.usb_label = QtGui.QLabel(self.usb['name'] + " (" + self.usb['path'] + ")")
        if self.usb['attach']:
            button_msg  = _("Detach")
            button_icon = QtGui.QIcon(os.path.join(conf.IMGDIR, "eject.png"))
        else:
            button_msg = _("Attach")
            button_icon = QtGui.QIcon(os.path.join(conf.IMGDIR, "attach.png"))
        self.attach_button = QtGui.QPushButton(button_icon, button_msg)
        self.attach_button.setFlat(True)
        self.attach_button.setMaximumSize(100, 22)

        self.addWidget(self.usb_label)
        self.addWidget(self.attach_button)
        self.connect(self.attach_button, QtCore.SIGNAL("clicked()"), self.attach)

    def attach(self):
        if self.usb['attach']:
            self.attach_button.setText(_("Attach"))
            self.attach_button.setIcon(QtGui.QIcon(os.path.join(conf.IMGDIR, "attach.png")))
        else:
            self.attach_button.setText(_("Detach"))
            self.attach_button.setIcon(QtGui.QIcon(os.path.join(conf.IMGDIR, "eject.png")))

        self.callback(self.usb, attach=not self.usb['attach'])

    def hide(self):
        self.attach_button.hide()
        self.usb_label.hide()
        self.removeWidget(self.attach_button)
        self.removeWidget(self.usb_label)
        del self.attach_button
        del self.usb_label


class VirusFoundLayout(QtGui.QHBoxLayout):
    def __init__(self, virus, callback):
        QtGui.QHBoxLayout.__init__(self)

        self.virus    = virus
        self.callback = callback

        self.virus_infos_layout = QtGui.QVBoxLayout()
        self.virus_name = QtGui.QLabel(self.virus['name'])
        self.virus_path = QtGui.QLabel("<i><font size=2>" + self.virus['pretty'] + "</font></i>")
        self.virus_infos_layout.addWidget(self.virus_name)
        self.virus_infos_layout.addWidget(self.virus_path)
        del_button_msg   = _("Delete")
        del_button_icon  = QtGui.QIcon(os.path.join(conf.IMGDIR, "delete_virus.png"))
        pass_button_msg  = _("Ignore")
        pass_button_icon = QtGui.QIcon(os.path.join(conf.IMGDIR, "ignore_virus.png"))
        self.del_button = QtGui.QPushButton(del_button_icon, del_button_msg)
        self.del_button.setFlat(True)
        self.del_button.setMaximumSize(80, 22)
        self.pass_button = QtGui.QPushButton(pass_button_icon, pass_button_msg)
        self.pass_button.setFlat(True)
        self.pass_button.setMaximumSize(80, 22)

        self.addLayout(self.virus_infos_layout)
        self.addWidget(self.del_button)
        self.addWidget(self.pass_button)
        self.connect(self.del_button, QtCore.SIGNAL("clicked()"), self.action)
        self.connect(self.pass_button, QtCore.SIGNAL("clicked()"), self.action)

    def action(self):
        import clamavgui
        control = self.sender()
        if control == self.del_button:
            self.callback(self.virus['path'], clamavgui.VIRUS_DELETE)
        elif control == self.pass_button:
            self.callback(self.virus['path'], clamavgui.VIRUS_IGNORE)
        
    def hide(self):
        self.del_button.hide()
        self.pass_button.hide()
        self.virus_name.hide()
        self.virus_path.hide()
        self.virus_infos_layout.removeWidget(self.virus_name)
        self.virus_infos_layout.removeWidget(self.virus_path)
        self.removeWidget(self.del_button)
        self.removeWidget(self.pass_button)
        del self.del_button
        del self.pass_button
        del self.virus_name
        del self.virus_path
        del self.virus_infos_layout


class CredentialsLayout(QtGui.QVBoxLayout):
    def __init__(self, callback, keyring):
        QtGui.QVBoxLayout.__init__(self)

        self.callback = callback
        self.keyring  = keyring

        if self.callback and conf.USER != "":
            button_msg = "(" + conf.USER + ") - "
            if self.keyring:
                button_msg += _("You already are authenticated")
            else:
                button_msg += _("Authenticate")

            self.hbox = hbox = QtGui.QHBoxLayout()
            button_icon = QtGui.QIcon(os.path.join(conf.IMGDIR, "credentials.png"))
            self.expand_button = QtGui.QPushButton(button_icon, button_msg)
            self.expand_button.setFlat(True)
            self.expand_button.setDefault(True)
            self.connect(self.expand_button, QtCore.SIGNAL("clicked()"), self.expand)
            hbox.addWidget(self.expand_button, 0, QtCore.Qt.AlignLeft)

            if conf.GUESTMODE:
                self.guest_button = QtGui.QPushButton(_("Guest mode"))
                self.connect(self.guest_button, QtCore.SIGNAL("clicked()"), self.on_guest_mode)
                hbox.addWidget(self.guest_button, 0, QtCore.Qt.AlignLeft)

            self.addLayout(hbox)
            self.expanded = False

    def set_parent(self, parent_widget):
        self.parent = parent_widget

    def valid_credentials(self):
        if self.password.text():
            if self.callback:
                self.callback(conf.USER, self.password.text(), self.remember.isChecked())
            if len(self.expand_button.text()) - len(conf.USER) - 10 > len(_("Authenticate")):
                offset = 42
            else:
                offset = 23
            self.expand_button.setText(QtCore.QString("(" + conf.USER + ")" + (offset * " ")))
        self.collapse()

    def expand(self):
        assert hasattr(self, "parent")

        if self.expanded:
            self.collapse()
            return

        self.expand_widgets = []
        self.hline = QtGui.QFrame()
        self.hline.setFrameShape(QtGui.QFrame.HLine)
        self.hline.setFrameShadow(QtGui.QFrame.Sunken)

        self.pass_label = QtGui.QLabel(_("UFO password:"))
        self.password = QtGui.QLineEdit()
        self.password.setEchoMode(QtGui.QLineEdit.Password)

        self.ok_button = QtGui.QPushButton("Ok")
        self.ok_button.setMaximumSize(32, 28)
        self.remember = QtGui.QCheckBox(_("Remember my password"))

        self.connect(self.password, QtCore.SIGNAL("returnPressed()"), self.valid_credentials)
        self.connect(self.ok_button, QtCore.SIGNAL("clicked()"), self.valid_credentials)

        self.password_field = QtGui.QHBoxLayout()
        self.add_expdand_contents(self, self.hline)
        self.add_expdand_contents(self.password_field, self.pass_label)
        self.add_expdand_contents(self.password_field, self.password, 100)
        self.add_expdand_contents(self.password_field, self.ok_button)
        self.addLayout(self.password_field)
        self.add_expdand_contents(self, self.remember)
        self.expanded = True

    def collapse(self):
        self.expanded = False
        for widget in self.expand_widgets:
            widget.hide()
        self.layout().activate()
        self.parent.resize_to_minimum()

    def add_expdand_contents(self, layout, item, offset=None):
        if offset:
            layout.addWidget(item, offset)
        else:
            layout.addWidget(item)
        self.expand_widgets.append(item)

    def on_guest_mode(self):
        conf.USER = conf.GUESTUSER
        if self.callback:
            self.callback(conf.USER, " ", False)
        if len(self.expand_button.text()) - len(conf.USER) - 10 > len(_("Authenticate")):
            offset = 42
        else:
            offset = 23
        self.expand_button.setText(QtCore.QString("(" + _("Guest mode") + ") - " + _("Authenticate")))
        self.guest_button.hide()
        self.hbox.removeWidget(self.guest_button)


class Downloader(threading.Thread):
    def __init__(self, file, dest, progress, finished_callback):
        threading.Thread.__init__(self)
        self.file = file
        self.dest = dest
        self.to_be_stopped = False
        self.progress = progress
        self.finished_callback = finished_callback

    def run(self):
        try:
            remote = urlopen(self.file)
            if hasattr(remote, "code") and remote.code == 404:
                raise Exception("404 error")
            remote.close()

            urlretrieve(self.file, self.dest, reporthook=self.on_progress)

            if not os.path.exists(self.dest):
                # The only way to detect 404 error with python < 2.6
                raise Exception("404 error")
        except:
            app.postEvent(app, JobFinishedEvent(self.finished_callback, True))
        else:
            app.postEvent(app, JobFinishedEvent(self.finished_callback, False))
        sys.exit()

    def on_progress(self, count, blockSize, totalSize):
        if not self.progress: return
        if self.to_be_stopped == True:
            sys.exit()
        self.count = count
        self.maximum = totalSize
        self.downloaded = float(blockSize*count)/totalSize
        app.postEvent(app, UpdateProgressEvent(self.progress,
                                                int(self.downloaded * 100)))

    def stop(self):
        self.to_be_stopped = True


class CommandLauncher(threading.Thread):
    def __init__(self, cmd, callback): 
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.callback = callback

    def run(self):
        error = False
        if isinstance(self.cmd[0], str):
            if utils.call(self.cmd) != 0:
                error = True
        else:
            try:
                self.cmd[0](*self.cmd[1:])
            except:
                error = True

        app.postEvent(app, CommandEvent(self.callback, error))
        sys.exit()


class Extractor(threading.Thread):
    def __init__(self, tar, dest, progress, finished_callback, tarcmd=False):
        threading.Thread.__init__(self)
        self.tar  = tar
        self.dest = dest
        self.progress = progress
        self.finished_callback = finished_callback

    def run(self):
        try:
            members  = self.tar.getmembers()
            nb_files = len(members)

            self.step  = nb_files / 100.0
            self.count = 0
            for m in members:
                self.tar.extract(m, self.dest)
                self.count = self.count + 1
                if int(self.count / self.step) > self.progress.value():
                    self.on_progress(self.count / self.step)

        except:
            app.postEvent(app, JobFinishedEvent(self.finished_callback, True))
        else:
            app.postEvent(app, JobFinishedEvent(self.finished_callback, False))
        sys.exit()

    def on_progress(self, percent):
        app.postEvent(app, UpdateProgressEvent(self.progress, percent))


class WaitWindow(QtGui.QDialog):
    def __init__(self, cmd, title, msg, success_msg, error_msg, parent=None):
        super(WaitWindow, self).__init__(main)
        self.cmd = cmd
        self.setWindowTitle(title)
        self.command = CommandLauncher(self.cmd, self.finished)
        self.msg = msg
        self.success_msg = success_msg
        self.error_msg = error_msg
        self.statusLabel = QtGui.QLabel(self.msg)
        self.cancelButton = QtGui.QPushButton(_("Cancel"))
        self.animation = QtGui.QLabel()
        self.animation.setAlignment(QtCore.Qt.AlignCenter)
        self.animation.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.addButton(self.cancelButton, QtGui.QDialogButtonBox.ActionRole)
        self.cancelButton.hide()
        topLayout = QtGui.QHBoxLayout()
        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(topLayout)
        main_layout.addWidget(self.statusLabel)
        main_layout.addWidget(buttonBox)
        main_layout.addWidget(self.animation)
        self.setLayout(main_layout)

        self.animated = QtGui.QMovie(os.path.join(conf.IMGDIR, "animated-bar.mng"), 
                                     QtCore.QByteArray(), 
                                     self.animation)
        self.animated.setCacheMode(QtGui.QMovie.CacheAll)
        self.animated.setSpeed(100)
        self.animation.setMovie(self.animated)

        self.animated.start()
        self.command.start()

    def finished(self, error):
        if error:
            self.reject()
        else:
            self.accept()


class DownloadWindow(QtGui.QDialog):
    def __init__(self, url, filename, title, msg, autostart,
                 success_msg, autoclose=False,
                 embedded_progress=True, parent=None):
        super(DownloadWindow, self).__init__(parent)
        self.url = url
        self.fileName = filename
        self.autostart = autostart
        self.autoclose = autoclose
        self.success_msg = success_msg
        self.outFile = None
        self.httpGetId = 0
        self.http_request_aborted = False
        self.finished = False
        self.statusLabel = QtGui.QLabel(msg)
        self.embedded_progress = embedded_progress
        self.progress_dialog = None
        self.progress_bar = None
        self.downloading = False
        self.downloadButton = QtGui.QPushButton(_("Download"))
        self.downloadButton.setDefault(True)
        self.actionButton = QtGui.QPushButton(_("Cancel"))
        self.actionButton.setAutoDefault(False)
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.addButton(self.downloadButton,
                QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(self.actionButton, QtGui.QDialogButtonBox.RejectRole)
        self.connect(self.downloadButton, QtCore.SIGNAL("clicked()"), self.download_file)
        self.connect(self.actionButton, QtCore.SIGNAL("clicked()"), self.action)
        topLayout = QtGui.QHBoxLayout()
        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(topLayout) 
        main_layout.addWidget(self.statusLabel)
        main_layout.addWidget(buttonBox)
        self.setLayout(main_layout)
        self.setWindowTitle(title)
        if self.autostart:
            self.download_file()

    def hide_progress(self):
        self.progress_bar.hide()
        self.layout().removeWidget(self.progress_bar)
        self.progress_bar = None

    def action(self):
        if self.embedded_progress:
            if self.downloading:
                self.cancel_download()
                self.hide_progress()
                self.actionButton.setText(_("Cancel"))
                return
        if self.finished:
            self.accept()
        else:
            self.reject()

    def init_downloader(self):
        if self.progress_dialog:
            progress = self.progress_dialog
        else:
            progress = self.progress_bar
        self.downloader = Downloader(self.url, 
                                     self.fileName, 
                                     progress=progress, 
                                     finished_callback=self.http_request_finished)

    def was_canceled(self):
        return self.http_request_aborted
        
    def download_file(self):
        self.http_request_aborted = False
        if self.finished:
            self.accept()
        fileName = self.fileName
        self.outFile = QtCore.QFile(fileName)
        if not self.outFile.open(QtCore.QIODevice.WriteOnly):
            QtGui.QMessageBox.information(self, 
                                          _("Error"), 
                                          _("Could not write to file %s: %s.") % \
                                              (fileName, self.outFile.errorString()))
            self.outFile = None
            return
        if self.embedded_progress:
            self.progress_bar = QtGui.QProgressBar(self)
            app.progress = self.progress_bar
            self.layout().insertWidget(self.layout().count() - 1, self.progress_bar)
            self.actionButton.setText(_("Cancel"))
            # self.connect(self.actionButton, QtCore.SIGNAL("clicked()"), self.cancel_download)
        else:
            self.progress_dialog = QtGui.QProgressDialog(self)
            app.progress = self.progress_dialog
            self.connect(self.progress_dialog, QtCore.SIGNAL("canceled()"), self.cancel_download)
            self.progress_dialog.setCancelButtonText(u"Annuler")
            self.progress_dialog.setWindowTitle(_("Downloading"))
            self.progress_dialog.setLabelText(_("Downloading to %s") %(fileName, ))
            self.progress_dialog.show()
            
        self.downloading = True
        self.downloadButton.setEnabled(False)
        # On prépare le thread qui gérera le téléchargement
        self.init_downloader()
        self.downloader.start()

    def cancel_download(self):
        self.statusLabel.setText(_("Download canceled.\n"
                                   "Press 'Download' to retry"))
        self.http_request_aborted = True
        self.downloading = False
        self.downloader.stop()
        self.downloadButton.setEnabled(True)

    def http_request_finished(self,  error):
        self.downloading = False
        if self.downloader.isAlive():
            self.downloader.join()

        self.init_downloader()
        if self.http_request_aborted:
            if self.outFile is not None:
                self.outFile.close()
                self.outFile.remove()
                self.outFile = None
            if not self.embedded_progress:
                self.progress_dialog.hide()
            return

        if not self.embedded_progress:
            self.progress_dialog.hide()
        self.outFile.close()
        if error:
            self.outFile.remove()
            self.done(0)

        else:
            self.finished = True
            self.downloadButton.hide()
            self.actionButton.setText(_("Continue"))
            self.statusLabel.setText(self.success_msg)
            self.hide_progress()

        if self.autoclose:
            self.accept()
            
        self.downloadButton.setEnabled(True)
        self.outFile = None


class ExtractWindow(QtGui.QProgressDialog):
    def __init__(self, tgz, dest, title, msg):
        super(ExtractWindow, self).__init__(main)
        self.tgz   = tgz
        self.dest  = dest
        self.title = title
        self.msg   = QtGui.QLabel(msg)
        self.cancel   = QtGui.QPushButton(_("Cancel"))
        self.progress = QtGui.QProgressBar(self)
        self.setLabel(self.msg)
        self.cancel.setEnabled(False)
        self.setCancelButton(self.cancel)
        self.setBar(self.progress)
        self.setWindowTitle(title)

        self.extractor = Extractor(self.tgz,
                                   self.dest,
                                   progress=self.progress,
                                   finished_callback=self.extraction_finished)
        self.extractor.start()

    def extraction_finished(self, error):
        if error:
            self.reject()
        else:
            self.accept()


class OurMessageBox(QtGui.QMessageBox):
    def set_minimum_size(self, width, height):
        self._minSize = (width, height)

    def show_event(self, event):
        QtGui.QMessageBox.show_event(self, event)
        if hasattr(self, "_minSize"):
            self.setFixedSize(*self._minSize)


class SplashScreen:
    def __init__(self, image):
        pixmap = QtGui.QPixmap(image)
        self.splash = QtGui.QSplashScreen(pixmap)
        self.splash.show()

    def destroy(self):
        self.splash.close()


class ListDialog(QtGui.QDialog):
    def __init__(self, parent=None, title="List", msg="msg", choices=[]):
        super(ListDialog, self).__init__(parent)
        msglabel = QtGui.QLabel(msg)
        self.choicelist = QtGui.QListWidget()        
        for i in choices:
            self.choicelist.addItem(i)
        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttonbox.accepted.connect(self.accept)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(msglabel)
        layout.addWidget(self.choicelist)
        layout.addWidget(buttonbox)
        self.setLayout(layout)
        self.setWindowTitle(title)


class Settings(QtGui.QDialog):
    def __init__(self, parent=None, tabs=None, fields=None,
                 show_default_button=True, no_reboot=False):
        super(Settings, self).__init__(parent)

        self.registred_selections = {}
        self.corresponding_values = {}
        self.custom_handlers      = {}
        self.groups               = {}
        self.no_reboot            = no_reboot
        
        # Registering custom handlers and layouts
        
        self.register_custom_handler('ballooncolors',
                                     self.create_balloon_custom_layout(),
                                     self.on_balloon_color_selection)
        self.register_custom_handler('guestdebug',
                                     self.create_debug_custom_layout())
        
        # Fill main dialog with configuration tabs
        
        tabWidget = QtGui.QTabWidget()
        tabWidget.setUsesScrollButtons(False)
        for tab in conf.settings:
            tab_name = unicode(self.tr(tab['tabname']))
            if (not tabs) or (tab_name in tabs):
                tabWidget.addTab(self.createOneTab(tab, fields=fields),
                                 QtGui.QIcon(os.path.join(conf.IMGDIR, tab['iconfile'])),
                                 tab_name)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(tabWidget)
        
        # Build controls buttons
        
        valid_layout   = QtGui.QHBoxLayout()

        ok_button      = QtGui.QPushButton(self.tr(_("Ok")))
        ok_button.clicked.connect(self.on_validation)
        valid_layout.addWidget(ok_button)

        cancel_button  = QtGui.QPushButton(self.tr(_("Cancel")))
        cancel_button.clicked.connect(self.on_cancel)
        valid_layout.addWidget(cancel_button)

        if show_default_button:
            default_button = QtGui.QPushButton(self.tr(_("Defaults")))
            default_button.clicked.connect(self.on_default)
            valid_layout.addWidget(default_button)

        main_layout.addLayout(valid_layout)
        self.setLayout(main_layout)

        self.setWindowTitle(self.tr(_("UFO settings")))
        
    def createOneTab(self, tab, fields=[]):
        widget     = QtGui.QWidget()
        tab_layout = QtGui.QVBoxLayout()
        
        for setting in tab['settings']:
            if fields:
                if setting.get('confid') not in fields:
                    continue
                else:
                    setting['value'] = self.get_conf(setting.get('confid'))
                    self.registred_selections.update({ setting.get('confid') : setting })

            if setting.get('hide') and setting['hide']:
                continue

            set_layout = QtGui.QVBoxLayout()
            label = QtGui.QLabel(self.tr(setting['label']))
            label.setWordWrap(True)
            set_layout.addWidget(label)
            
            if setting.has_key('group'):
                item_tab = setting['group']
                custom = self.custom_handlers.get(setting['grpid'])
                for i in item_tab:
                    self.groups.update({ i['confid'] : setting['grpid'] })
            else:
                item_tab = [ setting ]
                custom = self.custom_handlers.get(setting['confid'])
                
            for item in item_tab:
                if type(item.get('values')) == dict:
                    
                    # Here build an exclusive radio button group, and associate
                    # one combo box list for each radio button of the group
                    
                    group      = QtGui.QButtonGroup()
                    val_layout = QtGui.QHBoxLayout()
                    val_layout.addSpacing(30)
                    
                    col_tab = {}
                    for col in item['values'].keys():
                        col_layout = QtGui.QVBoxLayout()
                        radio      = QtGui.QRadioButton(self.tr(col))
                        group.addButton(radio)
                        col_layout.addWidget(radio)
                        
                        values = QtGui.QComboBox()
                        for val in item['values'][col]:
                            values.addItem(val)
                            
                        col_tab.update({ radio : values })
                        
                        # Connect items to action slot
                        
                        values.conf_infos = item
                        values.connect(values, 
                                       QtCore.SIGNAL("activated(const QString &)"), 
                                       self.on_selection)
                        if custom and custom['function']:
                            values.connect(values, 
                                           QtCore.SIGNAL("activated(const QString &)"), 
                                           custom['function'])
                        
                        col_layout.addWidget(values)
                        val_layout.addLayout(col_layout)
                        val_layout.addSpacing(30)
                        
                    set_layout.addLayout(val_layout)
                    group.setExclusive(True)
                    for radio in col_tab.keys():
                        for combo in col_tab.values():
                            if col_tab[radio] != combo:
                                radio.toggled.connect(combo.setDisabled)
                        
                        # Set current value
                        
                        if self.get_conf(item['confid']) in item['values'][str(radio.text())]:
                            radio.setChecked(QtCore.Qt.Checked)
                            index = item['values'][str(radio.text())].index(self.get_conf(item['confid']))
                            col_tab[radio].setCurrentIndex(index)
                        
                elif type(item.get('values')) == list:
                    
                    # Here build a combo box list with list values
                    
                    if item.has_key('strgs'):
                        assert len(item['values']) == len(item['strgs'])
                        
                        corr_vals = {}
                        for string in item['strgs']:
                            try:
                                index = item['strgs'].index(string)
                            except ValueError:
                                index = 0
                            corr_vals.update({ string : item['values'][index] })

                        self.corresponding_values.update({ item['confid'] : corr_vals })
                        value_key = 'strgs'
                    else:
                        value_key = 'values'
                        
                    val_layout = QtGui.QHBoxLayout()
                    val_layout.addSpacing(30)
                    
                    values = QtGui.QComboBox()
                    for val in item[value_key]:
                        values.addItem(val)
                    
                    # Connect items to action slot
                    
                    values.conf_infos = item
                    values.connect(values, 
                                   QtCore.SIGNAL("activated(const QString &)"), 
                                   self.on_selection)
                    if custom and custom['function']:
                        values.connect(values, 
                                       QtCore.SIGNAL("activated(const QString &)"), 
                                       custom['function'])
                        
                    # Set current value
                    try:
                        current_index = item['values'].index(self.get_conf(item['confid']))
                    except ValueError:
                        current_index = 0
                    values.setCurrentIndex(current_index)
                    
                    val_layout.addWidget(values)
                    val_layout.addSpacing(30)
                    set_layout.addLayout(val_layout)
                    
                elif type(item.get('range')) == list:
                    
                    # Here build integer value edit with specific range
                    
                    val_layout = QtGui.QHBoxLayout()
                    val_layout.addSpacing(30)
                    
                    spin = QtGui.QSpinBox()
                    spin.setMinimumWidth(75)
                    min, max = item['range'][0], item['range'][1]
                    
                    interval = int(math.ceil((max - min +1) / 16))
                    spin.setRange(min, max)
                    spin.setSingleStep(interval)
                    slider = QtGui.QSlider(QtCore.Qt.Horizontal)
                    slider.setFocusPolicy(QtCore.Qt.StrongFocus)
                    slider.setTickPosition(QtGui.QSlider.TicksBothSides)
                    slider.setRange(min, max)
                    slider.setTickInterval(interval)
                    slider.setSingleStep(interval)
                    
                    slider.valueChanged.connect(spin.setValue)
                    spin.valueChanged.connect(slider.setValue)
                    
                    # Set current value
                    
                    current_value = self.get_conf(item['confid'])
                    if current_value != conf.AUTO_INTEGER:
                        spin.setValue(current_value)
                        
                    # Connect items to action slot
                    
                    spin.conf_infos = item
                    slider.conf_infos = item
                    spin.valueChanged.connect(self.on_selection)
                    if custom and custom['function']:
                        spin.valueChanged.connect(custom['function'])
                            
                    if item.get('autocb') == True:
                        checkbox = QtGui.QCheckBox(self.tr(_("Auto")))
                                                
                        checkbox.conf_infos = item
                        checkbox.toggled.connect(slider.setDisabled)
                        checkbox.toggled.connect(spin.setDisabled)
                        
                        # Set current value
                        
                        if current_value == conf.AUTO_INTEGER:
                            checkbox.setChecked(QtCore.Qt.Checked)
                            
                        # Connect items to action slot
                        
                        checkbox.toggled.connect(self.on_selection)
                        if custom and custom['function']:
                            checkbox.toggled.connect(custom['function'])
                        
                        val_layout.addWidget(checkbox)
                    
                    val_layout.addWidget(spin)
                    val_layout.addWidget(slider)
                    val_layout.addSpacing(30)
                    set_layout.addLayout(val_layout)
                    
                else:
                    
                    # Here build value edit item corresponding to variable type
                    
                    current_value = self.get_conf(item['confid'])
                    
                    val_layout = QtGui.QHBoxLayout()
                    val_layout.addSpacing(30)
                    if type(current_value) == bool:
                        edit   = QtGui.QCheckBox(self.tr(item['short']))
                        signal = edit.toggled
                        funct  = self.on_selection

                        # Set current value
                        
                        if current_value:
                            edit.setChecked(QtCore.Qt.Checked)
                            
                    elif type(current_value) == str:
                        if len(current_value) > 0 and current_value[0] == '#':
                            
                            # Set current value
                            
                            edit = QtGui.QPushButton()
                            edit.buttonforcolor = True
                            edit.setAutoFillBackground(True);
                            edit.setStyleSheet("background-color: " + current_value)
                            edit.setMaximumWidth(40)
                            edit.setMaximumHeight(20)
                            signal = edit.clicked
                            funct  = self.on_color_selection
                            
                            # We will call possible custom function in
                            # the color_selection handler
                            
                            if custom and custom['function']:
                                custom = custom.copy()
                                custom['function'] = None

                            label = QtGui.QLabel(self.tr(item['short'] + ":"))
                            label.setWordWrap(True)
                            val_layout.addWidget(label)
                        
                        else:
                            
                            # Set current value
                            
                            if current_value == conf.AUTO_STRING:
                                value = ""
                            else:
                                value = current_value
                            edit   = QtGui.QLineEdit(value)
                            label  = QtGui.QLabel(self.tr(item['short']))
                            label.setWordWrap(True)
                            label.setMinimumWidth(150)
                            signal = edit.textChanged
                            funct  = self.on_selection
                            val_layout.addWidget(label)
                            
                    else:
                        raise Exception("Base type not yet supported")
                        
                    if item.get('autocb') == True:
                        checkbox = QtGui.QCheckBox(self.tr(_("Auto")))
                        
                        # Connect items to action slot
                        
                        if current_value == conf.AUTO_STRING:
                            checkbox.setChecked(QtCore.Qt.Checked)

                        checkbox.conf_infos = item
                        checkbox.toggled.connect(self.on_selection)
                        checkbox.toggled.connect(edit.setDisabled)
                        if custom and custom['function']:
                            checkbox.toggled.connect(custom['function'])
                            
                        val_layout.addWidget(checkbox)
                        
                    # Connect items to action slot
                        
                    edit.conf_infos = item
                    signal.connect(funct)
                    if custom and custom['function']:
                        signal.connect(custom['function'])
                    
                    val_layout.addWidget(edit)
                    val_layout.addSpacing(30)
                    set_layout.addLayout(val_layout)
                    
            tab_layout.addSpacing(15)
            tab_layout.addLayout(set_layout)
            
            if custom and custom['layout']:
                tab_layout.addLayout(custom['layout'])
                
            tab_layout.addStretch(1)
        
        tab_layout.addSpacing(15)
        widget.setLayout(tab_layout)
        return widget
        
    def on_selection(self, value):
        control = self.sender()

        if hasattr(control, 'text') and control.text() == _("Auto"):
            value = conf.get_auto_value(self.get_conf(control.conf_infos['confid']))
        
        if self.corresponding_values.has_key(control.conf_infos['confid']):
            value = self.corresponding_values[control.conf_infos['confid']][unicode(value)]
            
        control.conf_infos.update({ 'value' : value })
        self.registred_selections.update({ control.conf_infos['confid'] : control.conf_infos })
    
    def on_color_selection(self):
        control = self.sender()
        
        color = QtGui.QColorDialog.getColor(QtGui.QColor(self.get_conf(control.conf_infos['confid'])), self)
        if color.isValid():
            control.setStyleSheet("background-color: " + str(color.name()))
            
            self.on_selection(str(color.name()))
            if self.groups.get(control.conf_infos['confid']):
                customid = self.groups[control.conf_infos['confid']]
            else:
                customid = control.conf_infos['confid']
            if self.custom_handlers.get(customid):
                self.custom_handlers[customid]['function'](str(color.name()))
        
    def on_validation(self):
        if len(self.registred_selections) > 0:
            # yes = _("Yes")
            # no  = _("No")
            # msg = _("Would you validate the following changes ?") + "\n\n"
            # msg += self.get_changes_string()
            # TODO: Spawn confiramagtion dialog, the following code is bugged on MacOs,
            #       the settings dialog is re-shown at shutdown when ballon is shown...
            # input = dialog_question(_("Settings validation"), msg, button1=yes, button2=no)
            if True: #if input == yes:
                cp = ConfigParser()
                cp.read(conf.conf_file)
                need_reboot = False
                for setting in self.registred_selections.keys():
                    need_reboot |= self.registred_selections[setting].get("reboot", False)
                    cp.set(self.registred_selections[setting]['sectid'], 
                           self.registred_selections[setting]['confid'].upper(),
                           self.file_writable(self.registred_selections[setting]['value']))
                if (not self.no_reboot) and need_reboot:
                    dialog_info(title=_("Restart required"),
                                msg=_("You need to restart U.F.O for this changes to be applied"))
                cp.write(open(conf.conf_file, "w"))
                conf.reload()

        self.setVisible(False)
        self.close()
        self.accept()
        
    def on_cancel(self):
        if len(self.registred_selections) > 0:
            yes = _("Yes")
            no  = _("No")
            msg = _("Would you cancel the following changes ?") + "\n\n"
            msg += self.get_changes_string()
            # input = dialog_question(_("Cancel changes"), msg, button1=yes, button2=no)
            if True: #if input == yes:
                self.setVisible(False)
                self.close() 
                self.reject()
        else:
            self.setVisible(False)
            self.close()
            self.reject()
            
    def on_default(self):
        yes = _("Yes")
        no  = _("No")
        msg = _("Would you reset all settings to default ?")
        # input = dialog_question(_("Return to default"), msg, button1=yes, button2=no)
        if True: # if input == yes:
            cp = ConfigParser()
            cp.read(conf.conf_file)
            for tab in conf.settings:
                for setting in tab['settings']:
                    if setting.has_key('group'):
                        items = setting['group']
                    else:
                        items = [ setting ]
                    for item in items:
                        cp.remove_option(item['sectid'], item['confid'])
            cp.write(open(conf.conf_file, "w"))
            conf.reload()
            self.setVisible(False)
            self.close()
            self.accept()
    
    def get_conf(self, name_id):
        name_id = name_id.upper()
        return eval("conf." + name_id)
        
    def user_readable(self, value):
        if type(value) == bool:
            if value:
                return _("Activated")
            else:
                return _("Disabled")
        elif (type(value) == int and value == conf.AUTO_INTEGER) or \
              type(value) == str and value == conf.AUTO_STRING:
            return "auto"
        else:
            return value
        
    def file_writable(self, value):
        if type(value) == bool:
            return int(value)
        return value
        
    def get_changes_string(self):
        msg = ""
        for sel in self.registred_selections.keys():
            if self.registred_selections[sel]['value'] != self.get_conf(self.registred_selections[sel]['confid']):
                msg += "    - " + self.registred_selections[sel]['short'] + \
                       " :\t"   + unicode(self.user_readable(self.get_conf(sel))) + \
                       " -> "   + unicode(self.user_readable(self.registred_selections[sel]['value'])) + "\n"
        return msg

    def register_custom_handler(self, confid, layout, function=None):
        self.custom_handlers.update({ confid : { 'layout'   : layout, 'function' : function }})
    
    def on_balloon_color_selection(self, color):
        control = self.sender()
        self.balloon_preview.colors[control.conf_infos['confid']] = color
        self.balloon_preview.repaint()
    
    def create_balloon_custom_layout(self):
        custom_layout = QtGui.QVBoxLayout()
        val_layout = QtGui.QHBoxLayout()
        val_layout.addSpacing(30)

        self.balloon_preview = BalloonMessage(title=_("Message title"),
                                              fake= True,
                                              msg=_("Message contents"))
        val_layout.addWidget(self.balloon_preview)
        val_layout.addSpacing(30)
        custom_layout.addSpacing(15)
        custom_layout.addLayout(val_layout)
        
        return custom_layout

    def create_debug_custom_layout(self):
        def send_debug_reports():
            control = self.sender()
            control.setEnabled(False)
            import urllib
            report_files = glob.glob(os.path.join(os.path.dirname(conf.LOGFILE ), "*"))

            if conf.USER: user = conf.USER
            else: user = "None"
            reports = "REPORT SENDED MANUALLY BY USER (" + user + ")"
            for file in report_files:
                reports += "\n" + ("_" * len(file)) + "\n" + file + "\n\n"
                reports += open(file, 'r').read()
            params = urllib.urlencode({'report': reports})
            try:
                urllib.urlopen(conf.REPORTURL, params)
            except:
                pass

        custom_layout = QtGui.QHBoxLayout()
        custom_layout.addSpacing(30)
        send_button = QtGui.QPushButton(_("Send debug reports"))
        self.connect(send_button, QtCore.SIGNAL('clicked()'), send_debug_reports)
        custom_layout.addWidget(send_button)
        custom_layout.addSpacing(30)

        return custom_layout

# Globals

def extract_tar(tgz, dest, title=_("Installing"), msg=_("Please wait")):
    extract_win = ExtractWindow(tgz=tgz, dest=dest, title=title, msg=msg)
    return extract_win.exec_() == QtGui.QDialog.Accepted

def download_file(url, filename, title = _("Downloading"),
                  msg = _("Please wait"),
                  success_msg = _("Download completed"),
                  autostart=False, autoclose=False, parent=None):
    downloadWin = DownloadWindow(parent=parent, url=url, filename=filename, title=title, msg=msg,
                                 autostart=autostart, autoclose=autoclose, success_msg=success_msg, embedded_progress=True)
    if not autostart:
        downloadWin.show()
        return downloadWin.exec_() != QtGui.QDialog.Accepted
    else:
        ret = downloadWin.exec_()
        if downloadWin.was_canceled():
            return 1
        return ret != QtGui.QDialog.Accepted

def wait_command(cmd, title=_("Please wait"), msg=_("Operation in progress"),
                 success_msg=_("Operation successfully completed"), error_msg=("An error has occurred")):
    cmd_window = WaitWindow(cmd, title, msg, success_msg, error_msg)
    return cmd_window.exec_() == QtGui.QDialog.Accepted

def create_message_box(title, msg, width=200, height=100, buttons=QtGui.QMessageBox.Ok):
    darwin = sys.platform == "darwin"
    msgbox = OurMessageBox(main)
    msgbox.setText(msg)
    msgbox.setWindowTitle(title)
    if False: # darwin:
        msgbox.set_minimum_size(width, height)
        msgbox.setGeometry((screenRect.width() - width) / 2,
                           (screenRect.height() - height) / 2,
                           width, height)

    msgbox.setSizeGripEnabled(True)
    msgbox.setStandardButtons(buttons)
    return msgbox

def dialog_info(title, msg, error=False):
    msgbox = create_message_box(title=title, msg=msg)
    if error:
        msgbox.setIcon(QtGui.QMessageBox.Critical)
    else:
        msgbox.setIcon(QtGui.QMessageBox.Information)
    msgbox.exec_()

def dialog_question(title, msg, button1=_("Yes"), button2=_("No"), dangerous=False):
    msgbox = create_message_box(title=title, msg=msg, buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, width=500)
    if dangerous:
        icon = QtGui.QMessageBox.Warning
    else:
        icon = QtGui.QMessageBox.Question
    msgbox.setIcon(icon)
    reply = msgbox.exec_()
    if reply == QtGui.QMessageBox.Yes: return button1
    else: return button2

def dialog_error_report(title, msg, action=None, details=None, error=True):
    msgbox = OurMessageBox(main)
    msgbox.setIcon(QtGui.QMessageBox.Question)
    msgbox.setText(msg)
    msgbox.setWindowTitle(title)
    if error:
        msgbox.setIcon(QtGui.QMessageBox.Critical)
        msgbox.addButton(QtGui.QMessageBox.Ok)
    else:
        msgbox.setIcon(QtGui.QMessageBox.Question)
        msgbox.addButton(QtGui.QMessageBox.Cancel)
        
    if action:
        sendButton = msgbox.addButton(action, QtGui.QMessageBox.AcceptRole)

    if details:
        msgbox.setDetailedText(details)

    msgbox.exec_()
    if action and msgbox.clickedButton() == sendButton:
        return 1

    return 0

def dialog_password(msg=None, remember=False):
    w = QtGui.QWidget()
    if not msg:
        msg = _("Please enter the password for user ") + os.environ["USER"]

    dlg = QtGui.QInputDialog(w)
    dlg.setLabelText(msg)
    dlg.setWindowTitle(_("Password required"))
    dlg.setTextEchoMode(QtGui.QLineEdit.Password)
    if remember:
        check = QtGui.QCheckBox(_("Remember my password"))
        dlg.show()
        dlg.layout().addWidget(check)
    retcode = dlg.exec_()
    value = None
    if retcode:
        value = dlg.textValue()
    if remember: return value, check.isChecked()
    else: return value

def dialog_choices(title, msg, column, choices):
    dlg = ListDialog(title=title, msg=msg, choices=choices)
    dlg.exec_()
    return dlg.choicelist.currentRow()

def create_app(vbox):
    global app
    app = QtUFOGui(vbox)

def destroy_app(app):
    app.exit()
    app = None

app = QtUFOGui()
desktop = QtGui.QApplication.desktop()
screenRect = desktop.screenGeometry(desktop.primaryScreen())
main = QtGui.QMainWindow(desktop)
main.resize(screenRect.width(), screenRect.height())

if sys.platform == "darwin":
    QtGui.qt_mac_set_dock_menu(app.menu)
