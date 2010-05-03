NAME=vlaunch
VERSION=1.0
SOURCES=README COPYING vboxapi sdk boot src/*.py tools/ask-password tools/*.py \
        guest/vbox-client-dnd* guest/vbox-client-symlink* guest/vbox-get-property* \
        guest/toggle-fullscreen* guest/notify-logged-in* \
        graphics/ufo-*.bmp graphics/updater-*.png graphics/ufo-*.png graphics/close.png graphics/VolumeIcon-OS-trick \
        graphics/animated-bar.mng graphics/UFO.ico graphics/UFO.svg graphics/UFO.png graphics/settings.png graphics/about.png \
        graphics/.background graphics/VolumeIcon.icns graphics/credentials.png graphics/advanced.png graphics/graphics.png graphics/behavior.png graphics/personal.png \
        graphics/force.png graphics/exit.png graphics/system.png graphics/eject.png graphics/attach.png \
        setup/settings.conf setup/bootfloppy.img setup/.autorun setup/autorun.inf setup/DS_Store \
        locale windows.AMD64.tgz windows.x86.tgz mac-intel.tgz ufo_overlay.vdi Manuel\ d\'utilisation.pdf USB_Disk_Eject.exe

DIR=$(NAME)-$(VERSION)
ARCHIVE=$(DIR).tar.gz
SPECFILE=$(NAME).spec
URL=http://www.glumol.com/chicoutimi/vlaunch

OVERLAY_DEV_UUID=b07ac827-ce0c-4741-ae81-1f234377b4b5
OVERLAY_DEV_TYPE=ext4-no_journal-no_huge_files


ifneq ($(findstring ../Makefile.mk,$(wildcard ../Makefile.mk)), )
	include ../Makefile.mk
endif

all:

install: generate-mo
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
	mkdir -p $(DESTDIR)/usr/share/locale

	python -c "open(\"$(DESTDIR)$(TARGET_PATH)/._\xef\x80\xa9\", \"w\").write(open(\"VolumeIcon-OS-trick\").read())"

	for lang in `ls locale`; \
	do \
	    install -D -m 755 locale/$$lang/vlaunch.mo $(DESTDIR)$(TARGET_PATH)/.data/locale/$$lang/LC_MESSAGES/vlaunch.mo; \
	    install -D -m 755 locale/$$lang/vlaunch-guest.mo $(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/vlaunch-guest.mo; \
	done
	
	cp settings.conf $(DESTDIR)$(TARGET_PATH)/.data/settings/settings.conf
	cp UFO.svg *.bmp *.mng *.png $(DESTDIR)$(TARGET_PATH)/.data/images/
	cp UFO.ico $(DESTDIR)$(TARGET_PATH)/UFO.ico
	cp ufo_swap.vdi ufo_overlay.vdi $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/HardDisks/

	# build windows tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/bin64
	tar xvzf windows.x86.tgz -C $(DESTDIR)$(TARGET_PATH)/Windows/
	tar xvzf windows.AMD64.tgz -C $(DESTDIR)$(TARGET_PATH)/Windows/bin64
	rm -f $(DESTDIR)$(TARGET_PATH)/Windows/w9xpopen.exe
	rm -f $(DESTDIR)$(TARGET_PATH)/Windows/settings.conf
	cp autorun.inf $(DESTDIR)$(TARGET_PATH)/
	cp USB_Disk_Eject.exe $(DESTDIR)$(TARGET_PATH)/Windows/bin
	
	# build mac-intel tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/MacOS
	tar xvzf mac-intel.tgz -C $(DESTDIR)$(TARGET_PATH)/Mac-Intel
	rm -rf $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/

	# find $(DESTDIR)$(TARGET_PATH)/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app/Contents/Frameworks -type l -exec unlink {} \;

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
	cp VolumeIcon.icns $(DESTDIR)$(TARGET_PATH)/.VolumeIcon.icns
	./create_fat_symlink.py Mac-Intel/UFO.app $(DESTDIR)$(TARGET_PATH)/UFO.app
	
	# build linux tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/bin
	cp launcher-linux.py $(DESTDIR)$(TARGET_PATH)/Linux/ufo
	cp -R vboxapi sdk ufovboxapi.py linuxbackend.py launcher.py updater.py createrawvmdk.py keyring_ctypes.py conf.py utils.py ask-password ufo_subprocess.py osbackend.py gui*.py $(DESTDIR)$(TARGET_PATH)/Linux/bin
	cp .autorun $(DESTDIR)$(TARGET_PATH)/

	# installs Boot Iso
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/Isos
	cp UFO-VirtualBox-boot.img $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/Images/UFO-VirtualBox-boot.img

	# Kit de survie
	cp "Manuel d'utilisation.pdf" $(DESTDIR)$(TARGET_PATH)

	# shared folders automount and links
	mkdir -p $(DESTDIR)/usr/bin
	for prog in vbox-client-symlink vbox-client-dnd vbox-get-property toggle-fullscreen notify-logged-in; \
	do \
	    install -D -m 644 $$prog.pam $(DESTDIR)/etc/pam.d/$$prog; \
	    install -D -m 644 $$prog.console $(DESTDIR)/etc/security/console.apps/$$prog; \
	    ln -s consolehelper $(DESTDIR)/usr/bin/$$prog; \
	    install -D -m 755 $$prog $(DESTDIR)/usr/sbin/$$prog; \
	    install -D -m 755 $$prog $(DESTDIR)/usr/sbin; \
	done
	
	install -D -m 644 vbox-client-symlink.desktop $(DESTDIR)/etc/xdg/autostart/vbox-client-symlink.desktop
	install -D -m 644 vbox-client-dnd.desktop $(DESTDIR)/etc/xdg/autostart
	install -D -m 644 toggle-fullscreen.desktop $(DESTDIR)/usr/share/applications/toggle-fullscreen.desktop
	install -D -m 644 notify-logged-in.desktop $(DESTDIR)/etc/xdg/autostart/
	
	cd $(DESTDIR)$(TARGET_PATH) && find . -name .svn | xargs rm -rf
	cd $(DESTDIR)$(TARGET_PATH) && find . -mindepth 1 -not -path "./.data*" | sed 's/^.\///' > /tmp/launcher.filelist
	install -D -m 755 /tmp/launcher.filelist $(DESTDIR)$(TARGET_PATH)/.data/launcher.filelist
	
generate-pot:
	pygettext.py -d vlaunch src
	xgettext --from-code UTF-8 -o vlaunch-guest.pot -d vlaunch-guest -L Shell guest/vbox-client-symlink

update-po: generate-pot
	msgmerge -U locale/fr/vlaunch.po vlaunch.pot
	msgmerge -U locale/fr/vlaunch-guest.po vlaunch-guest.pot

generate-mo:
	for lang in `ls locale`; \
	do \
	    mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/locale/$$lang/LC_MESSAGES; \
	    msgfmt -o locale/$$lang/vlaunch.mo locale/$$lang/vlaunch.po; \
	    msgfmt -o locale/$$lang/vlaunch-guest.mo locale/$$lang/vlaunch-guest.po; \
	done

updater:
	REV=`python -c "import pysvn; print pysvn.Client().info('.')['revision'].number";`; \
	echo Revision: $$REV; \
	mkdir update-$$REV; \
	
live:
	pyinstaller-1.3/Build.py live.spec

download-binaries:
	# wget all binaries
	wget -O mac-intel.tgz http://kickstart/private/virtualization/mac-intel.tgz
	wget -O windows.AMD64.tgz http://kickstart/private/virtualization/windows.AMD64.tgz
	wget -O windows.x86.tgz http://kickstart/private/virtualization/windows.x86.tgz
	wget -O "Manuel d'utilisation.pdf" http://myufo.agorabox.fr/sites/myufo/media/files/guide_ufo.pdf
	wget -O "ufo_overlay.vdi" http://kickstart/private/virtualization/ufo_overlay-${OVERLAY_DEV_TYPE}-UUID=${OVERLAY_DEV_UUID}.vdi
	wget -O USBDiskEjector1.1.2.zip http://quick.mixnmojo.com/files/USBDiskEjector1.1.2.zip
	unzip USBDiskEjector1.1.2.zip

rpm: download-binaries build-rpm
