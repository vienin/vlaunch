del /F /Q /S dist build
setup.py py2exe
copy settings.conf.win32 dist\settings.conf
cd dist
rename launcher.exe ufo.exe
mkdir bin
xcopy /E /Y "E:\vbox\out\win.x86\release\bin\*" bin\
copy ..\snetcfg_x86.exe bin
C:\Python25\python.exe -c  "import tarfile; tar = tarfile.open('windows.tgz', 'w:gz'); tar.add('settings.conf'); tar.add('ufo.exe'); tar.add('bin'); tar.close();"
cd ..
pscp.exe dist\windows.tgz bob@kickstart.agorabox.org:/var/www/html/private/virtualization/windows.tgz
