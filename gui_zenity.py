import subprocess

zenity = subprocess.Popen(["which", "zenity"], stdout=subprocess.PIPE).communicate()[0]
if not os.path.lexists(zenity):
    raise "Could not find 'zenity'"

def set_icon(icon_path):
    pass

def dialog_info(title, msg, error = False):
    subprocess.call([ zenity, "--info", "--title=" + title, "--text" + msg ])

def dialog_question(title, msg, button1, button2):
    return (button1, button2)[ subprocess.call([ zenity, "--question", "--title=" + title, "--text" + msg ])]

# generic dialog box for ask password 
# params :
# return : pass_string
def dialog_password(root=None):
    return subprocess.Popen([ zenity, "--entry", "--title", 'Autorisation nécessaire',
                              "--text", 'Veuillez entrer votre mot de passe:',
                              "--entry-text", '', "--hide-text" ],
                            stdout=subprocess.PIPE).communicate()[0]


def SplashScreen(*args):
    print "Impossible d'afficher un splash screen avec zenity"
    pass


def dialog_error_report(*args):
    pass
