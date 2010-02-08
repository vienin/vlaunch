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
from urllib import urlretrieve
from ConfigParser import ConfigParser
import time, utils
import conf
import logging
import glob
import math

class QtUFOGui(QtGui.QApplication):
        
    def __init__(self):
        QtGui.QApplication.__init__(self, sys.argv)

        self.vbox            = None
        self.animation       = None
        self.tray            = None
        self.splash          = None
        self.usb_check_timer = None
        self.callbacks_timer = None
        self.console_window  = None
        self.console_winid   = 0
        
        self.menu = QtGui.QMenu()
        action_about = QtGui.QAction(QtGui.QIcon(os.path.join(conf.IMGDIR, "about.png")), 
                                     QtCore.QString(_("About")), self);
        action_about.setStatusTip(_("Get informations about UFO"))
        action_settings = QtGui.QAction(QtGui.QIcon(os.path.join(conf.IMGDIR, "settings.png")), 
                                        QtCore.QString(_("Settings...")), self);
        action_settings.setStatusTip(_("Configure the UFO launcher"))
        
        self.menu.addAction(action_about)
        self.menu.addAction(action_settings)
        self.connect(action_about, QtCore.SIGNAL("triggered()"), self.about)
        self.connect(action_settings, QtCore.SIGNAL("triggered()"), self.settings)
        
        self.setWindowIcon(QtGui.QIcon(os.path.join(conf.IMGDIR, "UFO.png")))
    
    def event(self, event):
        if isinstance(event, SetTrayIconEvent):
            self.tray = TrayIcon()
            if sys.platform != "darwin":
                self.tray.setContextMenu(self.menu)

        elif isinstance(event, DownloadFinishedEvent):
            event.callback(event.error)

        elif isinstance(event, CreateSplashEvent):
            self._create_splash_screen()

        elif isinstance(event, DestroySplashEvent):
            self._destroy_splash_screen()

        elif isinstance(event, CommandEvent):
            event.callback(event.error)
            
        elif isinstance(event, UpdateEvent):
            event.callback()
            
        elif isinstance(event, ProgressEvent):
            event.value = int(event.value * 100)
            try:
                event.progress.setValue(int(event.value))
                if event.msg:
                    self.tray.authentication(event.msg)
            except: 
                # Underlying C++ object has been deleted error...
                pass
            
        elif isinstance(event, BalloonMessageEvent):
            if not event.show:
                self.tray.hide_balloon()
            elif event.progress:
                self.tray.show_progress(event.title, event.msg, event.timeout, 
                                        credentials_cb=event.credentials_cb, credentials=event.credentials)
            else:
                self.tray.show_message(event.title, event.msg, event.timeout)
                
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
                    
        elif isinstance(event, TimerEvent):
            if event.stop:
                event.timer.stop()
                del event.timer
                event.timer = None
            else:
                if not event.timer:
                    event.timer = QtCore.QTimer(self)
                    self.connect(event.timer, QtCore.SIGNAL("timeout()"), event.function)
                    event.timer.start(event.time * 1000)
            
        else:
            return False

        return True
    
    def initialize(self, vbox):
        self.vbox = vbox
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
        
    def start_usb_check_timer(self, time, function):
        self.postEvent(self, TimerEvent(self.usb_check_timer,
                                        time, 
                                        function))
        
    def stop_usb_check_timer(self):
        self.postEvent(self, TimerEvent(self.usb_check_timer,
                                        time=None, 
                                        function=None, 
                                        stop=True))
    
    def start_callbacks_timer(self, time, function):
        self.postEvent(self, TimerEvent(self.callbacks_timer,
                                        time, 
                                        function))
        
    def stop_callbacks_timer(self):
        self.postEvent(self, TimerEvent(self.callbacks_timer,
                                        time=None, 
                                        function=None, 
                                        stop=True))

    def update_progress(self, progress, value):
        if progress:
            self.postEvent(self, ProgressEvent(progress, 
                                               float(value), 
                                               100))
            
    def authentication(self, msg):
        if self.tray.progress:
            self.postEvent(self, ProgressEvent(self.tray.progress, 
                                               100, 
                                               100,
                                               msg))

    def show_balloon_message(self, title, msg, timeout=0):
        self.postEvent(self, 
                       BalloonMessageEvent(title, 
                                           msg, 
                                           timeout))
        
    def show_balloon_progress(self, title, msg, credentials_cb=None, credentials=False):
        self.postEvent(self, 
                       BalloonMessageEvent(title, 
                                           msg, 
                                           timeout=0, 
                                           progress=True,
                                           credentials_cb=credentials_cb,
                                           credentials=credentials))
        
    def hide_balloon(self):
        self.postEvent(self, 
                       BalloonMessageEvent(title=None, 
                                           msg=None, 
                                           timeout=0, 
                                           progress=None, 
                                           show=False))
        
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
                                               _("For more information, please visit") + " http://ufo.agorabox.org"))
    
    def settings(self):
        self.settings = Settings()
        self.settings.show()
        self.settings.exec_()
        del self.settings

