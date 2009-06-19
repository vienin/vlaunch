NAME=vlaunch
VERSION=0.4
SOURCES=settings.conf.* *.py set_xml_attr boot ufo.bmp README COPYING Resources MacOS site.py bootfloppy.img launcher-linux.py QtCoreVBox QtGuiVBox QtNetworkVBox VBoxClientSymlink vboxclientsymlink.desktop VBoxClientDnD vboxclientdnd.desktop

DIR=$(NAME)-$(VERSION)
ARCHIVE=$(DIR).tar.gz
SPECFILE=$(NAME).spec
URL=http://www.glumol.com/chicoutimi/vlaunch

ifneq ($(findstring ../Makefile.mk,$(wildcard ../Makefile.mk)), )
	include ../Makefile.mk
endif

all:

install:
	# build virtual machine xml setting files
	# sleep 5 sec between each vm creation, instead of killing VBoxXp process
	mkdir tmp_vbox_home_linux tmp_vbox_home_windows tmp_vbox_home_macosx  
	./createvm.py -o `pwd`/tmp_vbox_home_linux -v $(VM_NAME)
	sleep 5
	./createvm.py -o `pwd`/tmp_vbox_home_windows -v $(VM_NAME) -s WIN
	sleep 5
	./createvm.py -o `pwd`/tmp_vbox_home_macosx  -v $(VM_NAME) -s MAC
	sleep 5
	
	# build windows tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/HardDisks
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/settings
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/logs
	tar xvzf windows.tgz -C $(DESTDIR)$(TARGET_PATH)/Windows/
	tar xvzf fake_vmdk.tgz -C $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/HardDisks
	# cp $(DESTDIR)$(TARGET_PATH)/Windows/settings.conf $(DESTDIR)$(TARGET_PATH)/Windows/settings/
	rm -f $(DESTDIR)$(TARGET_PATH)/Windows/settings.conf
	cp  settings.conf.win32 $(DESTDIR)$(TARGET_PATH)/Windows/settings/settings.conf
	cp -R tmp_vbox_home_windows/Machines tmp_vbox_home_windows/VirtualBox.xml ufo.bmp $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/
	cp -R tmp_vbox_home_windows/VirtualBox.xml $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/VirtualBox.xml.template
	cp tmp_vbox_home_windows/Machines/UFO/UFO.xml $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/Machines/UFO/UFO.xml.template
	
	# build mac-intel tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/MacOS
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/HardDisks
	tar xvzf mac-intel.tgz -C $(DESTDIR)$(TARGET_PATH)/Mac-Intel
	tar xvzf fake_vmdk.tgz -C $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/HardDisks/
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/HardDisks
	# cp Info.plist PkgInfo $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/
	# cp mac-intel-launcher settings.conf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/MacOS/
	# cp ufo.icns $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Resources/VirtualBoxVM.app/Contents/MacOS
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Resources/VirtualBoxVM.app/Contents/Resources
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Frameworks/QtGuiVBox.framework/QtGuiVBox
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Frameworks/QtCoreVBox.framework/QtCoreVBox
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Frameworks/QtNetworkVBox.framework/QtNetworkVBox
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/lib/python2.5/site.py
	cp Resources MacOS $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Resources/VirtualBoxVM.app/Contents/
	cp QtGuiVBox $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Frameworks/QtGuiVBox.framework/QtGuiVBox
	cp QtCoreVBox $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Frameworks/QtCoreVBox.framework/QtCoreVBox
	cp QtNetworkVBox $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Frameworks/QtNetworkVBox.framework/QtNetworkVBox
	cp site.py $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/lib/python2.5/
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/settings
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/settings.conf
	cp -f settings.conf.mac $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/settings/settings.conf
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/site.pyc
	cp -R tmp_vbox_home_macosx/Machines tmp_vbox_home_macosx/VirtualBox.xml ufo.bmp $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/
	cp tmp_vbox_home_macosx/VirtualBox.xml $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/VirtualBox.xml.template
	cp tmp_vbox_home_macosx/Machines/UFO/UFO.xml $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Machines/UFO/UFO.xml.template
	
	# build linux tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/HardDisks
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/settings
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/bin
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/logs
	tar xvzf fake_vmdk.tgz -C $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/HardDisks
	cp launcher-linux.py $(DESTDIR)$(TARGET_PATH)/Linux/ufo
	cp modifyvm.py linuxbackend.py launcher.py createrawvmdk.py easygui.py conf.py utils.py $(DESTDIR)$(TARGET_PATH)/Linux/bin
	cp settings.conf.linux $(DESTDIR)$(TARGET_PATH)/Linux/settings/settings.conf
	cp -R tmp_vbox_home_linux/Machines tmp_vbox_home_linux/VirtualBox.xml ufo.bmp $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/
	cp tmp_vbox_home_linux/VirtualBox.xml $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/VirtualBox.xml.template
	cp tmp_vbox_home_linux/Machines/UFO/UFO.xml $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/Machines/UFO/UFO.xml.template
	
	# installs Boot Isos
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/Isos
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Isos
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/Isos
	cp UFO-VirtualBox-boot-windows.img $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/Isos/UFO-VirtualBox-boot.img
	cp UFO-VirtualBox-boot-mac.img $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Isos/UFO-VirtualBox-boot.img
	cp UFO-VirtualBox-boot-linux.img $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/Isos/UFO-VirtualBox-boot.img

	# Kit de survie
	cp "Kit de survie.pdf" $(DESTDIR)$(TARGET_PATH)

	# shared folders automount and links
	mkdir -p $(DESTDIR)/usr/bin
	mkdir -p $(DESTDIR)/etc/xdg/autostart
	chmod +x VBoxClientSymlink
	chmod +x VBoxClientDnD
	cp VBoxClientSymlink $(DESTDIR)/usr/bin
	cp vboxclientsymlink.desktop $(DESTDIR)/etc/xdg/autostart
	cp VBoxClientDnD $(DESTDIR)/usr/bin
	cp vboxclientdnd.desktop $(DESTDIR)/etc/xdg/autostart
	
