# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
import threading, sys, os
from urllib import urlretrieve
import time, utils
import subprocess
import conf

class MyApp(QtGui.QApplication):
    def __init__(self, argv):
        self.progressDialog = None
        self.DownloadWindow = None
        self.waitWindow = None
        self.animation = None
        QtGui.QApplication.__init__(self, argv)

    def event(self, event):
        if isinstance(event, MyFinishedEvent):
            self.DownloadWindow.http_request_finished(event.error)
        elif self.progressDialog and isinstance(event, MyNoneEvent):
           self.progressDialog.setMaximum(event.total)
           self.progressDialog.setValue(event.size)
        elif self.waitWindow and isinstance(event, MyCommandEvent):
            self.waitWindow.finished(event.error)
        elif self.waitWindow and isinstance(event, MyUpdateEvent):
            self.waitWindow.update()
        return False

def create_app():
    global app
    app = QtGui.QApplication(sys.argv)
    # After this line, subprocess needs to be patch as in Ubuntu
    # http://svn.python.org/view?view=rev&revision=65475
    # http://twistedmatrix.com/trac/ticket/733

def destroy_app(app):
    app.exit()
    app = None

app = MyApp(sys.argv)
desktop = app.desktop()
screenRect = desktop.screenGeometry(desktop.primaryScreen())
main = QtGui.QMainWindow(desktop)
main.resize(screenRect.width(), screenRect.height())

class MyNoneEvent(QtCore.QEvent):
    def __init__(self, size, total):
        super(MyNoneEvent, self).__init__(QtCore.QEvent.None)
        self.size = size
        self.total = total
    pass

class MyFinishedEvent(QtCore.QEvent):
    def __init__(self, error=False):
        super(MyFinishedEvent, self).__init__(QtCore.QEvent.None)
        self.error = error
    pass

class MyCommandEvent(QtCore.QEvent):
    def __init__(self, error=False):
        super(MyCommandEvent, self).__init__(QtCore.QEvent.None)
        self.error = error
    pass

class MyUpdateEvent(QtCore.QEvent):
    def __init__(self, error=False):
        super(MyUpdateEvent, self).__init__(QtCore.QEvent.None)
        self.error = error
    pass

# Gere le téléchargement dans un thread a part.
# Envoie Deux type d'evenement à l'application :
#   1. MyNoneEvent pour chaque mise a jour de la progression du téléchargemetn
#   2. MyFinishedEvent quand il termine(sur une erreur ou non)
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
                    app.postEvent(app, MyFinishedEvent(True))
                else: 
                    app.postEvent(app, MyFinishedEvent(False))
                sys.exit()

        def progress(self, count, blockSize, totalSize):
                if self.toBeStop == True:
                    sys.exit()
                self.count = count
                self.maximum = totalSize
                self.downloaded = blockSize*count*100/totalSize
                app.postEvent(app, MyNoneEvent(int(self.downloaded), 100))

        def stop(self):
                self.toBeStop = True

class CommandLauncher(threading.Thread):
        def __init__(self, cmd): 
            threading.Thread.__init__(self)
            self.cmd = cmd

        def update(self):
            app.postEvent(app, MyUpdateEvent())
            
        def run(self):
            t = utils.call(self.cmd, spawn=True)
            while t.poll() == None:
                self.update()
                time.sleep(1)
            app.postEvent(app, MyCommandEvent(False))
            sys.exit()
    
class WaitWindow(QtGui.QDialog):
    def __init__(self,  cmd="", title="", msg="", parent=None):
        self.chars = ["     ", ".", "..", "..."]
        self.index = 0
        QtGui.QDialog.__init__(self, parent)
        self.cmd = cmd
        self.setWindowTitle(title)
        self.command = CommandLauncher(self.cmd)
        self.msg = msg
        app.waitWindow = self
        self.statusLabel = QtGui.QLabel(self.msg + " " + self.chars[self.index])
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
        print os.path.join(conf.HOME, "animated-bar.mng")
        self.animated = QtGui.QMovie(os.path.join(conf.HOME, "animated-bar.mng"), QtCore.QByteArray(), self.animation)
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

    def update(self):
        self.index = self.index + 1
        if self.index >= len(self.chars):
            self.index = 0
        self.statusLabel.setText(self.msg + " " + self.chars[self.index])

    def run(self):
        self.animated.start()
        self.show()
        self.command.start()
        return self.exec_()

class DownloadWindow(QtGui.QDialog):
    def __init__(self, url, filename, title, msg, parent=None, autostart=False):
        super(DownloadWindow, self).__init__(parent)

        app.DownloadWindow = self
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

# Globals functions

def set_icon(icon_path):
    QtGui.QApplication.setWindowIcon(QtGui.QIcon(icon_path))

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

