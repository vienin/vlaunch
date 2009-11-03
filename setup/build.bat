set VBOX_PATH=F:\VirtualBox-3.0.4_OSE\out\win.x86\release\bin
set OLDPATH=%PATH%
set PATH=F:\Qt\4.5.2\bin;%PATH%;%VBOX_PATH%;
cmd /C comregister.cmd
set PATH=%OLDPATH%
del /F /Q /S dist build
copy ..\src\launcher.py ..\src\ufo.py
del ..\src\subprocess.py*
setup.py py2exe
rem copy ufo.exe.manifest dist
mkdir dist\settings
mkdir dist\.VirtualBox
copy settings.conf dist\settings\settings.conf
copy ..\graphics\ufo-generic.png dist\.VirtualBox
copy ..\graphics\ufo-generic.bmp dist\.VirtualBox
copy ..\graphics\updater-install.png dist\.VirtualBox
copy ..\graphics\updater-download.png dist\.VirtualBox
rem mt -inputresource:dist\ufo.exe;#1 -manifest ufo.exe.manifest -outputresource:dist\ufo.exe;#1
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
rem copy /Y ..\..\tools\drivers\snetcfg_x86.exe bin
copy "E:\Program Files\Microsoft Visual Studio .NET 2003\SDK\v1.1\Bin\msvc*.dll" bin
copy "E:\Program Files\Microsoft Visual Studio .NET 2003\SDK\v1.1\Bin\msvc*.dll" .
C:\Python25\python.exe -c  "import glob, tarfile; tar = tarfile.open('windows.tgz', 'w:gz'); map(tar.add, glob.glob('*.dll')); tar.add('ufo.exe'); tar.add('bin'); tar.close();"
cd ..
pscp.exe -i id_rsa.ppk dist\ufo.exe dist\windows.tgz bob@kickstart.agorabox.org:/var/www/html/private/virtualization
rem pscp.exe -i id_rsa.ppk dist\ufo.exe bob@kickstart.agorabox.org:/var/www/html/private/virtualization
