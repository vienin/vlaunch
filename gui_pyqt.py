# -*- coding: utf-8 -*-

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

        self.progress_dialog = None
        self.download_window = None
        self.wait_window     = None
        self.animation       = None
        self.tray            = None
        self.usb_check_timer = None
        self.callbacks_timer = None
        self.console_window  = None
        self.console_winid   = 0

        self.setWindowIcon(QtGui.QIcon(os.path.join(conf.IMGDIR, "UFO.png")))

    def event(self, event):
        if isinstance(event, SetTrayIconEvent):
            self.tray = TrayIcon()

        elif isinstance(event, FinishedEvent):
            self.download_window.http_request_finished(event.error)

        elif isinstance(event, CreateSplashEvent):
            self._create_splash_screen()

        elif isinstance(event, DestroySplashEvent):
            self._destroy_splash_screen()

        elif self.progress_dialog and isinstance(event, NoneEvent):
           self.progressDialog.setMaximum(event.total)
           self.progressDialog.setValue(event.size)
           
        elif self.wait_window and isinstance(event, CommandEvent):
            self.wait_window.finished(event.error)
            
        elif self.wait_window and isinstance(event, UpdateEvent):
            self.wait_window.update()
            
        elif isinstance(event, ProgressEvent):
            event.progress.setValue(int(event.value * 100))
            
        elif isinstance(event, BalloonMessageEvent):
            if not event.show:
                self.tray.hide_balloon()
            elif event.progress:
                self.tray.show_progress(event.title, event.msg)
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
                    
                if event.show:
                    self.console_window.showFullScreen()
                else:
                    self.console_window.show()
                    self.console_window.showMinimized()
                    
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
        self.postEvent(self, self.create_splash_event)

    def destroy_splash_screen(self):
        self.postEvent(self, DestroySplashEvent())

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

    def show_balloon_message(self, title, msg, timeout=0):
        self.postEvent(self, BalloonMessageEvent(title, 
                                                 msg, 
                                                 timeout))
        
    def show_balloon_progress(self, title, msg):
        self.postEvent(self, BalloonMessageEvent(title, 
                                                 msg, 
                                                 timeout=0, 
                                                 progress=True))
        
    def hide_balloon(self):
        self.postEvent(self, BalloonMessageEvent(title=None, 
                                                 msg=None, 
                                                 timeout=0, 
                                                 progress=None, 
                                                 show=False))
        
    def set_tooltip(self, tip):
        self.postEvent(self, ToolTipEvent(tip))
        
    def fullscreen_window(self, winid):
        self.postEvent(self, ConsoleWindowEvent(winid, True))
        
    def minimize_window(self, winid):
        self.postEvent(self, ConsoleWindowEvent(winid, False))
        
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
    def __init__(self, progress, value, total):
        super(ProgressEvent, self).__init__(QtCore.QEvent.None)
        self.progress = progress
        self.value    = value
        self.total    = total

class BalloonMessageEvent(QtCore.QEvent):
    def __init__(self, title, msg, timeout, progress=False, show=True):
        super(BalloonMessageEvent, self).__init__(QtCore.QEvent.None)
        self.show     = show
        self.title    = title
        self.msg      = msg
        self.timeout  = timeout
        self.progress = progress

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
    def __init__(self, winid, show):
        super(ConsoleWindowEvent, self).__init__(QtCore.QEvent.None)
        self.winid = winid
        self.show  = show

class FinishedEvent(QtCore.QEvent):
    def __init__(self, error=False):
        super(FinishedEvent, self).__init__(QtCore.QEvent.None)
        self.error = error

class CommandEvent(QtCore.QEvent):
    def __init__(self, error=False):
        super(CommandEvent, self).__init__(QtCore.QEvent.None)
        self.error = error

class UpdateEvent(QtCore.QEvent):
    def __init__(self, error=False):
        super(UpdateEvent, self).__init__(QtCore.QEvent.None)
        self.error = error


