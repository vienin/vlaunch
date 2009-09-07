set VBOX_PATH=F:\VirtualBox-3.0.4_OSE\out\win.x86\release\bin
set OLDPATH=%PATH%
set PATH=%PATH%;%VBOX_PATH%
cmd /C comregister.cmd
set PATH=%OLDPATH%
del /F /Q /S dist build
copy launcher.py ufo.py
del subprocess.py*
setup.py py2exe
setup_updater.py py2exe
rem copy ufo.exe.manifest dist
mkdir dist\settings
copy settings.conf.win32 dist\settings\settings.conf
copy ufo-generic.gif dist\.VirtualBox
copy ufo-generic.bmp dist\.VirtualBox
copy updater-install.gif dist\.VirtualBox
copy updater-download.gif dist\.VirtualBox
rem mt -inputresource:dist\ufo.exe;#1 -manifest ufo.exe.manifest -outputresource:dist\ufo.exe;#1
cd dist
rename launcher.exe ufo.exe
mkdir bin
xcopy /E /Y "%VBOX_PATH%\*" bin\
move /Y ufo-updater.exe bin
mkdir bin\drivers
mkdir bin\drivers\VBoxDrv
mkdir bin\drivers\network
mkdir bin\drivers\network\netflt
move /Y bin\VBoxDrv.sys bin\drivers\VBoxDrv
copy /Y ..\snetcfg_x86.exe bin
C:\Python25\python.exe -c  "import glob, tarfile; tar = tarfile.open('windows.tgz', 'w:gz'); map(tar.add, glob.glob('*.dll')); tar.add('ufo.exe'); tar.add('bin'); tar.close();"
cd ..
pscp.exe -i id_rsa.ppk dist\ufo.exe dist\windows.tgz bob@kickstart.agorabox.org:/var/www/html/private/virtualization
