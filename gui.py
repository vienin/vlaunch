import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

try:
    from gui_pyqt import *
    backend = "PyQt"
    print "Using PyQt backend"
    gui = "PyQt4"
except:
    raise
    try:
        from gui_tk_ import *
        backend = "Tk"
        print "Using Tk backend"
        gui = "Tk"
    except:
        try:
            from gui_zenity import *
            backend = "Zenity"
            print "Using zenity backend"
            gui = "Zenity"
        except Exception, e:
            print "Didn't find a gui backend..."
            backend = ""

if __name__ == "__main__":
    print dialog_choices(title="Title", msg="Messages", column="Objects",
                         choices = [ "a", "b", "c" ])
    dialog_question("Titre", "Message")
    dialog_info("Titre", "Message")
    print dialog_password()
    download_file("http://www.glumol.com", "toto")
    splash = SplashScreen(image="ufo-generic.png")
    import time
    time.sleep(5)
