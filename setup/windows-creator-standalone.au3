; UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
;
; Copyright (c) 2008-2010 Agorabox, Inc.
;
; This is free software; you can redistribute it and/or modify it
; under the terms of the GNU General Public License as published by
; the Free Software Foundation; either version 2 of the License, or
; (at your option) any later version.
;
; This program is distributed in the hope that it will be useful, but
; WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
; General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with this program; if not, write to the Free Software
; Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

#RequireAdmin

$tempdir = @TempDir & "\ufo-creator"

If FileExists ($tempdir) Then
    DirRemove ($tempdir , 1)
EndIf

DirCreate ($tempdir & "\bin\Microsoft.VC90.CRT")
DirCreate ($tempdir & "\.data\images")
DirCreate ($tempdir & "\.data\logs")
DirCreate ($tempdir & "\.data\settings")

; UFO components
FileInstall("dist\bin\ufo.x86.exe", $tempdir & "\bin\ufo.x86.exe")
FileInstall("dist\bin\library.zip", $tempdir & "\bin\library.zip")
FileInstall("dist\bin\python26.dll", $tempdir & "\bin\python26.dll")
FileInstall("dist\bin\pythoncom26.dll", $tempdir & "\bin\pythoncom26.dll")
FileInstall("dist\bin\pywintypes26.dll", $tempdir & "\bin\pywintypes26.dll")

; Qt dependencies
FileInstall("dist\bin\QtCore4.dll", $tempdir & "\bin\QtCore4.dll")
FileInstall("dist\bin\QtGui4.dll", $tempdir & "\bin\QtGui4.dll")
FileInstall("dist\bin\QtNetwork4.dll", $tempdir & "\bin\QtNetwork4.dll")
FileInstall("dist\bin\PyQt4.QtNetwork.pyd", $tempdir & "\bin\PyQt4.QtNetwork.pyd")
FileInstall("dist\bin\PyQt4.QtGui.pyd", $tempdir & "\bin\PyQt4.QtGui.pyd")
FileInstall("dist\bin\PyQt4.QtCore.pyd", $tempdir & "\bin\PyQt4.QtCore.pyd")

; Microsoft dependencies
FileInstall("dist\bin\Microsoft.VC90.CRT\Microsoft.VC90.CRT.manifest", $tempdir & "\bin\Microsoft.VC90.CRT\Microsoft.VC90.CRT.manifest")
FileInstall("dist\bin\Microsoft.VC90.CRT\msvcm90.dll", $tempdir & "\bin\Microsoft.VC90.CRT\msvcm90.dll")
FileInstall("dist\bin\Microsoft.VC90.CRT\msvcp90.dll", $tempdir & "\bin\Microsoft.VC90.CRT\msvcp90.dll")
FileInstall("dist\bin\Microsoft.VC90.CRT\msvcr90.dll", $tempdir & "\bin\Microsoft.VC90.CRT\msvcr90.dll")

; Python binaries
FileInstall("dist\bin\win32wnet.pyd", $tempdir & "\bin\win32wnet.pyd")
FileInstall("dist\bin\win32ui.pyd", $tempdir & "\bin\win32ui.pyd")
FileInstall("dist\bin\win32trace.pyd", $tempdir & "\bin\win32trace.pyd")
FileInstall("dist\bin\win32pipe.pyd", $tempdir & "\bin\win32pipe.pyd")
FileInstall("dist\bin\win32file.pyd", $tempdir & "\bin\win32file.pyd")
FileInstall("dist\bin\win32evtlog.pyd", $tempdir & "\bin\win32evtlog.pyd")
FileInstall("dist\bin\win32event.pyd", $tempdir & "\bin\win32event.pyd")
FileInstall("dist\bin\win32api.pyd", $tempdir & "\bin\win32api.pyd")
FileInstall("dist\bin\unicodedata.pyd", $tempdir & "\bin\unicodedata.pyd")
FileInstall("dist\bin\sip.pyd", $tempdir & "\bin\sip.pyd")
FileInstall("dist\bin\select.pyd", $tempdir & "\bin\select.pyd")
FileInstall("dist\bin\bz2.pyd", $tempdir & "\bin\bz2.pyd")
FileInstall("dist\bin\_win32sysloader.pyd", $tempdir & "\bin\_win32sysloader.pyd")
FileInstall("dist\bin\_ssl.pyd", $tempdir & "\bin\_ssl.pyd")
FileInstall("dist\bin\_socket.pyd", $tempdir & "\bin\_socket.pyd")
FileInstall("dist\bin\_hashlib.pyd", $tempdir & "\bin\_hashlib.pyd")
FileInstall("dist\bin\_ctypes.pyd", $tempdir & "\bin\_ctypes.pyd")

; Usefull datas
FileInstall("settings.conf", $tempdir & "\.data\settings\settings.conf")
FileInstall("..\graphics\UFO.png", $tempdir & "\.data\images\UFO.png")
FileInstall("..\graphics\graphics.png", $tempdir & "\.data\images\graphics.png")
FileInstall("..\graphics\reload.png", $tempdir & "\.data\images\reload.png")

; Translations
DirCreate ($tempdir & "\.data\locale\fr\LC_MESSAGES")
FileInstall("..\locale\vlaunch\fr.mo", $tempdir & "\.data\locale\fr\LC_MESSAGES\vlaunch.mo")

Run($tempdir & "\bin\ufo.x86.exe --dd", @ScriptDir)