# Gere le téléchargement dans un thread a part.
# Envoie Deux type d'evenement à l'application :
#   1. NoneEvent pour chaque mise a jour de la progression du téléchargemetn
#   2. FinishedEvent quand il termine(sur une erreur ou non)
# ATTENTION: pour chaque appel de stop par le thread principale il faut recréer l'objet downloader
class Downloader(threading.Thread):
        def __init__(self, file, dest): 
                threading.Thread.__init__(self)
                self.file = file
                self.dest = dest
                self.toBeStop = False

        def run(self):
                try:
                    yeah, headers = urlretrieve(self.file, self.dest, reporthook=self.progress)
                except :
                    app.postEvent(app, FinishedEvent(True))
                else: 
                    app.postEvent(app, FinishedEvent(False))
                sys.exit()

        def progress(self, count, blockSize, totalSize):
                if self.toBeStop == True:
                    sys.exit()
                self.count = count
                self.maximum = totalSize
                self.downloaded = blockSize*count*100/totalSize
                app.postEvent(app, NoneEvent(int(self.downloaded), 100))

        def stop(self):
                self.toBeStop = True


class CommandLauncher(threading.Thread):
        def __init__(self, cmd): 
            threading.Thread.__init__(self)
            self.cmd = cmd

        def update(self):
            app.postEvent(app, UpdateEvent())
            
        def run(self):
            t = utils.call(self.cmd, spawn=True)
            while t.poll() == None:
                self.update()
                time.sleep(1)
            app.postEvent(app, CommandEvent(False))
            sys.exit()
    

