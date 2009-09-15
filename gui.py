import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

try:
    from gui_pyqt import *
    backend = "PyQt"
    logging.warning("Using PyQt backend")
except:
    raise
    try:
        from gui_tk import *
        backend = "Tk"
        logging.debug("Using Tk backend")
    except:
        try:
            from gui_zenity import *
            backend = "Zenity"
            logging.debug("Using zenity backend")
        except:
            logging.debug("Didn't find a gui backend...")
            backend = ""

if __name__ == "__main__":
    dialog_question("Titre", "Message")
    dialog_info("Titre", "Message")
    print dialog_password()
    download_file("http://www.glumol.com", "toto")
    splash = SplashScreen(image="ufo-generic.gif")
    import time
    time.sleep(5)
