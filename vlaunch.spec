Name:           vlaunch
Version:        0.6
Release:        1%{?dist}
Summary:        Install files for virtualization on the UFO vfat partition

BuildArch:      i386
Group:          Applications/System
License:        GPLv2
URL:            http://www.glumol.com
Source0:        http://www.glumol.com/chicoutimi/vlaunch-%{version}.1.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:	python /usr/bin/VirtualBox
Requires:       kernel-vbox python-augeas

%define TARGET_PATH /media/UFO
%define OVERLAY_DEV_UUID b07ac827-ce0c-4741-ae81-1f234377b4b5
%define OVERLAY_DEV_TYPE ext4-no_journal-no_huge_files

%package guest
Summary: Install guest part files
Group: Applications/System
Requires: VirtualBox-OSE-guest >= 2.2.4

%package generic
Summary: Install specific files for generic distribution
Group: Applications/System
Requires: vlaunch = %{version}-%{release}

%package polenumerique
Summary: Install specific files for pole numerique distribution
Group: Applications/System
Requires: vlaunch = %{version}-%{release}

%package descartes
Summary: Install specific files for the Descartes University distribution
Group: Applications/System
Requires: vlaunch = %{version}-%{release}


%description
vlaunch installs VirtualBox binaries and virtual machines configuration 
files on the UFO vfat partition. 3 directories are installed, one for each 
operating systems : Linux, Windows and MacOSX.

%description guest
Installs guest binaries that provide guest part of custom VirtualBox-OSE features.

%description generic
vlaunch installs VirtualBox binaries and virtual machines configuration 
files on the UFO vfat partition. 3 directories are installed, one for each 
operating systems : Linux, Windows and MacOSX.

%description polenumerique
vlaunch installs VirtualBox binaries and virtual machines configuration 
files on the UFO vfat partition. 3 directories are installed, one for each 
operating systems : Linux, Windows and MacOSX.

%description descartes
vlaunch installs VirtualBox binaries and virtual machines configuration 
files on the UFO vfat partition. 3 directories are installed, one for each 
operating systems : Linux, Windows and MacOSX.


%prep
%setup -n vlaunch-%{version}.1
# wget all binaries
wget http://kickstart.agorabox.org/private/virtualization/mac-intel.tgz
wget http://kickstart.agorabox.org/private/virtualization/windows.tgz
wget http://kickstart.agorabox.org/private/virtualization/fake_vmdk.tgz
wget -O "Kit de survie.pdf" http://ufo.agorabox.fr/sites/myufo/media/files/KIT_DE_SURVIE_BETA.pdf
wget -O "ufo_overlay.vdi" http://kickstart.agorabox.org/private/virtualization/ufo_overlay-%{OVERLAY_DEV_TYPE}-UUID=%{OVERLAY_DEV_UUID}.vdi

rm -rf iso
mkdir iso
cp bootfloppy.img UFO-VirtualBox-boot-windows.img
mount -o loop -t vfat UFO-VirtualBox-boot-windows.img iso
cp boot/grub.conf.windows iso/boot/grub/grub.conf
umount iso

rm -rf iso
mkdir iso 
cp bootfloppy.img UFO-VirtualBox-boot-linux.img
mount -o loop -t vfat UFO-VirtualBox-boot-linux.img iso
cp boot/grub.conf.linux iso/boot/grub/grub.conf
umount iso

rm -rf iso
mkdir iso 
cp bootfloppy.img UFO-VirtualBox-boot-mac.img 
mount -o loop -t vfat UFO-VirtualBox-boot-mac.img iso
cp boot/grub.conf.macosx iso/boot/grub/grub.conf
umount iso

# windows iso
# cp boot/grub.conf.windows iso/boot/grub/grub.conf
# mkisofs -R -b boot/grub/stage2_eltorito -no-emul-boot -boot-load-size 4 -boot-info-table -o UFO-VirtualBox-boot.iso iso

# macosx iso
# cp boot/grub.conf.macosx iso/boot/grub/grub.conf
# mkisofs -R -b boot/grub/stage2_eltorito -no-emul-boot -boot-load-size 4 -boot-info-table -o UFO-VirtualBox-boot.iso iso

# linux iso
# cp boot/grub.conf.linux iso/boot/grub/grub.conf
# mkisofs -R -b boot/grub/stage2_eltorito -no-emul-boot -boot-load-size 4 -boot-info-table -o UFO-VirtualBox-boot.iso iso

rm -rf iso

%build
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT TARGET_PATH=%{TARGET_PATH}


%post guest


