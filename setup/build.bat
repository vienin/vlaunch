set VBOX_PATH=F:\vbox\out\win.x86\release\bin
set QT_PATH=F:\Qt\4.5.2\bin
set OLDPATH=%PATH%
set PATH=%QT_PATH%;%PATH%;%VBOX_PATH%;
cmd /C comregister.cmd
set PATH=%OLDPATH%
del /F /Q /S dist build
copy ..\src\launcher.py ..\src\ufo.py
del ..\src\subprocess.py*
setup.py py2exe --custom-boot-script custom-boot-script.py
copy %QT_PATH%\QtNetwork*.dll dist\bin
rem copy dist\ufo.exe ..\setup\dist
rem cd ..\setup
rem copy ufo.exe.manifest dist
rem mkdir dist\settings
rem mkdir dist\.VirtualBox
rem copy settings.conf dist\settings\settings.conf
rem copy ..\graphics\ufo-generic.png dist\.VirtualBox
rem copy ..\graphics\ufo-generic.bmp dist\.VirtualBox
rem copy ..\graphics\updater-install.png dist\.VirtualBox
rem copy ..\graphics\updater-download.png dist\.VirtualBox
cd dist
rename launcher.exe ufo.exe
mkdir bin
xcopy /E /Y "%VBOX_PATH%\*" bin\
del /F /Q /S bin\tst*.*
del /F /Q /S bin\testcase
rmdir bin\testcase
mkdir bin\drivers
mkdir bin\drivers\VBoxDrv
mkdir bin\drivers\network
mkdir bin\drivers\network\netflt
move /Y bin\VBoxDrv.sys bin\drivers\VBoxDrv
copy "E:\Program Files\Microsoft Visual Studio .NET 2003\SDK\v1.1\Bin\msvc*.dll" bin
copy "E:\Program Files\Microsoft Visual Studio .NET 2003\SDK\v1.1\Bin\msvc*.dll" .
C:\Python25\python.exe -c  "import glob, tarfile; tar = tarfile.open('windows.tgz', 'w:gz'); map(tar.add, glob.glob('*.dll')); tar.add('ufo.exe'); tar.add('bin'); tar.close();"
cd ..
pscp.exe -i id_rsa.ppk dist\ufo.exe dist\windows.tgz bob@kickstart.agorabox.org:/var/www/html/private/virtualization
rem pscp.exe -i id_rsa.ppk dist\ufo.exe bob@kickstart.agorabox.org:/var/www/html/private/virtualization
