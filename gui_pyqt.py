# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, QtNetwork
import sys, os

app = QtGui.QApplication(sys.argv)
main = QtGui.QMainWindow()
desktop = app.desktop()
screenRect = desktop.screenGeometry(desktop.primaryScreen())

class OurMessageBox(QtGui.QMessageBox):
    def setMinimumSize(self, width, height):
        self._minSize = (width, height)

    def showEvent(self, event):
        QtGui.QMessageBox.showEvent(self, event)
        if hasattr(self, "_minSize"):
            self.setFixedSize(*self._minSize)

def create_message_box(title, msg, width = 200, height = 100, buttons = QtGui.QMessageBox.Ok):
    msgbox = OurMessageBox(desktop)
    msgbox.setText(msg)
    msgbox.setWindowTitle(title)
    msgbox.setMinimumSize(width, height)
    msgbox.setSizeGripEnabled(True)
    msgbox.setStandardButtons(buttons)

    msgbox.setGeometry((screenRect.width() - width) / 2,
                       (screenRect.height() - height) / 2,
                       width, height)
    return msgbox

def dialog_info(title, msg):
    # QtGui.QMessageBox.information(main, title, msg)
    msgbox = create_message_box(title=title, msg=msg)
    msgbox.exec_()

def dialog_question(title, msg, button1="Yes", button2="No"):
    reply = create_message_box(title=title, msg=msg, buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    if reply == QtGui.QMessageBox.Yes: return button1
    else: return button2

def dialog_password(msg=None):
    dlg = QtGui.QInputDialog(desktop)
    dlg.setTextEchoMode(QtGui.QLineEdit.Password)
    if not msg:
        msg = u"Veuillez entrer le mot de passe de l'utilisateur " + os.environ["USER"]
    dlg.setLabelText(msg)
    dlg.setWindowTitle(u"Autorisations nécessaires")
    dlg.exec_()
    return dlg.textValue()

class DownloadWindow(QtGui.QDialog):
    def __init__(self, url, filename, parent=None):
        super(DownloadWindow, self).__init__(parent)

        self.url = url
        self.fileName = filename
        self.outFile = None
        self.httpGetId = 0
        self.httpRequestAborted = False

        self.statusLabel = QtGui.QLabel(self.tr(u"Un live U.F.O est nécessaire pour continuer. \n"   
                                                u"Cliquez sur 'Télécharger' pour commencer le téléchargement.\n\n"
                                                u"Cette opération peut prendre de quelques minutes à plusieurs heures\n" 
                                                u"suivant la vitesse de votre connexion."))

        self.progressDialog = QtGui.QProgressDialog(self)

        self.downloadButton = QtGui.QPushButton(self.tr(u"Télécharger"))
        self.downloadButton.setDefault(True)
        self.quitButton = QtGui.QPushButton(self.tr(u"Quitter"))
        self.quitButton.setAutoDefault(False)

        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.addButton(self.downloadButton,
                QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(self.quitButton, QtGui.QDialogButtonBox.RejectRole)

        self.http = QtNetwork.QHttp(self)

        self.http.requestFinished.connect(self.httpRequestFinished)
        self.http.dataReadProgress.connect(self.updateDataReadProgress)
        self.http.responseHeaderReceived.connect(self.readResponseHeader)

        self.progressDialog.canceled.connect(self.cancelDownload)
        self.downloadButton.clicked.connect(self.downloadFile)   
        self.quitButton.clicked.connect(self.close)

        topLayout = QtGui.QHBoxLayout()

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(topLayout) 
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle(self.tr(u"Téléchargement de l'image"))

    def downloadFile(self):
        fileName = self.fileName
        self.outFile = QtCore.QFile(fileName)
        if not self.outFile.open(QtCore.QIODevice.WriteOnly):
            QtGui.QMessageBox.information(self, self.tr("HTTP"),
                    self.tr(u"Impossible d'écrire dans le fichier %1: %2.").arg(fileName).arg(self.outFile.errorString()))
            self.outFile = None
            return

        self.http.setHost(QtCore.QUrl(self.url).host())

        self.httpGetId = self.http.get(self.url, self.outFile)

        self.progressDialog.setWindowTitle(self.tr(u"Téléchargement de l'image"))
        self.progressDialog.setLabelText(self.tr(u"Téléchargement en cours : %1.").arg(fileName))
        self.downloadButton.setEnabled(False)

    def cancelDownload(self):
        self.statusLabel.setText(self.tr(u"Téléchargement annulé. \n"
                                         u"Cliquer sur 'Télécharger' pour recommencer."))
        self.httpRequestAborted = True
        self.http.abort()
        self.downloadButton.setEnabled(True)

    def httpRequestFinished(self, requestId, error):
        if requestId != self.httpGetId:
            return

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
            QtGui.QMessageBox.information(self, self.tr("HTTP"),
                    self.tr(u"Le téléchargement a échoué. Vérifiez votre connexion Internet."))
        else:
            self.statusLabel.setText(self.tr(u"Téléchargement terminé. Cliquez sur 'Démarrer' pour continuer."))
            self.downloadButton.setText(u"Démarrer")
            self.statusLabel.setText(self.tr(u"Veuillez patienter pendant le "   
                                             u"téléchargement de l'image."))

        self.downloadButton.setEnabled(True)
        self.outFile = None

    def readResponseHeader(self, responseHeader):
        # Check for genuine error conditions.
        if responseHeader.statusCode() not in (200, 300, 301, 302, 303, 307):
            QtGui.QMessageBox.information(self, self.tr("HTTP"),
                                          self.tr("Le téléchargement est actuellement indisponible. " \
                                                  "Merci de bien vouloir réesayer plus tard.")) # responseHeader.reasonPhrase()))
            self.httpRequestAborted = True
            self.progressDialog.hide()
            self.http.abort()

    def updateDataReadProgress(self, bytesRead, totalBytes):
        if self.httpRequestAborted:
            return

        self.progressDialog.setMaximum(totalBytes)
        self.progressDialog.setValue(bytesRead)   

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

