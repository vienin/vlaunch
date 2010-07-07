from conf import conf
from PyQt4 import QtGui, QtCore

import logging
import time
import os
import sys
import gui

class DDWindow(QtGui.QWizard):

    PAGE_INDEX_INTRO   = 0
    PAGE_INDEX_BURN    = 1
    PAGE_INDEX_PROCESS = 2
    PAGE_INDEX_FINISH  = 3

    def __init__(self, backend, relaunch=""):
        super(DDWindow, self).__init__()
        self.backend = backend

        self.load_usbs()
        
        self.connect(self, QtCore.SIGNAL("currentIdChanged(int)"), self.currentIdChanged)

        self.addPage(self.create_intro_page())
        self.addPage(self.create_burn_page())
        self.addPage(self.create_processing_page())
        self.addPage(self.create_finish_page())

        self.setWindowTitle(_("Mobile PC Creator"))

    def load_usbs(self):
        self.usbs = dict(self.backend.get_usb_sticks())
        letters = {}
        for usb in self.backend.get_usb_devices():
            mountpoint = usb[0]
            if mountpoint.endswith("\\"):
                mountpoint = mountpoint[:-1]
            devname = usb[2]
            letters[devname] = letters.get(devname, []) + [ usb[0][0] ]
            model = self.usbs[devname]
            if model.endswith(")"):
                model = model[:-2] + " " + mountpoint + " )"
            else:
                model = model + " ( " + mountpoint + " )"
            self.usbs[devname] = model
        self.usbs = self.usbs.items()

    def launch_process(self):
        self.button(QtGui.QWizard.NextButton).setEnabled(False)
        self.progress.setRange(0, 100)
        self.progress.valueChanged.connect(self.is_process_finished)
        kwargs = {}
        kwargs["callback"] = self.update_progress
        import threading
        threading.Thread(target=self.backend.write_image,
                         args=(str(self.source), str(self.target)),
                         kwargs=kwargs).start()

    def prepare(self):
        self_copy  = False
        need_admin = not self.backend.is_admin()

        usbs = self.backend.get_usb_devices()
        for usb in usbs:
            if conf.SCRIPT_PATH.startswith(usb[0]):
                self_copy = True

        if self_copy or need_admin:
            if self_copy:
                cmd = [ self.backend.prepare_self_copy(), "--dd" ]
            else:
                cmd = [ sys.executable ] + sys.argv + [  "--dd" ]

            logging.debug("Launching creator : " + " ".join(cmd))
            self.backend.execv(cmd, root=need_admin)
            sys.exit(0)

    def create_intro_page(self):
        class IntroPage(QtGui.QWizardPage):
            def validatePage(_self):
                if self.create.isChecked():
                    self.reverse = False
                else:
                    self.reverse = True
                return True

        page = IntroPage()
        page.setTitle(_("Introduction"))
        label = QtGui.QLabel(_("Welcome to the Mobile PC Creator software.\n\n"
                               "This tool allows you to put G-Dium Mobile PC on your "
                               "USB pen drive or your USB hard drive or to backup "
                               "your G-Dium Mobile PC system into a file.\n\n"
                               "Please select what you want to do.\n"))
        label.setWordWrap(True)

        groupbox = QtGui.QGroupBox()
        self.create = QtGui.QRadioButton(_("Install G-Dium Mobile PC on a device"), groupbox)
        self.backup = QtGui.QRadioButton(_("Backup my G-Dium Mobile PC device"), groupbox)
        self.create.setChecked(True)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.create)
        layout.addWidget(self.backup)
        page.setLayout(layout)

        return page

    def create_burn_page(self):
        def add_to_layout(layout, intem, align=False):
            if type(intem) == QtGui.QHBoxLayout:
                item_type = "layout"
                add_function = layout.addLayout
            else:
                item_type = "widget"
                add_function = layout.addWidget

            if not hasattr(layout, item_type + "s"):
                setattr(layout, item_type + "s", [])
            getattr(layout, item_type + "s").append(intem)
            if align:
                add_function(intem, 0, align)
            else:
                add_function(intem)

        class BurnPage(QtGui.QWizardPage):
            dl_mutex = False

            def validatePage(_self):
                if self.reverse:
                    missing_device_title = _("Missing source device")
                    missing_device_msg = _("Please select a source device")
                    missing_file_title = _("Missing target image")
                    missing_file_msg = _("Please specify a target image")
                else:
                    missing_device_title = _("Missing target device")
                    missing_device_msg = _("Please select a target device")
                    missing_file_title = _("Missing source image")
                    missing_file_msg = _("Please specify a source image or download one by "
                                         "clicking the 'Download it' button")

                # checking device selection
                if _self.usb_list.currentItem() == None:
                    gui.dialog_info(title=missing_device_title, msg=missing_device_msg)
                    return False

                # checking file  selection
                edit = _self.edit.text()
                if not edit or (not os.path.exists(edit) and not self.reverse):
                    gui.dialog_info(title=missing_file_title, msg=missing_file_msg)
                    return False

                if self.reverse:
                    self.source = str(self.usbs[_self.usb_list.currentRow()][0])
                    self.target = str(edit)
                    source_size = self.backend.get_device_size(self.source) * 512
                    disk_space = self.backend.get_free_space(os.path.dirname(self.target))
                    if disk_space < source_size:
                        gui.dialog_info(title=_("Insufficient disk space"),
                                    msg=_("The available size on your disk is insufficient. "
                                          "You need more than %d Mo free on your disk to backup your device."
                                          "<br><br>Please free some space and retry.") % ((source_size - disk_space) / 1024 / 1024))
                        return False
                else:
                    self.source = str(edit)
                    self.target = str(self.usbs[_self.usb_list.currentRow()][0])
                    source_size = os.stat(self.source).st_size
                    target_size = self.backend.get_device_size(self.target) * 512
                    if target_size < source_size:
                        gui.dialog_info(title=_("The selected target is too small"),
                                        msg=_("The size of the source you have selected (%d Mo)"
                                              " is bigger than the size of the selected target (%d Mo)."
                                              "<br><br>Please select a source equal or smaller than the target.") % (source_size / 1024 / 1024, target_size / 1024 / 1024))
                    return False

                if not self.reverse:
                    response = gui.dialog_question(title=_("All data on the device will be lost"),
                                                   msg=_("To setup %s on your device, "
                                                         "the device needs to be formatted. Are you sure you want to continue ?") % (conf.PRODUCTNAME,),
                                                   dangerous = True)
                    if response != _("Yes"):
                        return False

                self.umounted = False
                for possible_dev in [self.source, self.target]:
                    for usb in self.usbs:
                        if possible_dev == usb[0]:
                            self.umounted = True
                            while not self.backend.umount_device(usb[0]):
                                input = gui.dialog_error_report(_("Warning"),
                                                                _("%s is not able to umount <b>\"") % (conf.PRODUCTNAME,) + usb[0] + _("\"</b> because it seems to be busy.\n"
                                                                  "Please close the program that is using it and retry."),
                                                                _("Retry"),
                                                                error=False)
                                if not input:
                                    return False
                                time.sleep(0.3)

                return True

            def on_dl(_self):
                if _self.dl_mutex:
                    return
                _self.dl_mutex = True

                filedialog = QtGui.QFileDialog(self, _("Please select a destination directory for the download"), os.getcwd())
                filedialog.setFileMode(QtGui.QFileDialog.Directory)
                filedialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
                if filedialog.exec_() != QtGui.QDialog.Accepted:
                    _self.dl_mutex = False
                    return

                _self.dest_dir = str(filedialog.selectedFiles()[0])
                _self.dest_file = os.path.join(_self.dest_dir, "ufo-key-latest.img")

                logging.debug("Downloading " + conf.IMGURL + " to " + _self.dest_file)
                retcode  = gui.download_file(conf.IMGURL,
                                             _self.dest_file,
                                             title=_("Downloading UFO key image"),
                                             msg=_("Please wait while the image is being downloaded"),
                                             autoclose = True, autostart = True)
                if not retcode:
                    _self.edit.setText(_self.dest_file)

                else:
                    gui.dialog_info(title=_("Warning"),
                                    msg=_("The download has encountered a fatal error, please check your Internet connection and retry"))
                _self.dl_mutex = False

            def on_file_select(_self):
                filedialog = QtGui.QFileDialog(self, _("Please select an UFO image"), os.getcwd())
                if filedialog.exec_() != QtGui.QDialog.Accepted:
                    return
                _self.edit.setText(str(filedialog.selectedFiles()[0]))

            def on_refresh(self):
                self.load_usbs()
                _self.usb_list.clear()
                for i in self.usbs:
                    _self.usb_list.addItem(i[1])

            def create_file_chooser_label(_self, reverse):
                if reverse:
                    msg = _("Please select the target file your key will be backed up into")
                else:
                    msg = _("If you already have downloaded an image "
                            "please select its location, otherwise you "
                            "can download the latest version from the Web")
                label = QtGui.QLabel(msg)
                label.setWordWrap(True)
                return label

            def create_file_chooser_layout(_self, reverse):
                hlayout = QtGui.QHBoxLayout()
                _self.edit = edit = QtGui.QLineEdit()
                browse = QtGui.QPushButton("...")
                browse.clicked.connect(_self.on_file_select)
                browse.setMaximumWidth(20)
                add_to_layout(hlayout, edit)
                add_to_layout(hlayout, browse)
                if not reverse:
                    download = QtGui.QPushButton(_("Download it"))
                    download.clicked.connect(_self.on_dl)
                    add_to_layout(hlayout, download)
                return hlayout

            def create_device_chooser_label(_self, reverse):
                hlayout = QtGui.QHBoxLayout()
                if reverse:
                    msg = _("Please choose the source device you want to backup:")
                else:
                    msg = _("Please choose the target device:")
                label = QtGui.QLabel(msg)
                refresh = QtGui.QPushButton(QtGui.QIcon(os.path.join(conf.IMGDIR, "reload.png")), _("Refresh"))
                refresh.setFlat(True)
                refresh.clicked.connect(_self.on_refresh)
                add_to_layout(hlayout, label)
                add_to_layout(hlayout, refresh, QtCore.Qt.AlignLeft)
                return hlayout

            def create_device_chooser_layout(_self):
                _self.usb_list = QtGui.QListWidget()
                for i in self.usbs:
                    _self.usb_list.addItem(i[1])
                return _self.usb_list

            def delete(_self, item):
                item.deleteLater()
                QtCore.QCoreApplication.sendPostedEvents(item, QtCore.QEvent.DeferredDelete)

            def reset(_self):
                layout = _self.layout()
                if hasattr(layout, "layouts"):
                    for lay in layout.layouts:
                        if hasattr(lay, "widgets"):
                            for widget in lay.widgets:
                                lay.removeWidget(widget)
                                _self.delete(widget)
                if hasattr(layout, "widgets"):
                    for widget in layout.widgets:
                        layout.removeWidget(widget)
                        _self.delete(widget)
                _self.delete(layout)

            def fill_page(_self, reverse):
                if _self.layout():
                    _self.reset()

                if reverse:
                    _self.setTitle(_("Backup my Gdium Mobile PC device on hard disk"))
                else:
                    _self.setTitle(_("Install Gdium Mobile PC on my device"))

                layout = QtGui.QVBoxLayout()

                if reverse:
                    add_to_layout(layout, _self.create_device_chooser_label(reverse))
                    add_to_layout(layout, _self.create_device_chooser_layout())
                    add_to_layout(layout, _self.create_file_chooser_label(reverse))
                    add_to_layout(layout, _self.create_file_chooser_layout(reverse))
                else:
                    add_to_layout(layout, _self.create_file_chooser_label(reverse))
                    add_to_layout(layout, _self.create_file_chooser_layout(reverse))
                    add_to_layout(layout, _self.create_device_chooser_label(reverse))
                    add_to_layout(layout, _self.create_device_chooser_layout())

                _self.setLayout(layout)

        page = BurnPage()
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
        if id == self.PAGE_INDEX_BURN:
            self.page(id).fill_page(self.reverse)

        elif id == self.PAGE_INDEX_PROCESS:
            self.launch_process()


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
