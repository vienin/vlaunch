import easygui

def dialog_info(title, msg):
    easygui.msgbox(msg=msg, title=title)

def dialog_question(title, msg, button1, button2):
    choices = [ button1, button2 ]
    reply = easygui.buttonbox(msg, title, choices=choices)
    return reply

# generic dialog box for ask password 
# params :
# return : pass_string
def dialog_password(root=None):
    return easygui.passwordbox(msg="Veuillez entrer le mot de passe de cet ordinateur", root=root)

