import gui
from gui_pyqt import WaitWindow
from windowsbackend import WindowsBackend
import subprocess
import os
import sys
import conf
from PyQt4 import QtGui

backend = WindowsBackend()

filedialog = QtGui.QFileDialog(None, "Please select an UFO image", os.getcwd())
filedialog.exec_()
filename = filedialog.selectedFiles()[0]
print filename

if not os.path.exists(filename):
    gui.dialog_info(msg=_("Could not find an UFO image.\nPlease move the file UFO.img to the executable folder"),
                     title=_("Image not found"))
    sys.exit(1)

usb = backend.get_usb_sticks()
names = [ x[1] for x in usb ]
ret = gui.dialog_choices(msg=_("Select the USB device you want to install UFO on"),
                         title="UFO", column=_("Device"), choices= [ _("Cancel") ] + names)
if not ret:
    sys.exit(0)
dev = usb[ret - 1][0]
print dev

# subprocess.call(["dd.exe", "if=UFO.img", "bs=1M", "of=" + dev, "--progress"], shell=True)

conf.IMGDIR = os.getcwd()
WaitWindow(["dd.exe", 'if=' + str(filename), "bs=1M", "of=" + dev, "--progress"],
           "Please wait", "Writing the image to the disk", "Success", "Error").run()