del /F /Q /S dist build
setup.py py2exe
setup_updater.py py2exe
copy settings.conf.win32 dist\settings.conf
cd dist
rename launcher.exe ufo.exe
mkdir bin
xcopy /E /Y "E:\vbox\out\win.x86\release\bin\*" bin\
move /Y updater.exe bin
mkdir bin\drivers
mkdir bin\drivers\VBoxDrv
mkdir bin\drivers\network
mkdir bin\drivers\network\netflt
move /Y bin\VBoxDrv.sys bin\drivers\VBoxDrv
copy /Y ..\snetcfg_x86.exe bin
C:\Python25\python.exe -c  "import glob, tarfile; tar = tarfile.open('windows.tgz', 'w:gz'); map(tar.add, glob.glob('*.dll')); tar.add('ufo.exe'); tar.add('tcl'); tar.add('bin'); tar.close();"
cd ..
pscp.exe dist\windows.tgz bob@kickstart.agorabox.org:/var/www/html/private/virtualization/windows.tgz
