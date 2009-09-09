# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
import threading,sys,os
from urllib import urlretrieve


class MyNoneEvent(QtCore.QEvent):
    def __init__(self, size,total):
        super(MyNoneEvent,self).__init__(QtCore.QEvent.None)
        self.size = size
        self.total = total
    pass

class MyFinishedEvent(QtCore.QEvent):
    def __init__(self,error=False):
        super(MyFinishedEvent,self).__init__(QtCore.QEvent.None)
        self.error = error
    pass

class MyApp(QtGui.QApplication):
    def __init__(self, argv):
        self.progressDialog = None
        self.DownloadWindow = None
        QtGui.QApplication.__init__(self, argv)

    def event(self,event):
        if isinstance(event,MyFinishedEvent):
            self.DownloadWindow.httpRequestFinished(event.error)
        elif self.progressDialog and isinstance(event,MyNoneEvent):
           self.progressDialog.setMaximum(event.total)
           self.progressDialog.setValue(event.size)
        return False

app = MyApp(sys.argv)
desktop = app.desktop()
screenRect = desktop.screenGeometry(desktop.primaryScreen())
main = QtGui.QMainWindow(desktop)
main.resize(screenRect.width(), screenRect.height())

def set_icon(icon_path):
    QtGui.QApplication.setWindowIcon(QtGui.QIcon(icon_path))

def create_app():
    global app
    app = QtGui.QApplication(sys.argv)
    # After this line, subprocess needs to be patch as in Ubuntu
    # http://svn.python.org/view?view=rev&revision=65475
    # http://twistedmatrix.com/trac/ticket/733

def destroy_app(app):
    app.exit()
    app = None


# Gere le téléchargement dans un thread a part.
# Envoie Deux type d'evenement à l'application :
#   1. MyNoneEvent pour chaque mise a jour de la progression du téléchargemetn
#   2. MyFinishedEvent quand il termine(sur une erreur ou non)
# ATTENTION: pour chaque appel de stop par le thread principale il faut recréer l'objet downloader
class Downloader(threading.Thread):
        def __init__(self,file,dest): 
                threading.Thread.__init__(self)
                self.file=file
                self.dest=dest
                self.toBeStop=False

        def run(self):
                try:
                    yeah, headers = urlretrieve(self.file, self.dest, reporthook=self.progress)
                except :
                    app.postEvent(app,MyFinishedEvent(True))
                else: 
                    app.postEvent(app,MyFinishedEvent(False))
                sys.exit()

        def progress(self,count,blockSize,totalSize):
                if self.toBeStop==True:
                    sys.exit()
                self.count=count
                self.maximum=totalSize
                self.downloaded=blockSize*count*100/totalSize
                app.postEvent(app, MyNoneEvent(int(self.downloaded),100))

        def stop(self):
                self.toBeStop=True


class OurMessageBox(QtGui.QMessageBox):
    def setMinimumSize(self, width, height):
        self._minSize = (width, height)

    def showEvent(self, event):
        QtGui.QMessageBox.showEvent(self, event)
        if hasattr(self, "_minSize"):
            self.setFixedSize(*self._minSize)

def create_message_box(title, msg, width = 200, height = 100, buttons = QtGui.QMessageBox.Ok):
    darwin = sys.platform == "darwin"
    msgbox = OurMessageBox(main)
    msgbox.setText(msg)
    msgbox.setWindowTitle(title)
    if False: # darwin:
        msgbox.setMinimumSize(width, height)
        msgbox.setGeometry((screenRect.width() - width) / 2,
                           (screenRect.height() - height) / 2,
                           width, height)
    msgbox.setSizeGripEnabled(True)
    msgbox.setStandardButtons(buttons)

    return msgbox

def dialog_info(title, msg, error = False):
    msgbox = create_message_box(title=title, msg=msg)
    if error:
        msgbox.setIcon(QtGui.QMessageBox.Critical)
    else:
        msgbox.setIcon(QtGui.QMessageBox.Information)
    msgbox.exec_()

