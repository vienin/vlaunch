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


from PyQt4 import QtGui, QtCore
import threading, sys, os
from urllib import urlretrieve
import time, utils
import subprocess
import conf
import logging
import glob

class QtUFOGui(QtGui.QApplication):
        
    def __init__(self, argv):
        QtGui.QApplication.__init__(self, argv)

        self.animation       = None
        self.tray            = None
        self.splash          = None
        self.usb_check_timer = None
        self.callbacks_timer = None
        self.console_window  = None
        self.console_winid   = 0

        self.setWindowIcon(QtGui.QIcon(os.path.join(conf.IMGDIR, "UFO.png")))

    def event(self, event):
        if isinstance(event, SetTrayIconEvent):
            self.tray = TrayIcon()

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
                self.tray.show_progress(event.title, event.msg, event.timeout, credentials=event.credentials, keyring=event.keyring)
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
                
                if event.type == ConsoleWindowEvent.defs.get('ShowFullscreen'):
                    self.console_window.showMaximized()
                elif event.type == ConsoleWindowEvent.defs.get('ToggleFullscreen'):
                    if self.console_window.isFullscreen() or self.console_window.isMaximized():
                        self.console_window.showNormal()
                    else:
                        self.console_window.showMinimized()
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

    def initialize_tray_icon(self):
        self.postEvent(self, SetTrayIconEvent())
        
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
        
    def show_balloon_progress(self, title, msg, credentials=None, keyring=False):
        self.postEvent(self, 
                       BalloonMessageEvent(title, 
                                           msg, 
                                           timeout=0, 
                                           progress=True,
                                           credentials=credentials,
                                           keyring=keyring))
        
    def hide_balloon(self):
        self.postEvent(self, 
                       BalloonMessageEvent(title=None, 
                                           msg=None, 
                                           timeout=0, 
                                           progress=None, 
                                           show=False))
        
    def set_tooltip(self, tip):
        self.postEvent(self, ToolTipEvent(tip))

    def fullscreen_window(self, winid, toggle):
        if toggle:
            type = 'ToggleFullscreen'
        else:
            type = 'ShowFullscreen'
            
        self.postEvent(self, 
                       ConsoleWindowEvent(winid, 
                                          ConsoleWindowEvent.defs.get(type)))
        
    def minimize_window(self, winid):
        self.postEvent(self, 
                       ConsoleWindowEvent(winid, 
                                          ConsoleWindowEvent.defs.get('ShowMinimized')))
        
    def process_gui_events(self):
        self.processEvents()

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
    def __init__(self, title, msg, timeout, progress=False, show=True, credentials=None, keyring=False):
        super(BalloonMessageEvent, self).__init__(QtCore.QEvent.None)
        self.show     = show
        self.title    = title
        self.msg      = msg
        self.timeout  = timeout
        self.progress = progress
        self.credentials = credentials
        self.keyring  = keyring

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
            'ShowFullscreen':1,
            'ToggleFullscreen':2}
    
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
    def __init__(self,  cmd="", title="", msg="", parent=None):
        super(WaitWindow, self).__init__(main)
        self.cmd = cmd
        self.setWindowTitle(title)
        self.command = CommandLauncher(self.cmd, self.finished)
        self.msg = msg
        self.statusLabel = QtGui.QLabel(self.msg)
        self.cancelButton = QtGui.QPushButton(u"Annuler")
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
            self.statusLabel.setText("Une erreur est survenue")
        else:
            self.statusLabel.setText(u"Installation terminée")
        self.close()

    def run(self):
        self.animated.start()
        self.show()
        self.command.start()
        return self.exec_()


