import gui
from gui_pyqt import WaitWindow
import logging
import subprocess
import os
import sys
from conf import conf
from PyQt4 import QtGui

class MainWindow(QtGui.QDialog):
    def get_usb_list(self):
        usb = backend.get_usb_sticks()
        names = [ x[1] for x in usb ]
        choicelist = QtGui.QListWidget()
        for i in names:
            choicelist.addItem(i)
        return choicelist

    def __init__(self):
        super(MainWindow, self).__init__()
        self.source_filename = ""
        self.target_filename = ""
        self.setWindowTitle("UFO cloner")

        main_layout = QtGui.QVBoxLayout()

        groupbox = QtGui.QGroupBox("Source")
        box_layout = QtGui.QVBoxLayout()
        self.source = source = QtGui.QButtonGroup()

        self.source_image = source_image = QtGui.QRadioButton("From a file", groupbox)
        source_image.clicked.connect(self.on_source_select)
        source.addButton(source_image)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(source_image)
        self.source_label = QtGui.QLabel("")
        hlayout.addWidget(self.source_label)
        box_layout.addLayout(hlayout)

        source_key = QtGui.QRadioButton("A USB key", groupbox)
        source.addButton(source_key)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(source_key)
        box_layout.addLayout(hlayout)
        self.source_key_list = self.get_usb_list()
        box_layout.addWidget(self.source_key_list)

        groupbox.setLayout(box_layout)
        main_layout.addWidget(groupbox)

        groupbox = QtGui.QGroupBox("Target")
        box_layout = QtGui.QVBoxLayout()
        self.target = target = QtGui.QButtonGroup()

        self.target_image = target_image = QtGui.QRadioButton("From a file", groupbox)
        target_image.clicked.connect(self.on_target_select)
        target.addButton(target_image)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(target_image)
        self.target_label = QtGui.QLabel("")
        hlayout.addWidget(self.target_label)
        box_layout.addLayout(hlayout)

        self.target_key = target_key = QtGui.QRadioButton("A USB key", groupbox)
        target.addButton(target_key)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(target_key)
        box_layout.addLayout(hlayout)
        self.target_key_list = self.get_usb_list()
        box_layout.addWidget(self.target_key_list)

        groupbox.setLayout(box_layout)
        main_layout.addWidget(groupbox)

        hlayout = QtGui.QHBoxLayout()
        start_button = QtGui.QPushButton("Start")
        start_button.clicked.connect(self.on_start)
        hlayout.addWidget(start_button)
        exit_button = QtGui.QPushButton("Exit")
        exit_button.clicked.connect(self.on_exit)
        hlayout.addWidget(exit_button)
        main_layout.addLayout(hlayout)

        self.setLayout(main_layout)

    def on_exit(self):
        sys.exit(0)

    def on_start(self):
        if not self.source.checkedButton():
            gui.dialog_info(title=_("Missing source"), msg=_("Please specify a source"))
            return
        if not self.target.checkedButton():
            gui.dialog_info(title=_("Missing target"), msg=_("Please specify a target"))
            return
        conf.IMGDIR = os.getcwd()
        if self.source.checkedButton() == self.source_image:
            if not self.source_filename:
                gui.dialog_info(title=_("Missing source image"), msg=_("Please specify a source image"))
                return
            source = self.source_filename
        else:
            if not self.source_key_list.currentItem():
                gui.dialog_info(title=_("Missing source key"), msg=_("Please specify a source key"))
                return
            source = self.source_key_list.currentItem().getText()
        if self.target.checkedButton() == self.target_image:
            if not self.target_filename:
                gui.dialog_info(title=_("Missing target image"), msg=_("Please specify a target image"))
                return
            target = self.target_filename
        else:
            if not self.target_key_list.currentItem():
                gui.dialog_info(title=_("Missing target key"), msg=_("Please specify a target key"))
                return
            target = self.target_key_list.currentItem().getText()
        if target == source:
            gui.dialog_info(title=_("Source and target are the same"), msg=_("Source and target can not be the same"))
            return
        cmd = [ "if=" + source, "of=" + target, "bs=1M" ]
        if os.name == "win32":
            WaitWindow(["dd.exe", 'if=' + str(filename), "bs=1M", "of=" + dev, "--progress"],
                       "Please wait", "Writing the image to the disk", "Success", "Error").run()
        else:
            WaitWindow(["dd"] + cmd,
                       "Please wait", "Writing the image to the disk", "Success", "Error").run()

    def on_source_select(self):
        filedialog = QtGui.QFileDialog(None, "Please select an UFO image", os.getcwd())
        filedialog.exec_()
        self.source_filename = str(filedialog.selectedFiles()[0])
        self.source_label.setText(self.source_filename)

    def on_target_select(self):
        filedialog = QtGui.QFileDialog(None, "Please select an UFO image", os.getcwd())
        filedialog.exec_()
        self.target_filename = str(filedialog.selectedFiles()[0])
        self.target_label.setText(self.target_filename)

if sys.platform == "win32":
    from windowsbackend import *
    backend = WindowsBackend()
    logging.debug("Platfrom: win32")
elif sys.platform == "darwin":
    from macbackend import *
    backend = MacBackend()
    logging.debug("Platfrom: darwin")
elif sys.platform == "linux2":
    from linuxbackend import *
    backend = create_linux_distro_backend()
    logging.debug("Platfrom: linux2, distro: %s, version: %s, codename: %s" % (backend.dist, backend.version, backend.codename))
else:
    raise Exception("Unsupported platform")

main = MainWindow()
main.exec_()
