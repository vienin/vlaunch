@echo off
@echo PROCESSOR_ARCHITECTURE: %PROCESSOR_ARCHITECTURE%

del /F /Q /S dist build

set PRODUCT_NAME=Gdium Mobile PC

if %PROCESSOR_ARCHITECTURE% == x86    goto x86
if %PROCESSOR_ARCHITECTURE% == AMD64  goto amd64

:x86
set VBOX_PATH=F:\gitorious\vbox

set VBOX_BIN_PATH=%VBOX_PATH%\out\win.x86\release\bin
set QT_BIN_PATH=%VBOX_PATH%\tools\win.x86\Qt\4.5.2-32bits\bin
set MSVC_PATH="E:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT"
set VBOX_BIN_DEST=bin\
set SETUP_SCRIPT="setup.py"
set SIGNTOOL_PATH=F:\6000\bin\SelfSign

"C:\Program Files\AutoIt3\Aut2Exe\Aut2exe.exe" /in windows-launcher-link.au3 /out dist\"%PRODUCT_NAME%.exe" /icon ../graphics/UFO.ico
"C:\Program Files\AutoIt3\Aut2Exe\Aut2exe.exe" /in windows-settings-link.au3 /out dist\"%PRODUCT_NAME% options.exe" /icon ../graphics/setting.ico
"C:\Program Files\AutoIt3\Aut2Exe\Aut2exe.exe" /in windows-creator-link.au3 /out dist\"%PRODUCT_NAME% creator.exe" /icon ../graphics/creator.ico

goto begin

:amd64
set VBOX_PATH=C:\Users\agorabox\Desktop\vbox

set VBOX_BIN_PATH=%VBOX_PATH%\out\win.amd64\release\bin
set QT_BIN_PATH=%VBOX_PATH%\tools\win.x86\Qt\4.5.2-64bits\bin
set VBOX_BIN_DEST="."
set SIGNTOOL_PATH=c:\WinDDK\7600.16385.1\bin\amd64\

set SETUP_SCRIPT="setup-64bits.py"

goto begin

@echo Unsupported platform...
goto end

:begin
set OLDPATH=%PATH%
set PATH=%PATH%;%VBOX_BIN_PATH%;%QT_BIN_PATH%;%VBOX_BIN_PATH%\Microsoft.VC80.CRT;E:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT

cmd /C comregister.cmd

c:\Python26\python.exe "%SETUP_SCRIPT%" py2exe
rem --custom-boot-script custom-boot-script.py

cd dist

mkdir %VBOX_BIN_DEST%\update
mkdir %VBOX_BIN_DEST%\update_cd
mkdir %VBOX_BIN_DEST%\custom_clamav\
xcopy /E /Y ..\..\clamav\src\update_cd  %VBOX_BIN_DEST%\update_cd\
xcopy /E /Y ..\..\clamav\src\custom_clamav\*.dll  %VBOX_BIN_DEST%\custom_clamav\
xcopy /E /Y ..\..\clamav\src\custom_clamav\*.pyd  %VBOX_BIN_DEST%\custom_clamav\
mkdir "%VBOX_BIN_DEST%\Microsoft.VC90.CRT"
xcopy /E /Y %MSVC_PATH% %VBOX_BIN_DEST%\Microsoft.VC90.CRT\

xcopy /E /Y "%VBOX_BIN_PATH%\*"  %VBOX_BIN_DEST%
copy %QT_BIN_PATH%\QtNetwork4.dll  %VBOX_BIN_DEST%
copy %QT_BIN_PATH%\QtOpenGL4.dll  %VBOX_BIN_DEST%

del /F /Q /S %VBOX_BIN_DEST%\tst*.*
del /F /Q /S %VBOX_BIN_DEST%\testcase

rmdir %VBOX_BIN_DEST%\testcase
mkdir %VBOX_BIN_DEST%\drivers
mkdir %VBOX_BIN_DEST%\drivers\VBoxDrv
move /Y %VBOX_BIN_DEST%\VBoxDrv.sys %VBOX_BIN_DEST%\drivers\VBoxDrv
move /Y %VBOX_BIN_DEST%\launcher.exe %VBOX_BIN_DEST%\ufo.%PROCESSOR_ARCHITECTURE%.exe

if "%1%" == "creator"  goto buildcreator 

:sign
%SIGNTOOL_PATH%\signtool sign /v /ac %VBOX_PATH%\tools\win.x86\cert\MSCV-GlobalSign.cer /s my /n "Agorabox" %VBOX_BIN_DEST%\ufo.%PROCESSOR_ARCHITECTURE%.exe
%SIGNTOOL_PATH%\signtool sign /v /ac %VBOX_PATH%\tools\win.x86\cert\MSCV-GlobalSign.cer /s my /n "Agorabox" "%PRODUCT_NAME%.exe" "%PRODUCT_NAME% options.exe" "%PRODUCT_NAME% creator.exe"
if "%1" == "creator"  %SIGNTOOL_PATH%\signtool sign /v /ac %VBOX_PATH%\tools\win.x86\cert\MSCV-GlobalSign.cer /s my /n "Agorabox" "..\%PRODUCT_NAME% creator.exe"

C:\Python26\python.exe -c  "import glob, tarfile; tar = tarfile.open('..\windows.%PROCESSOR_ARCHITECTURE%.tgz', 'w:gz'); tar.add('.'); tar.close();"

cd ..
pscp.exe windows.%PROCESSOR_ARCHITECTURE%.tgz "%PRODUCT_NAME% creator.exe" bob@kickstart.alpha.agorabox.org:/var/www/html/private/virtualization
rem pscp.exe -i id_rsa.ppk dist\ufo.exe bob@kickstart.agorabox.org:/var/www/html/private/virtualization

goto end

:buildcreator
@echo Building standalone creator
del /F /Q /S messages.mo
..\pygettext.py -o ..\..\locale\vlaunch\vlaunch.pot ..\..\locale\vlaunch ..\..\src
for %%f in (..\..\locale\vlaunch\*.po) do "c:\Program Files\GnuWin32\bin\msgmerge.exe" --update "%%f" ..\..\locale\vlaunch\vlaunch.pot
for %%f in (..\..\locale\vlaunch\*.po) do ..\msgfmt.py "%%f"
"C:\Program Files\AutoIt3\Aut2Exe\Aut2exe.exe"  /in ../windows-creator-standalone.au3 /out "..\%PRODUCT_NAME% creator.exe" /icon ../../graphics/creator.ico

goto sign

:end