class DownloadWindow(QtGui.QDialog):
    def __init__(self, url, filename, title, msg, parent=None, autostart=False, autoclose=False, embedded_progress=True):
        super(DownloadWindow, self).__init__(main)
        self.url = url
        self.fileName = filename
        self.autostart = autostart
        self.autoclose = autoclose
        self.outFile = None
        self.httpGetId = 0
        self.http_request_aborted = False
        self.finished = False
        self.statusLabel = QtGui.QLabel(msg)
        self.embedded_progress = embedded_progress
        self.progress_dialog = None
        self.progress_bar = None
        self.downloadButton = QtGui.QPushButton(u"Télécharger")
        self.downloadButton.setDefault(True)
        self.actionButton = QtGui.QPushButton(u"Quitter")
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

    def action(self):
        if self.embedded_progress:
            if self.downloading:
                self.cancel_download()
                self.progress_bar.hide()
                self.layout().removeWidget(self.progress_bar)
                self.progress_bar = None
                self.actionButton.setText(u"Quitter")
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
            QtGui.QMessageBox.information(self, "HTTP",
                    u"Impossible d'écrire dans le fichier %s: %s."%(fileName, self.outFile.errorString()))
            self.outFile = None
            return
        if self.embedded_progress:
            self.progress_bar = QtGui.QProgressBar(self)
            app.progress = self.progress_bar
            self.layout().insertWidget(self.layout().count() - 1, self.progress_bar)
            self.actionButton.setText("Annuler")
            self.connect(self.actionButton, QtCore.SIGNAL("clicked()"), self.cancel_download)
        else:
            self.progress_dialog = QtGui.QProgressDialog(self)
            app.progress = self.progress_dialog
            self.connect(self.progress_dialog, QtCore.SIGNAL("canceled()"), self.cancel_download)
            self.progress_dialog.setCancelButtonText(u"Annuler")
            self.progress_dialog.setWindowTitle(u"Téléchargement de l'image")
            self.progress_dialog.setLabelText(u"Téléchargement en cours : %s"%(fileName, ))
            self.progress_dialog.show()
            
        self.downloading = True
        self.downloadButton.setEnabled(False)
        # On prépare le thread qui gérera le téléchargement
        self.init_downloader()
        self.downloader.start()

    def cancel_download(self):
        self.statusLabel.setText(u"Téléchargement annulé. \n"
                                 u"Cliquer sur 'Télécharger' pour recommencer.")
        self.http_request_aborted = True
        self.downloading = False
        self.downloader.stop()
        self.downloadButton.setEnabled(True)

    def http_request_finished(self,  error):
        self.downlading = False
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
            QtGui.QMessageBox.information(self, "HTTP",
                    u"Le téléchargement a échoué. Vérifiez votre connexion Internet.")
        else:
            self.finished = True
            # On cache les boutons
            self.downloadButton.hide()
            self.actionButton.setText(u"Continuer")
            self.statusLabel.setText(u"Téléchargement terminé.")

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
        menu = QtGui.QMenu()
        self.setContextMenu(menu)
        self.connect(self, QtCore.SIGNAL("activate()"), self.activate)
        
        self.progress = None
        self.balloon  = None
        
        self.setToolTip(QtCore.QString(u"UFO: en cours de démarrage"))
        self.show()

    def show_message(self, title, msg, timeout=0):
        self.balloon = BalloonMessage(self, icon = os.path.join(conf.IMGDIR, "UFO.png"),
                                      title=title, msg=msg, timeout=timeout)

    def show_progress(self, title, msg, timeout=0, no_text=False, invert=False, credentials=None, keyring=False):
        self.balloon = BalloonMessage(self, icon = os.path.join(conf.IMGDIR, "UFO.png"),
                                     title=title, msg=msg, progress=True, timeout=timeout, 
                                     credentials=credentials, keyring=keyring)
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
        
    def activate(self):
        pass


