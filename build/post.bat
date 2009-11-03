copy out\win.x86\release\obj\VBoxManage\VBoxManage.exe.manifest out\win.x86\release\bin\
copy out\win.x86\release\obj\VirtualBox\VirtualBox.exe.manifest out\win.x86\release\bin\
copy out\win.x86\release\obj\VBoxSVC\VBoxSVC.exe.manifest out\win.x86\release\bin\
copy out\win.x86\release\obj\VBoxSDL\VBoxSDL.exe.manifest out\win.x86\release\bin\
copy out\win.x86\release\obj\VBoxNetDHCP\VBoxNetDHCP.exe.manifest out\win.x86\release\bin\
copy out\win.x86\release\obj\VBoxHeadless\VBoxHeadless.exe.manifest out\win.x86\release\bin\
copy "C:\Program Files\Microsoft Visual Studio 8\VC\redist\x86\Microsoft.VC80.CRT\*.*" out\win.x86\release\bin\
copy out\win.x86\release\bin\
mt -manifest out\win.x86\release\obj\VBoxC\VBoxC.dll.manifest -outputresource:out\win.x86\release\bin\VBoxC.dll;1
mt -manifest out\win.x86\release\obj\VBoxRT\VBoxRT.dll.manifest -outputresource:out\win.x86\release\bin\VBoxRT.dll;1
copy out\win.x86\release\obj\VBoxRT\VBoxRT.dll.manifest out\win.x86\release\bin\
; mt.exe -inputresource:out\win.x86\release\bin\VBoxRT.dll;#1 -manifest out\win.x86\release\obj\VBoxRT\VBoxRT.dll.manifest -outputresource:out\win.x86\release\bin\VBoxRT.dll;#3

copy E:\Qt\4.5.1\bin\QtCore4.dll out\win.x86\release\bin\
copy E:\Qt\4.5.1\bin\QtNetwork4.dll out\win.x86\release\bin\
copy E:\Qt\4.5.1\bin\QtGui4.dll out\win.x86\release\bin\
