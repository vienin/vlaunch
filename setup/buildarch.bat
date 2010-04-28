@echo off
@echo PROCESSOR_ARCHITECTURE: %PROCESSOR_ARCHITECTURE%

set VBOX_PATH=C:\vbox

del /F /Q /S dist build

if %PROCESSOR_ARCHITECTURE% == x86    goto x86
if %PROCESSOR_ARCHITECTURE% == AMD64  goto amd64

:x86
set VBOX_BIN_PATH=%VBOX_PATH%\out\win.x86\release\bin
set QT_BIN_PATH=%VBOX_PATH%\tools\win.x86\Qt\4.5.2-32bits\bin
set VBOX_BIN_DEST="bin\"
set SETUP_SCRIPT="setup.py"

c:\Python26\python.exe setup-arch-dispatcher.py py2exe

goto begin

:amd64
set VBOX_BIN_PATH=%VBOX_PATH%\out\win.amd64\release\bin
set QT_BIN_PATH=%VBOX_PATH%\tools\win.x86\Qt\4.5.2-64bits\bin
set VBOX_BIN_DEST="."

set SETUP_SCRIPT="setup-64bits.py"

goto begin

@echo Unsupported platform...
goto end

:begin

set OLDPATH=%PATH%
set PATH=%PATH%;%VBOX_BIN_PATH%;%QT_BIN_PATH%;%VBOX_BIN_PATH%\Microsoft.VC80.CRT

cmd /C comregister.cmd

c:\Python26\python.exe "%SETUP_SCRIPT%" py2exe
rem --custom-boot-script custom-boot-script.py

cd dist

xcopy /E /Y "%VBOX_BIN_PATH%\*"  %VBOX_BIN_DEST%
copy %QT_BIN_PATH%\QtNetwork4.dll  %VBOX_BIN_DEST%

del /F /Q /S %VBOX_BIN_DEST%\tst*.*
del /F /Q /S %VBOX_BIN_DEST%\testcase

rmdir %VBOX_BIN_DEST%\testcase
mkdir %VBOX_BIN_DEST%\drivers
mkdir %VBOX_BIN_DEST%\drivers\VBoxDrv
move /Y %VBOX_BIN_DEST%\VBoxDrv.sys %VBOX_BIN_DEST%\drivers\VBoxDrv
move /Y %VBOX_BIN_DEST%\launcher.exe %VBOX_BIN_DEST%\ufo.%PROCESSOR_ARCHITECTURE%.exe
move /Y launcher-windows.exe ufo.exe

C:\Python26\python.exe -c  "import glob, tarfile; tar = tarfile.open('..\windows.%PROCESSOR_ARCHITECTURE%.tgz', 'w:gz'); tar.add('.'); tar.close();"

cd ..
pscp.exe -i id_rsa.ppk windows.%PROCESSOR_ARCHITECTURE%.tgz vienin@kickstart.alpha.agorabox.org:/var/www/html/private/virtualization
rem pscp.exe -i id_rsa.ppk dist\ufo.exe bob@kickstart.agorabox.org:/var/www/html/private/virtualization

:end