def dialog_question(title, msg, button1="Yes", button2="No"):
    msgbox = create_message_box(title=title, msg=msg, buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, width = 500)
    msgbox.setIcon(QtGui.QMessageBox.Question)
    reply = msgbox.exec_()
    if reply == QtGui.QMessageBox.Yes: return button1
    else: return button2

def dialog_password(msg=None, rcode=False):
    w=QtGui.QWidget()
    #dlg = QtGui.QInputDialog(main)
    #dlg.setTextEchoMode(QtGui.QLineEdit.Password)
    if not msg:
        msg = u"Veuillez entrer le mot de passe de l'utilisateur " + os.environ["USER"]
    #dlg.setLabelText(msg)
    #dlg.setWindowTitle(u"Autorisations nécessaires")
    #dlg.exec_()
    value = QtGui.QInputDialog.getText(w,"Saisi de mot de passe",msg,QtGui.QLineEdit.Password)
    if rcode:
        return value[0], ret
    else:
        return value[0]

class DownloadWindow(QtGui.QDialog):
    def __init__(self, url, filename, parent=None):
        super(DownloadWindow, self).__init__(parent)

        app.DownloadWindow = self
        self.url = url
        self.fileName = filename
        self.outFile = None
        self.httpGetId = 0
        self.httpRequestAborted = False
        self.finished = False

        self.statusLabel = QtGui.QLabel(u"Un live U.F.O est nécessaire pour continuer. \n"   
                                                u"Cliquez sur 'Télécharger' pour commencer le téléchargement.\n\n"
                                                u"Cette opération peut prendre de quelques minutes à plusieurs heures\n" 
                                                u"suivant la vitesse de votre connexion.")

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
        self.initDownloader()

        # On se connecte au Slot Qt pointant sur les evenement C++, sender,SIGNAL,callable
        self.connect(self.progressDialog,QtCore.SIGNAL("canceled()"),self.cancelDownload)
        self.connect(self.downloadButton,QtCore.SIGNAL("clicked()"),self.downloadFile)
        self.connect(self.quitButton,QtCore.SIGNAL("clicked()"),self.close)

        topLayout = QtGui.QHBoxLayout()

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(topLayout) 
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle(u"Téléchargement de l'image")

    def initDownloader(self):
        self.downloader=Downloader(self.url,self.fileName)
        

    def downloadFile(self):
        if self.finished:
            self.accept()

        fileName = self.fileName
        self.outFile = QtCore.QFile(fileName)
        if not self.outFile.open(QtCore.QIODevice.WriteOnly):
            QtGui.QMessageBox.information(self, "HTTP",
                    "Impossible d'écrire dans le fichier %s: %s."%(fileName,self.outFile.errorString()))
            self.outFile = None
            return

        self.progressDialog.setWindowTitle(u"Téléchargement de l'image")
        self.progressDialog.setLabelText(u"Téléchargement en cours : %s"%(fileName,))
        self.progressDialog.show()
        
        self.downloadButton.setEnabled(False)
        self.downloader.start()


    def cancelDownload(self):
        self.statusLabel.setText(u"Téléchargement annulé. \n"
                                         u"Cliquer sur 'Télécharger' pour recommencer.")
        self.httpRequestAborted = True
        self.downloader.stop()
        self.initDownloader()
        self.downloadButton.setEnabled(True)

    def httpRequestFinished(self,  error):
        if self.downloader.isAlive():
            self.downloader.join()

        self.initDownloader()
        if self.httpRequestAborted:
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

        self.downloadButton.setEnabled(True)
        self.outFile = None

def download_file(url, filename):
    downloadWin = DownloadWindow(url=url, filename=filename)
    downloadWin.show()
    return downloadWin.exec_()

class SplashScreen:
    def __init__(self, image):
        pixmap = QtGui.QPixmap(image)
        self.splash = QtGui.QSplashScreen(pixmap)
        self.splash.show()

    def destroy(self):
        self.splash.close()