%preun guest


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc README COPYING
%{TARGET_PATH}/autorun.inf
%{TARGET_PATH}/.autorun
%{TARGET_PATH}/UFO.ico
%{TARGET_PATH}/.background/ufo.png
%{TARGET_PATH}/.DS_Store
%{TARGET_PATH}/UFO.app
# %{TARGET_PATH}/Windows/tcl84.dll
# %{TARGET_PATH}/Windows/tix84.dll
# %{TARGET_PATH}/Windows/tk84.dll
%{TARGET_PATH}/Windows/MSVCR71.dll
%{TARGET_PATH}/Windows/msvcp71.dll
%{TARGET_PATH}/Windows/ufo.exe
# %{TARGET_PATH}/Windows/ufo.exe.manifest
# %{TARGET_PATH}/Windows/tcl
%{TARGET_PATH}/Windows/bin
%{TARGET_PATH}/Windows/settings
%dir %{TARGET_PATH}/Windows/logs
%{TARGET_PATH}/Windows/.VirtualBox/HardDisks
%{TARGET_PATH}/Windows/.VirtualBox/Isos
%{TARGET_PATH}/Windows/.VirtualBox/updater-download.png
%{TARGET_PATH}/Windows/.VirtualBox/updater-install.png
%{TARGET_PATH}/Windows/.VirtualBox/animated-bar.mng

%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/MacOS
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/PkgInfo
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Info.plist
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Frameworks
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/lib
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/settings
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/UFO.py*
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/site.py*
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/ufo.icns
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/__boot__.py*
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/__error__.sh
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/HardDisks
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Isos
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/updater-download.png
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/updater-install.png
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/animated-bar.mng
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/ufo-updater.app
%dir %{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/logs

%{TARGET_PATH}/Linux/ufo
%{TARGET_PATH}/Linux/bin
%{TARGET_PATH}/Linux/settings
%dir %{TARGET_PATH}/Linux/logs
%{TARGET_PATH}/Linux/.VirtualBox/HardDisks
%{TARGET_PATH}/Linux/.VirtualBox/Isos
%{TARGET_PATH}/Linux/.VirtualBox/updater-download.png
%{TARGET_PATH}/Linux/.VirtualBox/updater-install.png
%{TARGET_PATH}/Linux/.VirtualBox/animated-bar.mng

"%{TARGET_PATH}/Kit de survie.pdf"

%{TARGET_PATH}/Linux/.VirtualBox/vboxpython-workaround.py*
%{TARGET_PATH}/Windows/.VirtualBox/vboxpython-workaround.py*
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/vboxpython-workaround.py*

%files guest
%{_sysconfdir}/pam.d/vbox-client-dnd
%{_sysconfdir}/pam.d/vbox-client-symlink
%{_sysconfdir}/security/console.apps/vbox-client-dnd
%{_sysconfdir}/security/console.apps/vbox-client-symlink
%{_bindir}/vbox-client-symlink
%{_bindir}/vbox-client-dnd
%{_sbindir}/vbox-client-symlink
%{_sbindir}/vbox-client-dnd
%{_sysconfdir}/xdg/autostart/vbox-client-symlink.desktop
%{_sysconfdir}/xdg/autostart/vbox-client-dnd.desktop

%files generic
%{TARGET_PATH}/Linux/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Linux/.VirtualBox/ufo-generic.png
%{TARGET_PATH}/Windows/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Windows/.VirtualBox/ufo-generic.png
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-generic.png

%files polenumerique
%{TARGET_PATH}/Linux/.VirtualBox/ufo-polenumerique.bmp
%{TARGET_PATH}/Linux/.VirtualBox/ufo-polenumerique.png
%{TARGET_PATH}/Windows/.VirtualBox/ufo-polenumerique.bmp
%{TARGET_PATH}/Windows/.VirtualBox/ufo-polenumerique.png
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-polenumerique.bmp
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-polenumerique.png

%files descartes
%{TARGET_PATH}/Linux/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Linux/.VirtualBox/ufo-generic.png
%{TARGET_PATH}/Windows/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Windows/.VirtualBox/ufo-generic.png
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-generic.png


%changelog
* Tue Jul 9 2009 Kevin Pouget <kevin.pouget@agorabox.org>
Add vdi swap process

* Wed Jul 8 2009 Sylvain Baubeau <sylvain.baubeau@agorabox.org>
Use consolehelper to run program as root

* Fri Jul 3 2009 Kevin Pouget <kevin.pouget@agorabox.org>
Split package for distinguate guest / hosts files 

* Wed Jul 1 2009 Kevin Pouget <kevin.pouget@agorabox.org>
Split package for graphic specific files

* Mon Jun 29 2009 Sylvain Baubeau <sylvain.baubeau@agorabox.org>
Now uses VirtualBox OSE

* Wed Jun 17 2009 Kevin Pouget <kevin.pouget@agorabox.org>
Add VBoxClientDnD script to start drag and drop service

* Mon May 25 2009 Kevin Pouget <kevin.pouget@agorabox.org>
Add host removable medias as shared folders

* Tue Feb 17 2009 Kevin Pouget <kevin.pouget@agorabox.org>
Added mac intel launcher script
Update all platforms script, now configure virtual machine to boot on iso

* Fri Feb 13 2009 Sylvain Baubeau <sylvain.baubeau@agorabox.org>
Added a .iso file to use a kernel specifically compiled for VirtualBox
        
* Mon Nov 24 2008 Kevin	Pouget <kevin.pouget@agorabox.org>
Initial release