class WaitWindow(QtGui.QDialog):
    def __init__(self,  cmd="", title="", msg="", parent=None):
        super(WaitWindow, self).__init__(main)
        self.cmd = cmd
        self.setWindowTitle(title)
        self.command = CommandLauncher(self.cmd)
        self.msg = msg
        app.wait_window = self
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
    def __init__(self, url, filename, title, msg, parent=None, autostart=False):
        super(DownloadWindow, self).__init__(main)

        app.download_window = self
        self.url = url
        self.fileName = filename
        self.autostart = autostart
        self.outFile = None
        self.httpGetId = 0
        self.http_request_aborted = False
        self.finished = False
        self.autostart = autostart
        self.statusLabel = QtGui.QLabel(msg)
        self.progressDialog = QtGui.QProgressDialog(self)
        app.progressDialog = self.progressDialog
        self.progressDialog.setCancelButtonText(u"Annuler")
        self.downloadButton = QtGui.QPushButton(u"Télécharger")
        self.downloadButton.setDefault(True)
        self.quitButton = QtGui.QPushButton(u"Quitter")
        self.quitButton.setAutoDefault(False)
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.addButton(self.downloadButton,
                QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(self.quitButton, QtGui.QDialogButtonBox.RejectRole)
        # On prépare le thread qui gérera le téléchargement
        self.init_downloader()
        # On se connecte au Slot Qt pointant sur les evenement C++, sender, SIGNAL, callable
        self.connect(self.progressDialog, QtCore.SIGNAL("canceled()"), self.cancel_download)
        self.connect(self.downloadButton, QtCore.SIGNAL("clicked()"), self.download_file)
        self.connect(self.quitButton, QtCore.SIGNAL("clicked()"), self.close)
        topLayout = QtGui.QHBoxLayout()
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(topLayout) 
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        self.setWindowTitle(title)
        if self.autostart:
            self.download_file()

    def init_downloader(self):
        self.downloader = Downloader(self.url, self.fileName)
        
    def download_file(self):
        if self.finished:
            self.accept()
        fileName = self.fileName
        self.outFile = QtCore.QFile(fileName)
        if not self.outFile.open(QtCore.QIODevice.WriteOnly):
            QtGui.QMessageBox.information(self, "HTTP",
                    u"Impossible d'écrire dans le fichier %s: %s."%(fileName, self.outFile.errorString()))
            self.outFile = None
            return
        self.progressDialog.setWindowTitle(u"Téléchargement de l'image")
        self.progressDialog.setLabelText(u"Téléchargement en cours : %s"%(fileName, ))
        self.progressDialog.show()
        self.downloadButton.setEnabled(False)
        self.downloader.start()

    def cancel_download(self):
        self.statusLabel.setText(u"Téléchargement annulé. \n"
                                 u"Cliquer sur 'Télécharger' pour recommencer.")
        self.http_request_aborted = True
        self.downloader.stop()
        self.init_downloader()
        self.downloadButton.setEnabled(True)

    def http_request_finished(self,  error):
        if self.downloader.isAlive():
            self.downloader.join()

        self.init_downloader()
        if self.http_request_aborted:
            if self.outFile is not None:
                self.outFile.close() 
                self.outFile.remove()
                self.outFile = None
            self.progressDialog.hide()
            return

        self.progressDialog.hide()
        self.outFile.close()
        if error:
            self.outFile.remove()
            QtGui.QMessageBox.information(self, "HTTP",
                    u"Le téléchargement a échoué. Vérifiez votre connexion Internet.")
        else:
            self.finished = True
            # On cache les boutons
            self.downloadButton.hide()
            self.quitButton.setText(u"Continuer")
            self.statusLabel.setText(u"Téléchargement terminé.")

        if self.autostart:
            self.close()
            
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
        #self.activated.connect(self.activate)
        
        self.progress = None
        self.balloon  = None
        
        self.setToolTip(QtCore.QString(u"UFO: en cours de démarrage"))
        self.show()

    def show_message(self, title, msg, timeout=0):
        self.balloon = BalloonMessage(self, icon = os.path.join(conf.IMGDIR, "UFO.png"),
                                      title=title, msg=msg, timeout=timeout)

    def show_progress(self, title, msg, timeout=0, no_text=False, invert=False):
        self.balloon = BalloonMessage(self, icon = os.path.join(conf.IMGDIR, "UFO.png"),
                                     title=title, msg=msg, progress=True)
        self.progress = self.balloon.progressBar
        #if no_text:
        #    self.progress.setTextVisible(False)
        #if invert:
        #    self.progress.setInvertedAppearance(True)

    def hide_balloon(self):
        if self.balloon:
            self.balloon.close()
            del self.balloon
            self.balloon = None
        self.progress = None

    def activate(self):
        pass


class BalloonMessage(QtGui.QWidget):
    def __init__(self, parent, icon, title, msg, timeout=0, progress=False):

        QtGui.QWidget.__init__(self, None, 
                         QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.X11BypassWindowManagerHint | QtCore.Qt.ToolTip)

        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.parent = parent
        self.mAnchor = QtCore.QPoint()
        BalloonLayout = QtGui.QHBoxLayout(self)

        Layout2 = QtGui.QVBoxLayout()
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
            BalloonLayout.addWidget(mImage)

        Layout2.addWidget(self.mTitle)
        Layout2.addWidget(self.mCaption)

        BalloonLayout.addLayout(Layout2)

        if progress:
            self.progressBar = QtGui.QProgressBar()
            Layout2.addWidget(self.progressBar)

        self.setAutoFillBackground(True)

        self.currentAlpha = 0
        self.setWindowOpacity(1.0)
        self.resize(180, 80)
    
        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timeout)
        #self.timer.timeout.connect(self.timeout)
        self.timer.start(1)

        if timeout:
            self.destroytimer = QtCore.QTimer(self)
            self.connect(self.destroytimer, QtCore.SIGNAL("timeout()"), self.destroy)
            #self.destroytimer.timeout.connect(self.destroy)
            self.destroytimer.start(timeout)

        deskRect = QtCore.QRect(desktop.availableGeometry())
        self.mAnchor = QtCore.QPoint(app.tray.geometry().center().x(),
                                     app.tray.geometry().bottom())
        self.show()
        self.connect(self, QtCore.SIGNAL("clicked()"), self.destroy)

    def destroy(self):
        self.close()

    def timeout(self):
        if self.currentAlpha <= 255:
            self.currentAlpha += 15
            self.timer.start(1)
        self.setWindowOpacity(1. / 255. * self.currentAlpha)

    def setAnchor(self, anchor):
        self.mAnchor = anchor
        deskRect = QtCore.QRect(desktop.availableGeometry())
        if self.mAnchor.y() > deskRect.height() / 2:
            y = - self.height() - 40
        else:
            y = 40
        self.move(deskRect.width() - self.width() - 10, self.mAnchor.y() + y)

    def showUpdateWindow(self):
        self.parent.parent.mainwidget.trayUpgradeSwitch()
        self.parent.parent.show()

    def paintEvent(self, evt):
        mask = QtGui.QRegion() # 10, 10, self.width() - 20, self.height() - 20)

        corners = [
            QtCore.QPoint(self.width() - 50, 10),
            QtCore.QPoint(10, 10),
            QtCore.QPoint(10, self.height() - 50),
            QtCore.QPoint(self.width() - 50, self.height() - 50),
            QtCore.QPoint(self.width() - 10, 10),
            QtCore.QPoint(10, 10),
            QtCore.QPoint(10, self.height() - 10),
            QtCore.QPoint(self.width() - 10, self.height() - 10)
            ]

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        path = QtGui.QPainterPath()
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 1, QtCore.Qt.SolidLine))
        path.addRoundedRect(QtCore.QRectF(0, 0, self.width(), self.height()), 7, 7)

        # get screen-geometry for screen our anchor is on
        # (geometry can differ from screen to screen!
        deskRect = QtCore.QRect(desktop.availableGeometry())

        bottom = (self.mAnchor.y() + self.height()) > ((deskRect.y() + deskRect.height()-48));
        right = (self.mAnchor.x() + self.width()) > ((deskRect.x() + deskRect.width()-48));

        if right:
            if bottom:
                points = [ QtCore.QPointF(self.width(), self.height()),
                           QtCore.QPointF(self.width() - 10, self.height() - 30),
                           QtCore.QPointF(self.width() - 30, self.height() - 10) ]
            else:
                points = [ QtCore.QPointF(self.width() , 0),
                           QtCore.QPointF(self.width() - 10,30),
                           QtCore.QPointF(self.width() - 30,10) ]
        else:
            if bottom:
                points = [ QtCore.QPointF(0, self.height()),
                           QtCore.QPointF(10, self.height() - 30),
                           QtCore.QPointF(30, self.height() - 10) ]
            else:
                points = [ QtCore.QPointF(0,0),
                           QtCore.QPointF(10,30),
                           QtCore.QPointF(30,10) ]

        point = QtCore.QPointF(points[0].x(), points[0].y())
        points += [ point ]
        # path.addPolygon(QtGui.QPolygonF(points))

        """
        if right:
            if bottom:
                self.move(self.mAnchor.x() - self.width(), self.mAnchor.y() - self.height())
            else:
                if self.mAnchor.y() < 0:
                    self.move(self.mAnchor.x() - self.width(), 0)
                else:
                    self.move(self.mAnchor.x() - self.width(), self.mAnchor.y())
        else:
            if bottom:
                if self.mAnchor.x() < 0:
                    self.move(0, self.mAnchor.y() - self.height())
                else:
                    self.move(self.mAnchor.x(), self.mAnchor.y() - self.height())
            else:
                if self.mAnchor.x() < 0:
                    if self.mAnchor.y() < 0:
                        self.move(0,0)
                    else:
                        self.move(0,self.mAnchor.y())
                else:
                    if self.mAnchor.y() < 0:
                        self.move(self.mAnchor.x(),0)
                    else:
                        self.move(self.mAnchor.x(),self.mAnchor.y())
        """
        painter.setClipPath(path)
        painter.drawPath(path)
        mask = painter.clipRegion()
        self.setMask(mask)

# Globals

def download_file(url, filename, title = u"Téléchargement...", msg = u"Veuillez patienter le télécharchement est en cours", autostart=False):
    downloadWin = DownloadWindow(url=url, filename=filename, title=title, msg=msg, autostart=autostart)
    if not autostart:
        downloadWin.show()
        return downloadWin.exec_()
    else:
        downloadWin.progressDialog.exec_()

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

def dialog_password(msg=None, rcode=False):
    w = QtGui.QWidget()
    if not msg:
        msg = u"Veuillez entrer le mot de passe de l'utilisateur " + os.environ["USER"]

    value = QtGui.QInputDialog.getText(w, "Saisi de mot de passe", msg, QtGui.QLineEdit.Password)
    if rcode:
        return value
    else:
        return value[0]

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
