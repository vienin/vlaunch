NAME=vlaunch
VERSION=0.7
SOURCES=settings.conf *.py set_xml_attr boot ufo-*.bmp updater-*.png ufo-*.png animated-bar.mng README COPYING vboxapi sdk\
        bootfloppy.img launcher-linux.py \
        vbox-client-symlink.desktop \
        vbox-client-dnd.desktop \
        vbox-client-dnd vbox-client-dnd.pam vbox-client-dnd.console \
        vbox-client-symlink vbox-client-symlink.pam vbox-client-symlink.console \
        autorun.inf UFO.ico DS_Store .background .autorun ask-password

DIR=$(NAME)-$(VERSION)
ARCHIVE=$(DIR).tar.gz
SPECFILE=$(NAME).spec
URL=http://www.glumol.com/chicoutimi/vlaunch


ifneq ($(findstring ../Makefile.mk,$(wildcard ../Makefile.mk)), )
	include ../Makefile.mk
endif

all:

install:
	python -c "from ConfigParser import ConfigParser; cf = ConfigParser(); cf.read('settings.conf'); cf.set('launcher', 'VERSION', '$(VERSION)'); cf.write(open('settings.conf', 'w'))"

	# build vdi file for swap device
	./createvdi.py -p `pwd`/ufo_swap.vdi

    # Common folder
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/settings
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/HardDisks
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/Images
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/images
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/logs

	cp settings.conf $(DESTDIR)$(TARGET_PATH)/.data/settings/settings.conf
	cp ufo-*.bmp updater-*.png ufo-*.png animated-bar.mng $(DESTDIR)$(TARGET_PATH)/.data/images/
	cp UFO.ico $(DESTDIR)$(TARGET_PATH)/UFO.ico
	cp ufo_swap.vdi ufo_overlay.vdi $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/HardDisks/

	# build windows tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows
	tar xvzf windows.tgz -C $(DESTDIR)$(TARGET_PATH)/Windows/
	rm -f $(DESTDIR)$(TARGET_PATH)/Windows/settings.conf
	cp autorun.inf $(DESTDIR)$(TARGET_PATH)/
	
	# build mac-intel tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/MacOS
	tar xvzf mac-intel.tgz -C $(DESTDIR)$(TARGET_PATH)/Mac-Intel
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/

	find $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Frameworks -type l -exec unlink {} \;

	# Create symlinks for Mac OS X using the XSYM format"
	# http://www.opensource.apple.com/source/msdosfs/msdosfs-136.5/msdosfs.kextproj/msdosfs.kmodproj/fat.h
	echo find $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app -type l
	mac_symlinks=`find $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app -type l`; \
	for symlink in $$mac_symlinks; \
	do \
	    echo ./create_fat_symlink.py `readlink $$symlink` $$symlink; \
	    ./create_fat_symlink.py `readlink $$symlink` $$symlink; \
	done

	mkdir $(DESTDIR)$(TARGET_PATH)/.background
	cp .background/ufo.png $(DESTDIR)$(TARGET_PATH)/.background
	cp DS_Store $(DESTDIR)$(TARGET_PATH)/.DS_Store
	./create_fat_symlink.py Mac-Intel/UFO.app $(DESTDIR)$(TARGET_PATH)/UFO.app
	
	# build linux tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/bin
	cp launcher-linux.py $(DESTDIR)$(TARGET_PATH)/Linux/ufo
	cp -R vboxapi sdk ufovboxapi.py linuxbackend.py launcher.py updater.py createrawvmdk.py easygui.py conf.py utils.py ask-password subprocess.py gui*.py $(DESTDIR)$(TARGET_PATH)/Linux/bin
	cp .autorun $(DESTDIR)$(TARGET_PATH)/
	
	# installs Boot Iso
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/Isos
	cp UFO-VirtualBox-boot.img $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/Images/UFO-VirtualBox-boot.img

	# Kit de survie
	cp "Manuel d'utilisation.pdf" $(DESTDIR)$(TARGET_PATH)

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
	
live:
	pyinstaller-1.3/Build.py live.spec