class NoneEvent(QtCore.QEvent):
    def __init__(self, size, total):
        super(NoneEvent, self).__init__(QtCore.QEvent.None)
        self.size = size
        self.total = total

class SetTrayIconEvent(QtCore.QEvent):
    def __init__(self):
        super(SetTrayIconEvent, self).__init__(QtCore.QEvent.None)

class CreateSplashEvent(QtCore.QEvent):
    def __init__(self):
        super(CreateSplashEvent, self).__init__(QtCore.QEvent.None)

class DestroySplashEvent(QtCore.QEvent):
    def __init__(self):
        super(DestroySplashEvent, self).__init__(QtCore.QEvent.None)

class ProgressEvent(QtCore.QEvent):
    def __init__(self, progress, value, total, msg=None):
        super(ProgressEvent, self).__init__(QtCore.QEvent.None)
        self.progress = progress
        self.value    = value
        self.total    = total
        self.msg      = msg

class BalloonMessageEvent(QtCore.QEvent):
    def __init__(self, title, msg, timeout, progress=False, show=True, credentials_cb=None, credentials=False):
        super(BalloonMessageEvent, self).__init__(QtCore.QEvent.None)
        self.show     = show
        self.title    = title
        self.msg      = msg
        self.timeout  = timeout
        self.progress = progress
        self.credentials_cb = credentials_cb
        self.credentials  = credentials

class TimerEvent(QtCore.QEvent):
    def __init__(self, timer, time, function, stop=False):
        super(TimerEvent, self).__init__(QtCore.QEvent.None)
        self.timer    = timer
        self.time     = time
        self.function = function
        self.stop     = stop

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

class DownloadFinishedEvent(QtCore.QEvent):
    def __init__(self, callback, error=False):
        super(DownloadFinishedEvent, self).__init__(QtCore.QEvent.None)
        self.callback = callback
        self.error = error

class CommandEvent(QtCore.QEvent):
    def __init__(self, callback, error=False):
        super(CommandEvent, self).__init__(QtCore.QEvent.None)
        self.callback = callback
        self.error = error

class UpdateEvent(QtCore.QEvent):
    def __init__(self, callback):
        super(UpdateEvent, self).__init__(QtCore.QEvent.None)
        self.callback = callback


# Gere le téléchargement dans un thread a part.
# Envoie Deux type d'evenement à l'application :
#   1. NoneEvent pour chaque mise a jour de la progression du téléchargemetn
#   2. FinishedEvent quand il termine(sur une erreur ou non)
# ATTENTION: pour chaque appel de stop par le thread principale il faut recréer l'objet downloader
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
            filename, headers = urlretrieve(self.file, self.dest, reporthook=self.on_progress)
        except:
            app.postEvent(app, DownloadFinishedEvent(self.finished_callback, True))
        else:
            app.postEvent(app, DownloadFinishedEvent(self.finished_callback, False))
        sys.exit()

    def on_progress(self, count, blockSize, totalSize):
        if not self.progress: return
        if self.to_be_stopped == True:
            sys.exit()
        self.count = count
        self.maximum = totalSize
        self.downloaded = float(blockSize*count)/totalSize
        app.update_progress(self.progress, self.downloaded)

    def stop(self):
        self.to_be_stopped = True


class CommandLauncher(threading.Thread):
    def __init__(self, cmd, callback): 
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.callback = callback

    def update(self):
        app.postEvent(app, UpdateEvent(self.update))
            
    def run(self):
        t = utils.call(self.cmd, spawn=True)
        while t.poll() == None:
            self.update()
            time.sleep(1)
        app.postEvent(app, CommandEvent(self.callback, False))
        sys.exit()
    

