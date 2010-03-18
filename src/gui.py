# UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
#
# Copyright (c) 2008-2009 Agorabox, Inc.
#
# This is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA. 


import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

try:
    from gui_pyqt import *
    backend = "PyQt"
    print "Using PyQt backend"
    gui = "PyQt4"

except:
    try:
        from gui_zenity import *
        backend = "Zenity"
        print "Using zenity backend"
        gui = "Zenity"
        
    except:
        if False:
            try:
                from gui_tk_ import *
                backend = "Tk"
                print "Using Tk backend"
                gui = "Tk"
                
            except Exception, e:
                print "Didn't find a gui backend..."
                backend = ""
        else:
            raise "Didn't find a gui backend... (Tk backend deprecated)"
            backend = ""
        

if __name__ == "__main__":
    app.initialize_tray_icon()
    app.process_gui_events()
    conf.USER = "ufo"
    app.show_balloon_progress(title="Demarrage",
                              msg=u"UFO est en cours de demarrage.",
                              credentials=True,
                              keyring=False)
        
    #balloon = BalloonMessage(None, "Title", "Do you Glumol ?", timeout=10000, credentials=(lambda x, y: x))
    times = 0
    interval = 0.05
    import time
    while times < 10:
        time.sleep(interval)
        times += interval
        app.process_gui_events()

    #app.exec_()
    #balloon.setAnchor(QtCore.QPoint(100, 100))
    #balloon.showMessage(timeout=5000)
    #app.exec_()
    print dialog_choices(title="Title", msg="Messages", column="Objects",
                         choices = [ "a", "b", "c" ])
    dialog_question("Titre", "Message")
    dialog_info("Titre", "Message")
    print dialog_password(msg="Merci d'entrer votre mot de passe")
    download_file("http://www.glumol.com", "toto")
    splash = SplashScreen(image="ufo-generic.png")
    wait_command([ "sleep", "3" ])
    import time
    time.sleep(2)
