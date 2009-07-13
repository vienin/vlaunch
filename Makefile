NAME=vlaunch
VERSION=0.5
SOURCES=settings.conf.* *.py set_xml_attr boot ufo-*.bmp ufo-*.gif README COPYING \
        Resources MacOS site.py bootfloppy.img launcher-linux.py QtCoreVBox \
        QtGuiVBox QtNetworkVBox vbox-client-symlink.desktop \
        vbox-client-dnd.desktop Headers Current 4.0 QtCore QtGui \
        QtGui.Resources QtNetwork QtNetwork.framework \
        QtCore.framework QtGui.framework \
        vbox-client-dnd vbox-client-dnd.pam vbox-client-dnd.console \
        vbox-client-symlink vbox-client-symlink.pam vbox-client-symlink.console \
        autorun.inf UFO.ico DS_Store .background .autorun

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
	./createswap.py -o `pwd`/tmp_vbox_home_linux -n ufo_swap.vdi -c settings.conf.linux
	./createvm.py -o `pwd`/tmp_vbox_home_linux -v $(VM_NAME) 
	sleep 5
	./createswap.py -o `pwd`/tmp_vbox_home_windows -n ufo_swap.vdi -c settings.conf.win32
	./createvm.py -o `pwd`/tmp_vbox_home_windows -v $(VM_NAME) -s WIN
	sleep 5
	./createswap.py -o `pwd`/tmp_vbox_home_macosx -n ufo_swap.vdi -c settings.conf.mac
	./createvm.py -o `pwd`/tmp_vbox_home_macosx  -v $(VM_NAME) -s MAC
	sleep 5
	
	# build windows tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/HardDisks
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/settings
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/logs
	tar xvzf windows.tgz -C $(DESTDIR)$(TARGET_PATH)/Windows/
	# cp $(DESTDIR)$(TARGET_PATH)/Windows/settings.conf $(DESTDIR)$(TARGET_PATH)/Windows/settings/
	rm -f $(DESTDIR)$(TARGET_PATH)/Windows/settings.conf
	cp settings.conf.win32 $(DESTDIR)$(TARGET_PATH)/Windows/settings/settings.conf
	cp tmp_vbox_home_windows/HardDisks/ufo_swap.vdi $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/HardDisks/
	cp -R tmp_vbox_home_windows/Machines tmp_vbox_home_windows/VirtualBox.xml ufo-*.bmp ufo-*.gif $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/
	cp tmp_vbox_home_windows/Machines/UFO/UFO.xml $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/Machines/UFO/UFO.xml.template
	cp autorun.inf $(DESTDIR)$(TARGET_PATH)/
	cp UFO.ico $(DESTDIR)$(TARGET_PATH)/.UFO.ico
	
	# build mac-intel tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/MacOS
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/Updater.app/Contents/MacOS
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/HardDisks
	tar xvzf mac-intel.tgz -C $(DESTDIR)$(TARGET_PATH)/Mac-Intel
	tar xvzf fake_vmdk.tgz -C $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/HardDisks/
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/HardDisks
	cp tmp_vbox_home_macosx/HardDisks/ufo_swap.vdi $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/HardDisks/
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Resources/VirtualBoxVM.app/Contents/MacOS
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Resources/VirtualBoxVM.app/Contents/Resources
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/lib/python2.5/site.py
	unlink $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/Updater.app/Contents/Resources/lib/python2.5/site.py
	cp Resources MacOS $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Resources/VirtualBoxVM.app/Contents/

	find $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework -type l -exec unlink {} \;

	cp Headers $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtCore.framework/Headers
	cp QtCore $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtCore.framework/QtCore
	cp 4.0 Current $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtCore.framework/Versions

	cp Headers $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtGui.framework/Headers
	cp QtGui $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtGui.framework/QtGui
	cp QtGui.Resources $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtGui.framework/Resources
	cp 4.0 Current $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtGui.framework/Versions

	cp Headers $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtNetwork.framework/Headers
	cp QtNetwork $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtNetwork.framework/QtNetwork
	cp 4.0 Current $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Framework/QtNetwork.framework/Versions

	cp QtCore.framework QtGui.framework QtNetwork.framework $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/MacOS

	cp site.py $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/lib/python2.5/
	cp site.py $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/Updater.app/Contents/Resources/lib/python2.5/
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/settings
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/settings.conf
	cp -f settings.conf.mac $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/settings/settings.conf
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/site.pyc
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/Updater.app/Contents/Resources/site.pyc
	cp -R tmp_vbox_home_macosx/Machines tmp_vbox_home_macosx/VirtualBox.xml ufo-*.bmp ufo-*.gif $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/
	cp tmp_vbox_home_macosx/Machines/UFO/UFO.xml $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Machines/UFO/UFO.xml.template

	mkdir $(DESTDIR)$(TARGET_PATH)/.background
	cp ufo.png $(DESTDIR)$(TARGET_PATH)/.background
	cp DS_Store $(DESTDIR)$(TARGET_PATH)/.DS_Store
	
	# build linux tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/HardDisks
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/settings
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/bin
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/logs
	tar xvzf fake_vmdk.tgz -C $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/HardDisks
	cp tmp_vbox_home_linux/HardDisks/ufo_swap.vdi $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/HardDisks
	cp launcher-linux.py $(DESTDIR)$(TARGET_PATH)/Linux/ufo
	cp modifyvm.py linuxbackend.py launcher.py updater.py createrawvmdk.py easygui.py conf.py utils.py $(DESTDIR)$(TARGET_PATH)/Linux/bin
	cp settings.conf.linux $(DESTDIR)$(TARGET_PATH)/Linux/settings/settings.conf
	cp -R tmp_vbox_home_linux/Machines tmp_vbox_home_linux/VirtualBox.xml ufo-*.bmp ufo-*.gif $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/
	cp tmp_vbox_home_linux/Machines/UFO/UFO.xml $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/Machines/UFO/UFO.xml.template
	cp .autorun $(DESTDIR)$(TARGET_PATH)/
	
	# installs Boot Isos
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/Isos
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Isos
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/Isos
	cp UFO-VirtualBox-boot-windows.img $(DESTDIR)$(TARGET_PATH)/Windows/.VirtualBox/Isos/UFO-VirtualBox-boot.img
	cp UFO-VirtualBox-boot-mac.img $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Isos/UFO-VirtualBox-boot.img
	cp UFO-VirtualBox-boot-linux.img $(DESTDIR)$(TARGET_PATH)/Linux/.VirtualBox/Isos/UFO-VirtualBox-boot.img

	# Kit de survie
	cp "Kit de survie.pdf" $(DESTDIR)$(TARGET_PATH)

	mkdir -p $(DESTDIR)/etc/pam.d
	install -p -m 644 vbox-client-symlink.pam $(DESTDIR)/etc/pam.d/vbox-client-symlink
	install -p -m 644 vbox-client-dnd.pam $(DESTDIR)/etc/pam.d/vbox-client-dnd

	mkdir -p $(DESTDIR)/etc/security/console.apps
	install -p -m 644 vbox-client-symlink.console $(DESTDIR)/etc/security/console.apps/vbox-client-symlink
	install -p -m 644 vbox-client-dnd.console $(DESTDIR)/etc/security/console.apps/vbox-client-dnd

	# shared folders automount and links
	mkdir -p $(DESTDIR)/usr/bin
	ln -s consolehelper $(DESTDIR)/usr/bin/vbox-client-symlink
	ln -s consolehelper $(DESTDIR)/usr/bin/vbox-client-dnd
	mkdir -p $(DESTDIR)/usr/sbin
	mkdir -p $(DESTDIR)/etc/xdg/autostart
	chmod +x vbox-client-symlink
	chmod +x vbox-client-dnd
	cp vbox-client-symlink $(DESTDIR)/usr/sbin
	cp vbox-client-symlink.desktop $(DESTDIR)/etc/xdg/autostart
	cp vbox-client-dnd $(DESTDIR)/usr/sbin
	cp vbox-client-dnd.desktop $(DESTDIR)/etc/xdg/autostart
	
updater:
	REV=`python -c "import pysvn; print pysvn.Client().info('.')['revision'].number";`; \
	echo Revision: $$REV; \
	mkdir update-$$REV; \
	