class WaitWindow(QtGui.QDialog):
    def __init__(self,  cmd, title, msg, success_msg, error_msg, parent=None):
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
        self.connect(self.cancelButton, QtCore.SIGNAL("canceled()"), self.cancel_command)
        self.cancelButton.hide()
        topLayout = QtGui.QHBoxLayout()
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(topLayout) 
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(buttonBox)
        mainLayout.addWidget(self.animation)
        self.setLayout(mainLayout)
        self.animated = QtGui.QMovie(os.path.join(conf.IMGDIR, "animated-bar.mng"), QtCore.QByteArray(), self.animation)
        self.animated.setCacheMode(QtGui.QMovie.CacheAll)
        self.animated.setSpeed(100)
        self.animation.setMovie(self.animated)

    def cancel_command(self):
        pass 

    def finished(self, error):
        if error:
            self.statusLabel.setText(self.error_msg)
        else:
            self.statusLabel.setText(self.success_msg)
        self.close()

    def run(self):
        self.animated.start()
        self.show()
        self.command.start()
        return self.exec_()


class DownloadWindow(QtGui.QDialog):
    def __init__(self, url, filename, title, msg, autostart,
                 success_msg, autoclose=False, embedded_progress=True):
        super(DownloadWindow, self).__init__(main)
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
        # On se connecte au Slot Qt pointant sur les evenement C++, sender, SIGNAL, callable
        self.connect(self.downloadButton, QtCore.SIGNAL("clicked()"), self.download_file)
        self.connect(self.actionButton, QtCore.SIGNAL("clicked()"), self.action)
        topLayout = QtGui.QHBoxLayout()
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(topLayout) 
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
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
        self.downloader = Downloader(self.url, self.fileName, progress=progress, finished_callback=self.http_request_finished)

    def was_canceled(self):
        return self.http_request_aborted
        
    def download_file(self):
        self.http_request_aborted = False
        if self.finished:
            self.accept()
        fileName = self.fileName
        self.outFile = QtCore.QFile(fileName)
        if not self.outFile.open(QtCore.QIODevice.WriteOnly):
            QtGui.QMessageBox.information(self, _("Error"),
                    _("Could not write to file %s: %s.") % (fileName, self.outFile.errorString()))
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
            QtGui.QMessageBox.information(self, _("Error"),
                                          _("Download has failed. Please check your Internet connection"))
        else:
            self.finished = True
            # On cache les boutons
            self.downloadButton.hide()
            self.actionButton.setText(_("Continue"))
            self.statusLabel.setText(self.success_msg)
            self.hide_progress()

        if self.autoclose:
            self.accept()
            
        self.downloadButton.setEnabled(True)
        self.outFile = None


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


class TrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self):
        QtGui.QSystemTrayIcon.__init__(self)
        
        self.setIcon(QtGui.QApplication.windowIcon())
        self.setVisible(True)
        
        self.connect(self, QtCore.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.activate)
        self.progress  = None
        self.balloon   = None
        self.minimized = False

        self.show()

    def show_message(self, title, msg, timeout=0):
        self.balloon = BalloonMessage(self, icon = os.path.join(conf.IMGDIR, "UFO.png"),
                                      title=title, msg=msg, timeout=timeout)

    def show_progress(self, title, msg, timeout=0, no_text=False, invert=False, credentials_cb=None, credentials=False):
        self.balloon = BalloonMessage(self, icon = os.path.join(conf.IMGDIR, "UFO.png"),
                                     title=title, msg=msg, progress=True, timeout=timeout, 
                                     credentials_cb=credentials_cb, credentials=credentials)
        self.progress = self.balloon.progressBar        
        if no_text:
            self.progress.setTextVisible(False)
        if invert:
            self.progress.setInvertedAppearance(True)

    def hide_balloon(self):
        if self.balloon:
            self.balloon.close()
            del self.balloon
            self.balloon = None
        self.progress = None

    def authentication(self, msg):
        if self.balloon:
            self.balloon.authentication(msg)
        
    def activate(self, reason):
        if reason == QtGui.QSystemTrayIcon.DoubleClick:
            if self.minimized:
                app.normalize_window()
                self.minimized = False
            else:
                app.minimize_window()
                self.minimized = True
        elif reason != QtGui.QSystemTrayIcon.Context:
            if self.balloon:
                self.balloon.show()
        

