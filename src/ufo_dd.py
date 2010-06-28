from conf import conf
from PyQt4 import QtGui, QtCore

import logging
import subprocess
import time
import os
import sys
import gui

class DDWindow(QtGui.QWizard):
    def __init__(self, backend, relaunch=""):
        super(DDWindow, self).__init__()
        self.backend = backend
        self.dl_mutex = False
        self.usbs = dict(self.backend.get_usb_sticks())
        self.letters = {}
        for usb in self.backend.get_usb_devices():
            devname = usb[2]
            self.letters[devname] = self.letters.get(devname, []) + [ usb[0][0] ]
            model = self.usbs[devname]
            if model.endswith(")"):
                model = model[:-2] + " " + usb[0] + " )"
            else:
                model = model + " ( " + usb[0][:-1] + " )"
            self.usbs[devname] = model
        self.usbs = self.usbs.items()

        self.connect(self, QtCore.SIGNAL("currentIdChanged(int)"), self.currentIdChanged)

        self.addPage(self.create_intro_page())
        self.addPage(self.create_burn_page())
        self.addPage(self.create_processing_page())
        self.addPage(self.create_finish_page())

        self.setWindowTitle(_("Mobile PC Creator"))

    def on_dl(self):
        if self.dl_mutex:
            return
        self.dl_mutex = True

        filedialog = QtGui.QFileDialog(self, _("Please select a destination directory for the download"), os.getcwd())
        filedialog.setFileMode(QtGui.QFileDialog.Directory)
        filedialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        if filedialog.exec_() != QtGui.QDialog.Accepted:
            self.dl_mutex = False
            return

        self.dest_dir = str(filedialog.selectedFiles()[0])
        self.dest_file = os.path.join(self.dest_dir, "ufo-key-latest.img")

        logging.debug("Downloading " + conf.IMGURL + " to " + self.dest_file)
        retcode  = gui.download_file(conf.IMGURL,
                                     self.dest_file,
                                     title=_("Downloading UFO key image"),
                                     msg=_("Please wait while the image is being downloaded"),
                                     parent=self, autoclose = True, autostart = True)
        if not retcode:
            self.source_filename = self.dest_file
            self.source.setText(self.dest_file)

        else:
            gui.dialog_info(title=_("Warning"),
                            msg=_("The download has encountered a fatal error, please check your Internet connection and retry"))
        self.dl_mutex = False

    def clone(self, source, target):
        cmd = [ "if=" + str(source), "of=" + str(target), "bs=" + str(1024*1024) ]

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

    def prepare_as_args(self):
        self_copy  = False
        need_admin = not self.backend.is_admin()

        usbs = self.backend.get_usb_devices()
        # if not self.backend.is_admin():
        #     for possible_dev in [source, target]:
        #         for usb in self.usbs.values():
        #             if possible_dev == usb:
        #                 need_admin = True
        for usb in usbs:
            if conf.SCRIPT_PATH.startswith(usb[0]):
                self_copy = True

        if self_copy or need_admin:
            if self_copy:
                executable = [ self.backend.prepare_self_copy() ]
            else:
                executable = [ sys.executable ] + sys.argv

            cmd = executable + [ "--dd" ]
            logging.debug("Launching creator : " + " ".join(cmd))

            self.backend.execv(cmd, root=need_admin)
            sys.exit(0)

    def on_source_select(self):
        filedialog = QtGui.QFileDialog(self, _("Please select an UFO image"), os.getcwd())
        if filedialog.exec_() != QtGui.QDialog.Accepted:
            return
        self.source_filename = str(filedialog.selectedFiles()[0])
        self.source.setText(self.source_filename)

    def on_target_select(self):
        filedialog = QtGui.QFileDialog(self, _("Please select an UFO image"), os.getcwd())
        if filedialog.exec_() != QtGui.QDialog.Accepted:
            return
        self.target_filename = str(filedialog.selectedFiles()[0])
        self.target_label.setText(self.target_filename)

    def create_intro_page(self):
        page = QtGui.QWizardPage()
        page.setTitle(_("Introduction"))
        label = QtGui.QLabel(_("Welcome to the Mobile PC Creator software.\n\n"
                               "This tool allows you to put G-Dium Mobile PC on your "
                               "USB pen drive or your USB hard drive or to backup "
                               "your G-Dium Mobile PC system into a file.\n\n"
                               "Please select what you want to do.\n"))
        label.setWordWrap(True)

        groupbox = QtGui.QGroupBox()
        create = QtGui.QRadioButton(_("Install G-Dium Mobile PC on a device"), groupbox)
        backup = QtGui.QRadioButton(_("Backup my G-Dium Mobile PC device"), groupbox)
        create.setChecked(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(create)
        layout.addWidget(backup)
        page.setLayout(layout)

        return page

    def create_burn_page(self):
        class BurnPage(QtGui.QWizardPage):
            def validatePage(_self):
                filename = self.source.text()
                if not filename or not os.path.exists(filename):
                    gui.dialog_info(title=_("Missing source image"),
                                    msg=_("Please specify a source image or download one by "
                                          "clicking the 'Download it' button"))
                    return False

                if self.choicelist.currentItem() == None:
                    gui.dialog_info(title=_("Missing target device"), msg=_("Please select a target device"))
                    return False

                self.device = self.usbs[self.choicelist.currentRow()][0]
                source_size = os.stat(filename).st_size
                target_size = self.backend.get_device_size(self.device) * 512

                if target_size < source_size:
                    gui.dialog_info(title=_("The selected device is too small"),
                                     msg=_("The size of the source you have selected (" + str(source_size / (1024 * 1024)) + " Mo)"
                                           " is bigger than the size of the selected target device (" + str(target_size / (1024 * 1024) ) + " Mo)."
                                           "<br><br>Please select a source equal or smaller than the target key."))
                    return False

                response = gui.dialog_question(title=_("All data on the device will be lost"),
                                               msg=_("To setup G-Dium Mobile PC on your device, "
                                                     "the device needs to be formatted. Are you sure you want to continue ?"),
                                               dangerous = True)
                if response != _("Yes"):
                    return False
                return True

        page = BurnPage()
        page.setTitle(_("Install G-Dium Mobile PC on my device"))
        layout = QtGui.QVBoxLayout()

        label = QtGui.QLabel(_("If you already have downloaded an image "
                               "please select its location, otherwise you "
                               "can download the latest version from the Web"))
        label.setWordWrap(True)
        layout.addWidget(label)

        hlayout = QtGui.QHBoxLayout()
        self.source = source = QtGui.QLineEdit()
        browse = QtGui.QPushButton("...")
        browse.clicked.connect(self.on_source_select)
        browse.setMaximumWidth(20)
        download = QtGui.QPushButton(_("Download it"))
        download.clicked.connect(self.on_dl)
        hlayout.addWidget(source)
        hlayout.addWidget(browse)
        hlayout.addWidget(download)
        layout.addLayout(hlayout)

        label = QtGui.QLabel(_("Please choose the target device:"))
        layout.addWidget(label)

        self.choicelist = choicelist = QtGui.QListWidget()
        for i in self.usbs:
            choicelist.addItem(i[1])
        layout.addWidget(choicelist)

        page.setLayout(layout)
        return page

    def create_processing_page(self):
        page = QtGui.QWizardPage()
        page.setTitle(_("Generating"))
        layout = QtGui.QVBoxLayout()

        label = QtGui.QLabel(_("Please wait while G-Dium Mobile PC is beeing "
                               "written to the device"))
        label.setWordWrap(True)
        layout.addWidget(label)

        self.progress = progress = QtGui.QProgressBar()
        layout.addWidget(progress)

        page.setLayout(layout)
        return page

    def create_finish_page(self):
        page = QtGui.QWizardPage()
        page.setTitle(_("Operation successfull !"))
        layout = QtGui.QVBoxLayout()

        label = QtGui.QLabel(_("G-Dium Mobile PC has been successfully installed "
                               "on your device. You can use it right away.\n\n"
                               "Enjoy !"))
        label.setWordWrap(True)
        layout.addWidget(label)

        page.setLayout(layout)
        return page

    def is_process_finished(self, value):
        if value == 100:
            self.next()

    def update_progress(self, sectors, total):
        if total:
            gui.app.postEvent(gui.app, gui.UpdateProgressEvent(self.progress, int(sectors / float(total) * 100)))

    def currentIdChanged(self, id):
        if id == len(self.pageIds()) - 2:
            self.progress.setRange(0, 100)
            self.progress.valueChanged.connect(self.is_process_finished)
            kwargs = {}
            if self.letters.has_key(self.device):
                kwargs["volume"] = self.letters[self.device][0]
            kwargs["callback"] = self.update_progress
            import threading
            threading.Thread(target=self.backend.write_image,
                             args=(self.source.text(), self.device),
                             kwargs=kwargs).start()

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
