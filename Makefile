NAME=vlaunch
VERSION=1.0

DIR=$(NAME)-$(VERSION)
ARCHIVE=$(DIR).tar.gz
SPECFILE=$(NAME).spec
URL=http://www.glumol.com/chicoutimi/vlaunch

OVERLAY_DEV_UUID=b07ac827-ce0c-4741-ae81-1f234377b4b5
OVERLAY_DEV_TYPE=ext4-no_journal-no_huge_files

POFILES         = $(wildcard locale/vlaunch*/*.po)
MOFILES         = $(patsubst %.po,%.mo,$(POFILES))

MSGFMT          = msgfmt --statistics --verbose
MSGMERGE        = msgmerge -v -U

SOURCES = src/ufovboxapi.py src/linuxbackend.py src/launcher.py src/updater.py src/createrawvmdk.py src/keyring_ctypes.py src/conf.py src/utils.py src/ufo_subprocess.py src/osbackend.py src/gui*.py

GUESTBIN        = guest/vbox-client-symlink guest/vbox-client-dnd guest/vbox-get-property guest/vbox-set-property guest/toggle-fullscreen guest/notify-logged-in guestmode/bind-fat-folders

ifneq ($(findstring ../Makefile.mk,$(wildcard ../Makefile.mk)), )
	include ../Makefile.mk
endif

all:

install: install-mo
	# build vdi file for swap device
	tools/createvdi.py -p `pwd`/ufo_swap.vdi

	# Common folder
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/settings
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/HardDisks
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/Images
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/images
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/logs
	mkdir -p $(DESTDIR)/usr/share/locale

	python -c "open(\"$(DESTDIR)$(TARGET_PATH)/._\xef\x80\xa9\", \"w\").write(open(\"graphics/VolumeIcon-OS-trick\").read())"

	cp graphics/UFO.svg graphics/*.bmp graphics/*.mng graphics/*.png $(DESTDIR)$(TARGET_PATH)/.data/images/
	cp graphics/UFO.ico $(DESTDIR)$(TARGET_PATH)/UFO.ico
	cp ufo_swap.vdi ufo_overlay.vdi $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/HardDisks/

	python -c "from ConfigParser import ConfigParser; cf = ConfigParser(); cf.read('setup/settings.conf'); cf.set('launcher', 'VERSION', '$(VERSION)'); cf.write(open('$(DESTDIR)$(TARGET_PATH)/.data/settings/settings.conf', 'w'))"

	# build windows tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Windows/bin64
	tar xvzf windows.x86.tgz -C $(DESTDIR)$(TARGET_PATH)/Windows/
	tar xvzf windows.AMD64.tgz -C $(DESTDIR)$(TARGET_PATH)/Windows/bin64
	rm -f $(DESTDIR)$(TARGET_PATH)/Windows/w9xpopen.exe
	rm -f $(DESTDIR)$(TARGET_PATH)/Windows/settings.conf
	cp setup/autorun.inf $(DESTDIR)$(TARGET_PATH)/
	cp USB_Disk_Eject.exe $(DESTDIR)$(TARGET_PATH)/Windows/bin
	cp USB_Disk_Eject.exe $(DESTDIR)$(TARGET_PATH)/Windows/bin64
	cp dd.exe $(DESTDIR)$(TARGET_PATH)/Windows/bin
	cp dd.exe $(DESTDIR)$(TARGET_PATH)/Windows/bin64
	
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
	    tools/create_fat_symlink.py `readlink $$symlink` $$symlink; \
	done

	install -D graphics/.background/ufo.png $(DESTDIR)$(TARGET_PATH)/.background/ufo.png
	cp setup/DS_Store $(DESTDIR)$(TARGET_PATH)/.DS_Store
	cp graphics/VolumeIcon.icns $(DESTDIR)$(TARGET_PATH)/.VolumeIcon.icns
	tools/create_fat_symlink.py Mac-Intel/UFO.app $(DESTDIR)$(TARGET_PATH)/UFO.app
	
	# build linux tree
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/bin
	mkdir -p $(DESTDIR)$(TARGET_PATH)/Linux/bin/sdk/bindings/xpcom/python
	cp src/launcher-linux.py $(DESTDIR)$(TARGET_PATH)/Linux/ufo
	cp setup/linux-settings-link $(DESTDIR)$(TARGET_PATH)/Linux/settings
        cp setup/linux-creator-link $(DESTDIR)$(TARGET_PATH)/Linux/creator
	cp -R sdk/bindings/xpcom/python/xpcom $(DESTDIR)$(TARGET_PATH)/Linux/bin/sdk/bindings/xpcom/python
	cp -R vboxapi sdk $(SOURCES) $(DESTDIR)$(TARGET_PATH)/Linux/bin
	cp setup/.autorun $(DESTDIR)$(TARGET_PATH)/

	# installs Boot Iso
	mkdir -p $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/Isos
	cp UFO-VirtualBox-boot.img $(DESTDIR)$(TARGET_PATH)/.data/.VirtualBox/Images/UFO-VirtualBox-boot.img

	# Kit de survie
	cp "Manuel d'utilisation.pdf" $(DESTDIR)$(TARGET_PATH)

	# shared folders automount and links
	mkdir -p $(DESTDIR)/usr/bin
	for prog in $(GUESTBIN); \
	do \
	    progname=`basename $$prog`; \
	    install -D -m 644 $$prog.pam $(DESTDIR)/etc/pam.d/$$progname; \
	    install -D -m 644 $$prog.console $(DESTDIR)/etc/security/console.apps/$$progname; \
	    ln -s consolehelper $(DESTDIR)/usr/bin/$$progname; \
	    install -D -m 755 $$prog $(DESTDIR)/usr/sbin/$$progname; \
	    install -D -m 755 $$prog $(DESTDIR)/usr/sbin; \
	done
	
	install -D -m 644 guest/vbox-client-symlink.desktop $(DESTDIR)/etc/xdg/autostart/vbox-client-symlink.desktop
	install -D -m 644 guest/vbox-client-dnd.desktop $(DESTDIR)/etc/xdg/autostart
	install -D -m 644 guest/toggle-fullscreen.desktop $(DESTDIR)/usr/share/applications/toggle-fullscreen.desktop
	install -D -m 644 guest/notify-logged-in.desktop $(DESTDIR)/etc/xdg/autostart/
	install -D -m 644 guest/switch-gui.desktop $(DESTDIR)/etc/xdg/autostart/
	install -D -m 755 guest/auto-proxy guest/switch-keyboard-layout guest/update-free-space guestmode/notify-guest-mode $(DESTDIR)/usr/bin/
	install -D -m 755 guest/switch-gui $(DESTDIR)/usr/bin/
	install -D -m 644 guest/auto-proxy.desktop guest/switch-keyboard-layout.desktop guest/update-free-space.desktop guestmode/notify-guest-mode.desktop $(DESTDIR)/etc/xdg/autostart
	install -D -m 755 guestmode/00-bind-fat-folders.sh $(DESTDIR)/etc/X11/xinit/xinitrc.d/00-bind-fat-folders.sh
	
	mkdir -p $(DESTDIR)/home/guest/.config/guestmode
	mkdir -p $(DESTDIR)/home/guest/.config/tsumufs
	touch $(DESTDIR)/home/guest/.config/guestmode/enabled
	touch $(DESTDIR)/home/guest/.config/tsumufs/disabled

	cd $(DESTDIR)$(TARGET_PATH) && find . -mindepth 1 -not -path "./.data*" | sed 's/^.\///' > /tmp/launcher.filelist
	install -D -m 755 /tmp/launcher.filelist $(DESTDIR)$(TARGET_PATH)/.data/launcher.filelist
	
generate-pot:
	pygettext.py -o vlaunch.pot -p locale/vlaunch src
	xgettext --from-code UTF-8 -o vlaunch-guest.pot -p locale/vlaunch-guest -L Shell guestmode/notify-guest-mode guest/vbox-client-symlink

update-po: Makefile $(POTFILE) refresh-po

refresh-po: Makefile
	for cat in $(POFILES); do \
		lang=`basename $$cat .po`; \
		dir=`dirname $$cat`; \
		component=`basename $$dir`; \
		if $(MSGMERGE) $$cat $$dir/$$component.pot ; then \
			echo "$(MSGMERGE) of $$lang succeeded" ; \
		else \
			echo "$(MSGMERGE) of $$lang failed" ; \
		fi \
	done

%.mo: %.po
	$(MSGFMT) -o $@ $<

generate-mo: $(MOFILES)

install-mo: $(MOFILES)
	for po in $(MOFILES); \
	do \
	    lang=`basename $$po .mo`; \
	    install -D -m 755 $$po $(DESTDIR)$(TARGET_PATH)/.data/locale/$$lang/LC_MESSAGES/vlaunch.mo; \
	    install -D -m 755 $$po $(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/vlaunch-guest.mo; \
	done

updater:
	REV=`python -c "import pysvn; print pysvn.Client().info('.')['revision'].number";`; \
	echo Revision: $$REV; \
	mkdir update-$$REV; \
	
live:
	pyinstaller-1.3/Build.py live.spec

bootfloppy:
	rm -rf iso
	mkdir iso
	cp setup/bootfloppy.img bootfloppy.img
	mount -o loop -t vfat bootfloppy.img iso 
	cp boot/grub.conf iso/boot/grub/grub.conf
	umount iso
	mv bootfloppy.img UFO-VirtualBox-boot.img

download-binaries:
	# wget all binaries
	wget -O mac-intel.tgz http://kickstart/private/virtualization/mac-intel.tgz
	wget -O windows.AMD64.tgz http://kickstart/private/virtualization/windows.AMD64.tgz
	wget -O windows.x86.tgz http://kickstart/private/virtualization/windows.x86.tgz
	wget -O "Manuel d'utilisation.pdf" http://myufo.agorabox.fr/sites/myufo/media/files/guide_ufo.pdf
	wget -O "ufo_overlay.vdi" http://kickstart/private/virtualization/ufo_overlay-${OVERLAY_DEV_TYPE}-UUID=${OVERLAY_DEV_UUID}.vdi
	wget -O USBDiskEjector1.1.2.zip http://quick.mixnmojo.com/files/USBDiskEjector1.1.2.zip
	wget -O dd-0.5.zip http://www.chrysocome.net/downloads/dd-0.5.zip
	unzip -o USBDiskEjector1.1.2.zip
	unzip -o dd-0.5.zip