class BalloonMessage(QtGui.QWidget):
    def __init__(self, parent, title, msg, icon=None, timeout=0, 
                 progress=False, credentials_cb=None, credentials=None, fake=False):
        
        if sys.platform == "win32":
            flags = QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.ToolTip
        elif sys.platform == "linux2":
            flags = QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.X11BypassWindowManagerHint | QtCore.Qt.Popup
        else:
            flags = QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup
        
        QtGui.QWidget.__init__(self, None, flags)

        self.parent = parent
        self.title = title
        self.msg = msg
        self.fake = fake
        self.mAnchor = QtCore.QPoint()
        self.up = True
        self.login_shown = False
        self.credentials_cb = credentials_cb
        self.credentials = credentials
        self.colors = { 'ballooncolor'         : conf.BALLOONCOLOR, 
                        'ballooncolorgradient' : conf.BALLOONCOLORGRADIENT, 
                        'ballooncolortext'     : conf.BALLOONCOLORTEXT }
        
        self.BalloonLayout = QtGui.QHBoxLayout(self)

        self.Layout2 = QtGui.QVBoxLayout()
        self.title_layout = QtGui.QHBoxLayout()
        self.close_button = QtGui.QPushButton(QtGui.QIcon(os.path.join(conf.IMGDIR, "close.png")), "", self)
        self.close_button.setFlat(True)
        if fake:
            self.close_button.setDisabled(True)
        else:
            self.connect(self.close_button, QtCore.SIGNAL("clicked()"), self.hide)
        
        self.mTitle = QtGui.QLabel("<b><font color=" + self.colors['ballooncolortext'] + ">" + self.title + "</font></b>")
        self.mTitle.setPalette(QtGui.QToolTip.palette())
        self.mTitle.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.title_layout.addWidget(self.mTitle)
        if fake:
            self.title_layout.addSpacing(100)
        self.title_layout.addWidget(self.close_button, 0, QtCore.Qt.AlignRight)
        
        self.mCaption = QtGui.QLabel("<font color=" + self.colors['ballooncolortext'] + ">" + msg + "</font>")
        self.mCaption.setPalette(QtGui.QToolTip.palette())
        self.mCaption.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        if icon:
            pixmap = QtGui.QIcon(icon).pixmap(64, 64)
            mImage = QtGui.QLabel(self)
            mImage.setScaledContents(False);
            mImage.setPixmap(pixmap)
            self.BalloonLayout.addWidget(mImage, 0, QtCore.Qt.AlignTop)

        self.Layout2.addLayout(self.title_layout)
        self.Layout2.addWidget(self.mCaption)
        
        self.BalloonLayout.addLayout(self.Layout2)

        if progress:
            self.progressBar = QtGui.QProgressBar()
            self.Layout2.addWidget(self.progressBar)

        if credentials_cb and conf.USER != "":
            self.creds_layout = QtGui.QVBoxLayout()
            msg = "(" + conf.USER + ") - "
            if credentials:
                msg += _("You already are authenticated")
            else:
                msg += _("Authenticate")
            self.credentials_button = QtGui.QPushButton(QtGui.QIcon(os.path.join(conf.IMGDIR, "credentials.png")), msg, self)
            self.credentials_button.setFlat(True)
            self.credentials_button.setDefault(True)
            self.connect(self.credentials_button, QtCore.SIGNAL("clicked()"), self.show_login)
            self.creds_layout.addWidget(self.credentials_button, 0, QtCore.Qt.AlignLeft)
            self.Layout2.addLayout(self.creds_layout)

        self.setAutoFillBackground(True)
        self.currentAlpha = 0
        self.setWindowOpacity(0.0)
        self.resize(350, 80)
    
        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)
        self.timer.start(1)

        if timeout and not fake:
            self.destroytimer = QtCore.QTimer(self)
            self.connect(self.destroytimer, QtCore.SIGNAL("timeout()"), self.destroy)
            self.destroytimer.start(timeout)

        self.show()
        
    def show_login(self):
        if self.login_shown:
            self.hide_login()
            return
        else:
            self.login_shown = True

        self.hline = QtGui.QFrame(self)
        self.hline.setFrameShape(QtGui.QFrame.HLine)
        self.hline.setFrameShadow(QtGui.QFrame.Sunken)
        self.creds_layout.addWidget(self.hline)
        self.creds_hbox = QtGui.QHBoxLayout()
        self.pass_label = QtGui.QLabel(_("UFO password:"))
        self.creds_hbox.addWidget(self.pass_label)
        self.password = QtGui.QLineEdit(self)
        self.password.setEchoMode(QtGui.QLineEdit.Password)
        self.connect(self.password, QtCore.SIGNAL("returnPressed()"), self.return_pressed)
        self.creds_hbox.addWidget(self.password, 100)
        self.ok_button = QtGui.QPushButton("Ok", self)
        self.connect(self.ok_button, QtCore.SIGNAL("clicked()"), self.return_pressed)
        self.ok_button.setMaximumSize(32, 28)
        self.creds_hbox.addWidget(self.ok_button)
        self.creds_layout.addLayout(self.creds_hbox)
        self.remember = QtGui.QCheckBox(_("Remember my password"))
        if self.credentials != None:
            self.creds_layout.addWidget(self.remember)

    def hide_login(self):
        self.login_shown = False
        for control in [ self.pass_label, self.password, self.ok_button, self.remember, self.hline ]:
            control.hide()
        if self.credentials != None:
            self.creds_layout.removeWidget(self.remember)
        self.creds_hbox.removeWidget(self.password)
        self.creds_hbox.removeWidget(self.ok_button)
        self.creds_hbox.removeWidget(self.pass_label)
        self.creds_hbox.removeWidget(self.hline)
        self.close_button.clearFocus()
        self.layout().activate()
        self.resize(350, 20)
        self.show()
    
    def authentication(self, msg):
        self.mCaption.setText(msg)

    def destroy(self):
        self.hide()
        self.close()

    def return_pressed(self):
        if self.password.text():
            self.credentials_cb(self.password.text(), self.remember.isChecked())
            if len(self.credentials_button.text()) - len(conf.USER) - 10 > len(_("Authenticate")):
                offset = "                                          "
            else:
                offset = "                       "
            self.credentials_button.setText(QtCore.QString("(" + conf.USER + ")" + offset))
        self.hide_login()

    def timeout(self):
        if self.currentAlpha <= 255:
            self.currentAlpha += 15
            self.timer.start(1)
        self.setWindowOpacity(1. / 255. * self.currentAlpha)

    def resizeEvent(self, evt):
        if self.fake:
            return
        deskRect = QtCore.QRect(desktop.availableGeometry())
        self.up = app.tray.geometry().y() < deskRect.height() / 2
        mask = self.draw()
        self.setMask(mask)
        if self.up:
            y = app.tray.geometry().bottom() + 10
        else:
            y = app.tray.geometry().top() - self.height() - 10
        self.move(deskRect.width() - self.width() - 10, y)

    def draw(self, paintEvent=False):
        mask = QtGui.QRegion()

        self.mTitle.setText("<b><font color=" + self.colors['ballooncolortext'] + ">" + self.title + "</font></b>")
        self.mCaption.setText("<font color=" + self.colors['ballooncolortext'] + ">" + self.msg + "</font>")
        
        path = QtGui.QPainterPath()
        if hasattr(path, "addRoundedRect"):
            path.addRoundedRect(QtCore.QRectF(0, 0, self.width(), self.height()), 7, 7)
        else:
            path.addRect(QtCore.QRectF(0, 0, self.width(), self.height()))

        if paintEvent:
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
        if not paintEvent:
            painter.end()
        return mask

    def paintEvent(self, evt):
        self.draw(paintEvent=True)
        
        
