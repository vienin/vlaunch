from conf import conf
from PyQt4 import QtGui, QtCore

import logging
import time
import os
import sys
import gui
import tarfile
from ConfigParser import ConfigParser

STATUS_WRITING = 0

class DDWindow(QtGui.QWizard):

    PAGE_INDEX_INTRO   = 0
    PAGE_INDEX_BURN    = 1
    PAGE_INDEX_PROCESS = 2
    PAGE_INDEX_FINISH  = 3

    def __init__(self, backend, relaunch=""):
        super(DDWindow, self).__init__()
        self.backend = backend

        self.load_usbs()
        self.device_size = 0
        self.parts = []
        
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
        kwargs = {}
        kwargs["callback"] = self.update_progress
        import threading
        threading.Thread(target=self.write_image,
                         args=(unicode(self.source), unicode(self.target)),
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

    def repart(self, device, partitions, device_size, c, h, s):
        import mbr
        mb = mbr.MBR(device)
        mb.generate(partitions, device_size, c, h, s)
        mb.write(device)
        return mb

    def get_free_space(self):
        size = self.device_size
        for part in self.parts:
            size -= part["size"]
        return size

    def update_sliders(self):
        if not self.parts or not self.device_size:
            return

        self.button(QtGui.QWizard.NextButton).setEnabled(True)
        self.resize_label.setEnabled(True)
        self.splitter.setEnabled(True)

        sizes = []
        free_space = self.get_free_space()
        if not self.splitter.count():
           n = 0
           for i, part in enumerate(self.parts):
                if not part["resizable"]:
                    continue
                label = QtGui.QLabel(self.get_partition_pretty_name(part))
                label.setAlignment(QtCore.Qt.AlignCenter)
                label.setMinimumWidth(150)
                self.splitter.addWidget(label)
                self.splitter.setCollapsible(n, False)
                part["widget"] = label
                sizes.append(part["size"] + free_space * part["percentage"] / 100)
                n += 1

        widths = [ int(x / float(self.total_size)) for x in sizes ]
        self.splitter.setSizes(widths)
        self.update_sizes()

    def update_sizes(self):
        for i, part in self.get_resizable_partitions():
            self.update_text(part)

    def get_partition_pretty_name(self, part):
        return { "fat" : _("Public data"),
                 "root" : _("System data"),
                 "crypt" : _("Private data") }[part["name"]]

    def update_text(self, part):
        part["widget"].setText(self.get_partition_pretty_name(part) + " " + _("(%d Mo)") % (self.get_partition_size(part) / 1024 / 1024))

    def get_partition_size(self, part):
        if part.has_key("widget"):
            widget = part["widget"]
            return int((self.splitter.sizes()[self.splitter.indexOf(widget)] - widget.minimumWidth()) * self.get_size_per_pixel() + part["size"])
        else:
            return part["size"]

    def get_size_per_pixel(self):
        sizes = self.splitter.sizes()
        free_pixels = 0
        for i, size in enumerate(sizes):
            free_pixels += size - self.splitter.widget(i).minimumWidth()
        return float(self.get_free_space()) / free_pixels

    def get_resizable_partitions(self):
        return [ (self.parts.index(x), x) for x in self.parts if x["resizable"] ]

    def splitter_moved(self, pos, index):
        self.update_sizes()

    def on_select_device(self, row):
        self.open_device(self.usbs[row][0])
        self.update_sliders()

    def on_text_changed(self, text):
        if not self.reverse:
            self.open_target(unicode(text))
        self.update_sliders()

    def get_partition(self, name):
        for part in self.parts:
            if part["name"] == name:
                return part

    def open_device(self, device):
        self.device_size = self.backend.get_device_size(device) * 512

    def open_target(self, filename):
        if tarfile.is_tarfile(filename):
            self.parts = []
            self.total_size = 0
            tar = tarfile.open(filename)
            try:
                layout = ConfigParser()
                layout.readfp(tar.extractfile(tar.next()))
                for n in xrange(4):
                    section = "part%d" % n
                    if not layout.has_section(section):
                        break
                    size = int(layout.get(section, "size"))
                    self.total_size += size
                    self.parts.append( { "name" : layout.get(section, "name"),
                                         "type" : eval(layout.get(section, "type", "0x83")),
                                         "percentage" : int(layout.get(section, "percentage")),
                                         "size" : size,
                                         "resizable" : eval(layout.get(section, "resizable", "True")),
                                         "bootable" : eval(layout.get(section, "bootable", "False")) })

            except:
                logging.debug("Could not load layout.conf in archive %s" % filename)
                return -1

    def write_image(self, image, device, callback=None):
        if tarfile.is_tarfile(image):

            # We wait a bit otherwise it sometimes fails on Windows
            import time
            time.sleep(3)

            total_size = self.total_size
            device_size = self.device_size
            c, h, s = self.backend.get_disk_geometry(device)

            dev = self.backend.open(device, "rw")
            tar = tarfile.open(image)
            tar.next()

            logging.debug("Writing Master Boot Record")
            self.dd(tar.extractfile(tar.next()), dev)

            logging.debug("Repartition the key")
            mb = self.repart(dev, self.parts, device_size, c, h, s)

            written = 0
            i = 0
            while True:
                part = tar.next()
                if not part:
                    break
                logging.debug("Writing %s partition" % part.name)
                written += self.dd(tar.extractfile(part), dev, seek=mb.get_partition_offset(i),
                                   callback = lambda x: callback(x + written, total_size))
                i += 1
            dev.close()
        else:
            if self.reverse:
                total_size = self.get_device_size(image) * 512
            else:
                total_size = self.total_size
            self.dd(image, device, callback = lambda x: callback(x, total_size))

        self.next()

    def dd(self, src, dest, callback=None, bs=32768, count = -1, skip=0, seek=0):
        if type(src) in (str, unicode):
            srcfile = self.backend.open(src)
        else:
            srcfile = src

        if type(dest) in (str, unicode):
            destfile = self.backend.open(dest, 'w')
        else:
            destfile = dest

        logging.debug("Source %s opened" % (src, ))
        if skip:
            srcfile.seek(skip, os.SEEK_SET)

        if seek:
            destfile.seek(seek, os.SEEK_SET)

        status = STATUS_WRITING

        i = 0
        while (count == -1) or (count > 0 and status == STATUS_WRITING):
            data = srcfile.read(bs)
            if not len(data):
                break
            destfile.write(data)
            if callback:
                callback(i)
            if len(data) != bs:
                i += len(data)
                break
            if count != -1:
                count -= 1
            i += bs

        if callback:
	        callback(i)

        return i

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
            if isinstance(intem, QtGui.QLayout):
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
                edit = unicode(_self.edit.text())
                if not edit or (not os.path.exists(edit) and not self.reverse):
                    gui.dialog_info(title=missing_file_title, msg=missing_file_msg)
                    return False

                if self.reverse:
                    self.source = unicode(self.usbs[_self.usb_list.currentRow()][0])
                    self.target = unicode(edit)
                    source_size = self.backend.get_device_size(self.source) * 512
                    disk_space = self.backend.get_free_space(os.path.dirname(self.target))
                    if disk_space < source_size:
                        gui.dialog_info(title=_("Insufficient disk space"),
                                    msg=_("The available size on your disk is insufficient. "
                                          "You need more than %d Mo free on your disk to backup your device."
                                          "<br><br>Please free some space and retry.") % ((source_size - disk_space) / 1024 / 1024))
                        return False
                else:
                    self.source = unicode(edit)
                    self.target = unicode(self.usbs[_self.usb_list.currentRow()][0])
                    if self.device_size < self.total_size:
                        gui.dialog_info(title=_("The selected target is too small"),
                                        msg=_("The size of the source you have selected (%d Mo)"
                                              " is bigger than the size of the selected target (%d Mo)."
                                              "<br><br>Please select a source equal or smaller than the target.") % (self.total_size / 1024 / 1024, self.device_size / 1024 / 1024))
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

                sizes = []
                for part in self.parts:
                    sizes.append(self.get_partition_size(part))
                for i, part in enumerate(self.parts):
                    part["size"] = sizes[i]

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

                _self.dest_dir = unicode(filedialog.selectedFiles()[0])
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
                if self.reverse:
                    filedialog.setDefaultSuffix("img")
                if filedialog.exec_() != QtGui.QDialog.Accepted:
                    return
                _self.edit.setText(unicode(filedialog.selectedFiles()[0]))

            def on_refresh(_self):
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
                _self.edit.textChanged.connect(self.on_text_changed)
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
                _self.usb_list.currentRowChanged.connect(self.on_select_device)

                for i in self.usbs:
                    _self.usb_list.addItem(i[1])
                return _self.usb_list

            def create_device_resize_layout(_self):
                layout = QtGui.QVBoxLayout()
                self.resize_label = QtGui.QLabel(_("Partition sizes :<br>You can use the following default values "
                                                   "or you can resize the partition sizes to meet your needs :<br><br>"))
                self.resize_label.setWordWrap(True)
                self.resize_label.setEnabled(False)
                layout.addWidget(self.resize_label)
                self.splitter = splitter = QtGui.QSplitter()
                self.splitter.setMinimumHeight(32)
                self.splitter.setStyleSheet("QSplitter { border: 1px solid black; }")
                self.splitter.splitterMoved.connect(self.splitter_moved)
                self.splitter.setEnabled(False)
                layout.addWidget(splitter)
                return layout

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
                    add_to_layout(layout, _self.create_device_resize_layout())

                _self.setLayout(layout)

        page = BurnPage()
        page.fill_page(False)
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

    def update_progress(self, sectors, total):
        if total:
            gui.app.postEvent(gui.app, gui.UpdateProgressEvent(self.progress, int(sectors / float(total) * 100)))

    def currentIdChanged(self, id):
        if id == self.PAGE_INDEX_BURN:
            self.page(id).fill_page(self.reverse)
            self.button(QtGui.QWizard.NextButton).setEnabled(False)

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