class BalloonMessage(QtGui.QWidget):
    def __init__(self, parent, title, msg, icon=None, timeout=0, 
                 progress=False, credentials=None, keyring=False):
        
        if sys.platform == "win32":
            flags = QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup
        elif sys.platform == "linux2":
            flags = QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.X11BypassWindowManagerHint | QtCore.Qt.Popup
        else:
            flags = QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup
        
        QtGui.QWidget.__init__(self, None, flags)
        self.startTimer(500)

        self.parent = parent
        self.title = title
        self.mAnchor = QtCore.QPoint()
        self.up = True
        self.login_shown = False
        
        self.BalloonLayout = QtGui.QHBoxLayout(self)

        self.Layout2 = QtGui.QVBoxLayout()
        self.mTitle = QtGui.QLabel("<b>" + title + "</b>")
        self.mTitle.setPalette(QtGui.QToolTip.palette())
        self.mTitle.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        self.mCaption = QtGui.QLabel(msg)
        self.mCaption.setPalette(QtGui.QToolTip.palette())
        self.mCaption.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        if icon:
            pixmap = QtGui.QIcon(icon).pixmap(64, 64)
            mImage = QtGui.QLabel(self)
            mImage.setScaledContents(False);
            mImage.setPixmap(pixmap)
            self.BalloonLayout.addWidget(mImage, 0, QtCore.Qt.AlignTop)

        self.Layout2.addWidget(self.mTitle)
        self.Layout2.addWidget(self.mCaption)

        self.BalloonLayout.addLayout(self.Layout2)

        if progress:
            self.progressBar = QtGui.QProgressBar()
            self.Layout2.addWidget(self.progressBar)

        if credentials and conf.USER != "":
            self.credentials = credentials
            self.creds_layout = QtGui.QVBoxLayout()
            msg = "(" + conf.USER + ") - "
            if keyring:
                msg += u"Vous êtes déjà authentifié"
            else:
                msg += u"S'authentifier"
            self.credentials_button = QtGui.QPushButton(QtGui.QIcon(os.path.join(conf.IMGDIR, "credentials.png")), msg, self)
            self.credentials_button.setFlat(True)
            self.credentials_button.setDefault(True)
            self.connect(self.credentials_button, QtCore.SIGNAL("clicked()"), self.show_login)
            self.creds_layout.addWidget(self.credentials_button, 0, QtCore.Qt.AlignLeft)
            self.Layout2.addLayout(self.creds_layout)

        self.setAutoFillBackground(True)
        deskRect = QtCore.QRect(desktop.availableGeometry())
        self.currentAlpha = 0
        self.setWindowOpacity(0.0)
        self.resize(350, 80)
    
        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)
        self.timer.start(1)

        if timeout:
            self.destroytimer = QtCore.QTimer(self)
            self.connect(self.destroytimer, QtCore.SIGNAL("timeout()"), self.destroy)
            self.destroytimer.start(timeout)

        self.show()
        self.connect(self, QtCore.SIGNAL("clicked()"), self.destroy)
        
    def timerEvent (self, event):
        self.raise_()
         
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
        self.pass_label = QtGui.QLabel("Mot de passe UFO: ")
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
        self.remember = QtGui.QCheckBox(u"Enregistrer mon mot de passe")
        self.creds_layout.addWidget(self.remember)

    def hide_login(self):
        self.login_shown = False
        for control in [ self.pass_label, self.password, self.ok_button, self.remember, self.hline ]:
            control.hide()
        self.creds_layout.removeWidget(self.remember)
        self.creds_hbox.removeWidget(self.password)
        self.creds_hbox.removeWidget(self.ok_button)
        self.creds_hbox.removeWidget(self.pass_label)
        self.creds_hbox.removeWidget(self.hline)
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
            self.credentials(self.password.text(), self.remember.isChecked())
            if len(self.credentials_button.text()) - len(conf.USER) - 10 > len("S'authentifier"):
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

        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(0, 0, self.width(), self.height()), 7, 7)
        
        if paintEvent:
            painter = QtGui.QPainter(self)
        else:
            pixmap = QtGui.QPixmap(self.size())
            painter = QtGui.QPainter()
            painter.begin(pixmap)
        
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2, QtCore.Qt.SolidLine))
        painter.setClipPath(path)
        painter.drawPath(path)
        mask = painter.clipRegion()
        if not paintEvent:
            painter.end()
        return mask

    def paintEvent(self, evt):
        self.draw(paintEvent=True)

# Globals

def download_file(url, filename, title = u"Téléchargement...",
                  msg = u"Veuillez patienter le téléchargement est en cours",
                  autostart=False, autoclose=False):
    downloadWin = DownloadWindow(url=url, filename=filename, title=title, msg=msg,
                                 autostart=autostart, autoclose=autoclose, embedded_progress=True)
    if not autostart:
        downloadWin.show()
        return downloadWin.exec_() != QtGui.QDialog.Accepted
    else:
        ret = downloadWin.exec_()
        if downloadWin.was_canceled():
            return 1
        return ret != QtGui.QDialog.Accepted

def wait_command(cmd, title=u"Veuillez patienter", msg=u"Une opération est en cours"):
    cmdWin = WaitWindow(cmd, title, msg)
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

def dialog_question(title, msg, button1="Yes", button2="No"):
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
        msg = u"Veuillez entrer le mot de passe de l'utilisateur " + os.environ["USER"]

    dlg = QtGui.QInputDialog(w)
    dlg.setLabelText(msg)
    dlg.setWindowTitle("Saisie de mot de passe")
    dlg.setTextEchoMode(QtGui.QLineEdit.Password)
    if remember:
        check = QtGui.QCheckBox("Ne plus me poser la question")
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

def create_app():
    global app
    app = QtGui.QApplication(sys.argv)
    # After this line, subprocess needs to be patch as in Ubuntu
    # http://svn.python.org/view?view=rev&revision=65475
    # http://twistedmatrix.com/trac/ticket/733

def destroy_app(app):
    app.exit()
    app = None
    
app = QtUFOGui(sys.argv)
desktop = app.desktop()
screenRect = desktop.screenGeometry(desktop.primaryScreen())
main = QtGui.QMainWindow(desktop)
main.resize(screenRect.width(), screenRect.height())
