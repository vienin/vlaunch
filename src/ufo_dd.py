import gui
import logging
import subprocess
import time
import os
import sys
from conf import conf
from PyQt4 import QtGui

class DDWindow(QtGui.QDialog):
    def get_usb_list(self, usbs):
        choicelist = QtGui.QListWidget()
        for i in usbs.keys():
            choicelist.addItem(i)
        return choicelist

    def __init__(self, backend, relaunch=""):
        super(DDWindow, self).__init__()
        self.backend = backend

        self.source_filename = ""
        self.target_filename = ""
        self.setWindowTitle(_("UFO cloner"))

        self.dl_mutex = False

        self.usbs = {}
        for usb in self.backend.get_usb_sticks():
            self.usbs[usb[1]] = usb[0]

        main_layout = QtGui.QVBoxLayout()

        groupbox = QtGui.QGroupBox(_("Source"))
        box_layout = QtGui.QVBoxLayout()
        self.dl_button = QtGui.QPushButton(_("Download latest version from the Internet"))
        self.dl_button.clicked.connect(self.on_dl)
        box_layout.addWidget(self.dl_button)
        self.source = source = QtGui.QButtonGroup()

        self.source_image = source_image = QtGui.QRadioButton(_("From a file"), groupbox)
        source_image.clicked.connect(self.on_source_select)
        source.addButton(source_image)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(source_image)
        self.source_label = QtGui.QLabel("")
        hlayout.addWidget(self.source_label)
        box_layout.addLayout(hlayout)

        source_key = QtGui.QRadioButton(_("From a USB key"), groupbox)
        source.addButton(source_key)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(source_key)
        box_layout.addLayout(hlayout)
        self.source_key_list = self.get_usb_list(self.usbs)
        box_layout.addWidget(self.source_key_list)

        groupbox.setLayout(box_layout)
        main_layout.addWidget(groupbox)

        groupbox = QtGui.QGroupBox(_("Target"))
        box_layout = QtGui.QVBoxLayout()
        self.target = target = QtGui.QButtonGroup()

        self.target_image = target_image = QtGui.QRadioButton(_("To a file"), groupbox)
        target_image.clicked.connect(self.on_target_select)
        target.addButton(target_image)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(target_image)
        self.target_label = QtGui.QLabel("")
        hlayout.addWidget(self.target_label)
        box_layout.addLayout(hlayout)

        self.target_key = target_key = QtGui.QRadioButton(_("To a USB key"), groupbox)
        target.addButton(target_key)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(target_key)
        box_layout.addLayout(hlayout)
        self.target_key_list = self.get_usb_list(self.usbs)
        box_layout.addWidget(self.target_key_list)

        groupbox.setLayout(box_layout)
        main_layout.addWidget(groupbox)

        hlayout = QtGui.QHBoxLayout()
        self.start_button = QtGui.QPushButton(_("Start"))
        self.start_button.clicked.connect(self.on_start)
        hlayout.addWidget(self.start_button)
        self.exit_button = QtGui.QPushButton(_("Exit"))
        self.exit_button.clicked.connect(self.on_exit)
        hlayout.addWidget(self.exit_button)
        main_layout.addLayout(hlayout)

        self.setLayout(main_layout)

        if relaunch:
            self.clone(relaunch.split('#')[0], relaunch.split('#')[1])

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
            source_size = os.stat(source).st_size
        else:
            if not self.source_key_list.currentItem():
                gui.dialog_info(title=_("Missing source key"), msg=_("Please specify a source key"))
                return
            source = self.usbs[str(self.source_key_list.currentItem().text())]
            source_size = self.backend.get_device_size(source) * 512
        if self.target.checkedButton() == self.target_image:
            if not self.target_filename:
                gui.dialog_info(title=_("Missing target image"), msg=_("Please specify a target image"))
                return
            target = self.target_filename
        else:
            if not self.target_key_list.currentItem():
                gui.dialog_info(title=_("Missing target key"), msg=_("Please specify a target key"))
                return
            target = self.usbs[str(self.target_key_list.currentItem().text())]
            target_size = self.backend.get_device_size(target) * 512
            print target
            if  target_size < source_size:
                gui.dialog_info(title=_("Source is higher than the selected target"),
                                msg=_("The size of the source you have selected (" + str(source_size / (1024 * 1024)) + " Mo)"
                                      " is higher than the size of the selected target key (" + str(target_size / (1024 * 1024) ) + " Mo)."
                                      "<br><br>Please select a source equal or smaller than the target key."))
                return

        if target == source:
            gui.dialog_info(title=_("Source and target are the same"), msg=_("Source and target can not be the same"))
            return

        self.prepare_as_args(str(source), str(target))
        self.clone(source, target)

    def on_dl(self):
        if self.dl_mutex:
            return
        self.dl_mutex = True

        filedialog = QtGui.QFileDialog(self, _("Please select a destination directory for the download"), os.getcwd())
        filedialog.setFileMode(QtGui.QFileDialog.Directory)
        filedialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        if filedialog.exec_() != QtGui.QDialog.Accepted:
            return

        self.dest_dir = str(filedialog.selectedFiles()[0])
        self.dest_file = os.path.join(self.dest_dir, "ufo-key-latest.img")

        logging.debug("Downloading " + conf.IMGURL + " to " + self.dest_file)
        retcode  = gui.download_file(conf.IMGURL,
                                     self.dest_file,
                                     title=_("Downloading UFO key image"),
                                     msg=_("Please wait while the image is being downloaded"),
                                     parent=self)
        if not retcode:
            self.source_filename = self.dest_file
            self.source_label.setText(self.dest_file)
            self.source_image.setChecked(True)

        else:
            gui.dialog_info(title=_("Warning"),
                            msg=_("The download has encountered a fatal error, please check your Internet connection and retry"))
        self.dl_mutex = False

    def clone(self, source, target):
        cmd = [ "if=" + str(source), "of=" + str(target), "bs=1M" ]

        if os.name == "win32":
            cmd.insert(0, "dd.exe")
        else:
            cmd.insert(0, "dd")

        self.umounted = False
        usbs = self.backend.get_usb_devices()
        for possible_dev in [source, target]:
            for usb in usbs:
                if possible_dev == usb[2]:
                    self.umounted = True
                    while not self.backend.umount_device(usb[0]):
                        input = gui.dialog_error_report(_("Warning"),
                                        _("UFO is not able to umount <b>\"" + usb[0] + "\"</b> because it seems to be busy.\n"
                                          "Please close the program that is using it and retry."),
                                        _("Retry"),
                                        error=False)
                        if not input:
                            return
                        time.sleep(0.3)

        self.start_button.setEnabled(False)
        self.exit_button.setEnabled(False)
        if gui.wait_command(cmd=cmd,
                            title=_("Please wait"),
                            msg=_("Writing the image to the disk. This process can take several minutes.")):
            if self.umounted:
                msg = _("The copy had terminated successfully.<br><br>Please unplug and replug your UFO key if you want to launch it now.")
            else:
                msg = _("The copy had terminated successfully.")
            gui.dialog_info(title=_("Operation succeed"), msg=msg)

        else:
            gui.dialog_info(title=_("Operation failed"),
                            msg=_("The copy has encountered a fatal error and can't be completed"),
                            error=True)
        self.start_button.setEnabled(True)
        self.exit_button.setEnabled(True)

    def prepare_as_args(self, source, target):
        self_copy  = False
        need_admin = False

        usbs = self.backend.get_usb_devices()
        for possible_dev in [source, target]:
            for usb in self.usbs.values():
                if possible_dev == usb:
                    need_admin = True
        for possible_dev in [source, target]:
            for usb in usbs:
                if conf.SCRIPT_PATH.startswith(usb[0]):
                    self_copy = True

        self.backend.checking_pyqt()
        if self_copy or need_admin:
            if self_copy:
                executable = self.backend.prepare_self_copy()
            else:
                executable = conf.SCRIPT_PATH

            cmd = [ executable, "--dd", "--relaunch", source + "#" + target]
            logging.debug("Launching cloner : " + " ".join(cmd))

            if need_admin and not self.backend.is_admin():
                self.backend.execv_as_root(executable, cmd)
            else:
                logging.shutdown()
                os.execv(executable, cmd)
            sys.exit(0)

    def on_source_select(self):
        filedialog = QtGui.QFileDialog(self, _("Please select an UFO image"), os.getcwd())
        if filedialog.exec_() != QtGui.QDialog.Accepted:
            return
        self.source_filename = str(filedialog.selectedFiles()[0])
        self.source_label.setText(self.source_filename)

    def on_target_select(self):
        filedialog = QtGui.QFileDialog(self, _("Please select an UFO image"), os.getcwd())
        if filedialog.exec_() != QtGui.QDialog.Accepted:
            return
        self.target_filename = str(filedialog.selectedFiles()[0])
        self.target_label.setText(self.target_filename)


if __name__ == "__main__":

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

    main = DDWindow(backend)
    main.exec_()
