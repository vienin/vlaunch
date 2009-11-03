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


import easygui
from Tkinter import Tk, Image, PhotoImage, Toplevel, FLAT, NW, Canvas
import Tix

tk = Tkinter.Tk()
tk.withdraw()

def dialog_info(title, msg, error = False):
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

class SplashScreen(Toplevel):
    def __init__(self, master, image=None, timeout=1000):
        """(master, image, timeout=1000) -> create a splash screen
        from specified image file.  Keep splashscreen up for timeout
        milliseconds"""
        
        Toplevel.__init__(self, master, relief=FLAT, borderwidth=0)
        if master == None: master = Tk()
        self.main = master
        if self.main.master != None: # Why ?
            self.main.master.withdraw()
        self.main.withdraw()
        self.overrideredirect(1)
        self.image = PhotoImage(file=image)
        self.after_idle(self.centerOnScreen)

        self.update()
        if (timeout != 0): self.after(timeout, self.destroy)

    def centerOnScreen(self):
        self.update_idletasks()
        width, height = self.width, self.height = \
                        self.image.width(), self.image.height()

        xmax = self.winfo_screenwidth()
        ymax = self.winfo_screenheight()

        x0 = self.x0 = xmax/2 - width/2
        y0 = self.y0 = ymax/2 - height/2
        
        self.geometry("%dx%d+%d+%d" % (width, height, x0, y0))
        self.createWidgets()

    def createWidgets(self):
        self.canvas = Canvas(self, width=self.width, height=self.height)
        self.canvas.create_image(0,0, anchor=NW, image=self.image)
        self.canvas.pack()

    def destroy(self):
        # self.main.update()
        # self.main.deiconify()
        self.main.withdraw()
        self.withdraw()