class Settings(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Settings, self).__init__(parent)

        self.registred_selections = {}
        self.custom_handlers      = {}
        self.groups               = {}
        
        "Registering custom handlers and layouts"
        
        self.register_custom_handler('ballooncolors',
                                     self.create_ballon_custom_layout(),
                                     self.on_balloon_color_selection)
        
        "Fill main dialog with configuration tabs"
        
        tabWidget = QtGui.QTabWidget()
        for tab in conf.settings:
            tabWidget.addTab(self.createOneTab(tab), 
                             QtGui.QIcon(os.path.join(conf.IMGDIR, tab['iconfile'])), 
                             self.tr(tab['tabname']))

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        
        "Build controls buttons"
        
        valid_layout   = QtGui.QHBoxLayout()
        ok_button      = QtGui.QPushButton(self.tr(_("Ok")))
        cancel_button  = QtGui.QPushButton(self.tr(_("Cancel")))
        default_button = QtGui.QPushButton(self.tr(_("Defaults")))
        
        ok_button.clicked.connect(self.on_validation)
        cancel_button.clicked.connect(self.on_cancel)
        default_button.clicked.connect(self.on_default)
        
        valid_layout.addWidget(default_button)
        valid_layout.addWidget(ok_button)
        valid_layout.addWidget(cancel_button)
        mainLayout.addLayout(valid_layout)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr(_("UFO settings")))
        
    def createOneTab(self, tab):
        widget     = QtGui.QWidget()
        tab_layout = QtGui.QVBoxLayout()
        
        for setting in tab['settings']:
            set_layout = QtGui.QVBoxLayout()
            set_layout.addWidget(QtGui.QLabel(self.tr(setting['label'])))
            
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
                    
                    "Here build an exclusive radio button group, and associate"
                    "one combo box list for each radio button of the group"
                    
                    group      = QtGui.QButtonGroup()
                    val_layout = QtGui.QHBoxLayout()
                    col_tab    = {}
                    for col in item['values'].keys():
                        col_layout = QtGui.QVBoxLayout()
                        radio      = QtGui.QRadioButton(self.tr(col))
                        group.addButton(radio)
                        col_layout.addWidget(radio)
                        
                        values = QtGui.QComboBox()
                        for val in item['values'][col]:
                            values.addItem(val)
                            
                        col_tab.update({ radio : values })
                        
                        "Connect items to action slot"
                        
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
                        
                    set_layout.addLayout(val_layout)
                    group.setExclusive(True)
                    for radio in col_tab.keys():
                        for combo in col_tab.values():
                            if col_tab[radio] != combo:
                                radio.toggled.connect(combo.setDisabled)
                        
                        "Set current value"
                        
                        if self.get_conf(item['confid']) in item['values'][str(radio.text())]:
                            radio.setChecked(QtCore.Qt.Checked)
                            index = item['values'][str(radio.text())].index(self.get_conf(item['confid']))
                            col_tab[radio].setCurrentIndex(index)
                        
                elif type(item.get('values')) == list:
                    
                    "Here build a combo box list with list values"
                    
                    values = QtGui.QComboBox()
                    for val in item['values']:
                        values.addItem(val)
                    
                    "Connect items to action slot"
                    
                    values.conf_infos = item
                    values.connect(values, 
                                   QtCore.SIGNAL("activated(const QString &)"), 
                                   self.on_selection)
                    if custom and custom['function']:
                        values.connect(values, 
                                       QtCore.SIGNAL("activated(const QString &)"), 
                                       custom['function'])
                        
                    "Set current value"
                    
                    values.setCurrentIndex(item['values'].index(self.get_conf(item['confid'])))
                    
                    set_layout.addWidget(values)
                    
                elif type(item.get('range')) == list:
                    
                    "Here build integer value edit with specific range"
                    
                    val_layout = QtGui.QHBoxLayout()
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
                    
                    "Set current value"
                    
                    current_value = self.get_conf(item['confid'])
                    if current_value != conf.AUTO_INTEGER:
                        spin.setValue(current_value)
                        
                    "Connect items to action slot"
                    
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
                        
                        "Set current value"
                        
                        if current_value == conf.AUTO_INTEGER:
                            checkbox.setChecked(QtCore.Qt.Checked)
                            
                        "Connect items to action slot"
                        
                        checkbox.toggled.connect(self.on_selection)
                        if custom and custom['function']:
                            checkbox.toggled.connect(custom['function'])
                        
                        val_layout.addWidget(checkbox)
                    
                    val_layout.addWidget(spin)
                    val_layout.addWidget(slider)
                    set_layout.addLayout(val_layout)
                    
                else:
                    
                    "Here build value edit item corresponding to variable type"
                    
                    current_value = self.get_conf(item['confid'])
                    
                    val_layout = QtGui.QHBoxLayout()
                    if type(current_value) == bool:
                        edit   = QtGui.QCheckBox(self.tr(item['short']))
                        signal = edit.toggled
                        funct  = self.on_selection

                        "Set current value"
                        
                        if current_value:
                            edit.setChecked(QtCore.Qt.Checked)
                            
                    elif type(current_value) == str:
                        if current_value[0] == '#':
                            
                            "Set current value"
                            
                            edit = QtGui.QPushButton()
                            edit.buttonforcolor = True
                            edit.setAutoFillBackground(True);
                            edit.setStyleSheet("background-color: " + current_value)
                            edit.setMaximumWidth(40)
                            edit.setMaximumHeight(20)
                            signal = edit.clicked
                            funct  = self.on_color_selection
                            
                            "We will call possible custom function in"
                            "the color_selection handler"
                            
                            if custom and custom['function']:
                                custom = custom.copy()
                                custom['function'] = None
                                
                            val_layout.addWidget(QtGui.QLabel(self.tr(item['short'] + ":")))
                        
                        else:
                            
                            "Set current value"
                            
                            edit   = QtGui.QLineEdit(current_value)
                            signal = edit.textChanged
                            funct  = self.on_selection
                            
                    else:
                        raise Exception("Base type not yet supported")
                        
                    if item.get('autocb') == True:
                        checkbox = QtGui.QCheckBox(self.tr(_("Auto")))
                        
                        "Connect items to action slot"
                        
                        checkbox.conf_infos = item
                        checkbox.toggled.connect(self.on_selection)
                        checkbox.toggled.connect(edit.setDisabled)
                        if custom and custom['function']:
                            checkbox.toggled.connect(custom['function'])
                            
                        val_layout.addWidget(checkbox)
                        
                    "Connect items to action slot"
                        
                    edit.conf_infos = item
                    signal.connect(funct)
                    if custom and custom['function']:
                        signal.connect(custom['function'])
                    
                    val_layout.addWidget(edit)
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
            yes = _("Yes")
            no  = _("No")
            msg = _("Would you validate the following changes ?") + "\n\n"
            msg += self.get_changes_string()
            # TODO: Spawn confiramagtion dialog, the following code is bugged on MacOs,
            #       the settings dialog is re-shown at shutdown when ballon is shown...
            # input = dialog_question(_("Settings validation"), msg, button1=yes, button2=no)
            if True: #if input == yes:
                cp = ConfigParser()
                cp.read(conf.conf_file)
                for setting in self.registred_selections.keys():
                    cp.set(self.registred_selections[setting]['sectid'], 
                           self.registred_selections[setting]['confid'].upper(),
                           self.file_writable(self.registred_selections[setting]['value']))
                cp.write(open(conf.conf_file, "w"))
                reload(conf)
                self.setVisible(False)
                self.close()
                self.accept()

        self.setVisible(False)
        self.close()
        self.reject()
        
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
            reload(conf)
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
                       " :\t"    + str(self.user_readable(self.get_conf(sel))) + \
                       " -> "   + str(self.user_readable(self.registred_selections[sel]['value'])) + "\n"
        return msg

    def register_custom_handler(self, confid, layout, function):
        self.custom_handlers.update({ confid : { 'layout'   : layout, 'function' : function }})
    
    def on_balloon_color_selection(self, color):
        control = self.sender()
        self.balloon_preview.colors[control.conf_infos['confid']] = color
        self.balloon_preview.repaint()
    
    def create_ballon_custom_layout(self):
        custom_layout = QtGui.QVBoxLayout()
        self.balloon_preview = BalloonMessage(self, 
                                              fake  = True, 
                                              icon  = os.path.join(conf.IMGDIR, "UFO.png"),
                                              title =_("Message title"), 
                                              msg   = _("Message contents"))
        custom_layout.addSpacing(15)
        custom_layout.addWidget(self.balloon_preview)
        
        return custom_layout
        
# Globals

def download_file(url, filename, title = _("Downloading"),
                  msg = _("Please wait"),
                  success_msg = _("Download completed"), autostart=False, autoclose=False):
    downloadWin = DownloadWindow(url=url, filename=filename, title=title, msg=msg,
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
    cmdWin = WaitWindow(cmd, title, msg, success_msg, error_msg)
    cmdWin.run()

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

def dialog_question(title, msg, button1=_("Yes"), button2=_("No")):
    msgbox = create_message_box(title=title, msg=msg, buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, width=500)
    msgbox.setIcon(QtGui.QMessageBox.Question)
    reply = msgbox.exec_()
    if reply == QtGui.QMessageBox.Yes: return button1
    else: return button2

def dialog_error_report(title, msg, action=None, details=None):
    msgbox = OurMessageBox(main)
    msgbox.setIcon(QtGui.QMessageBox.Question)
    msgbox.setText(msg)
    msgbox.setWindowTitle(title)
    msgbox.addButton(QtGui.QMessageBox.Ok)
    msgbox.setIcon(QtGui.QMessageBox.Critical)
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
