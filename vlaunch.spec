%define TARGET_PATH /media/UFO
%define OVERLAY_DEV_UUID b07ac827-ce0c-4741-ae81-1f234377b4b5
%define OVERLAY_DEV_TYPE ext4-no_journal-no_huge_files

Name:           vlaunch
Version:        1.0
Release:        1%{?dist}
Summary:        Install files for virtualization on the UFO vfat partition

BuildArch:      i386
Group:          Applications/System
License:        GPLv2
URL:            http://www.glumol.com
Source0:        vlaunch-%{version}.tar.gz
Source1:        Manuel d'utilisation.pdf
Source2:        mac-intel.tgz
Source3:        windows.tgz
Source4:        ufo_overlay.vdi
Source5:        bootfloppy.img
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:	python /usr/bin/VirtualBox
Requires:       kernel-vbox python-augeas

%package guest
Summary: Install guest part files
Group: Applications/System
Requires: VirtualBox-OSE-guest >= 2.2.4 agorabox-ui pam_vbox

%package generic
Summary: Install specific files for generic distribution
Group: Applications/System

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
%setup -n vlaunch-%{version}
rm -rf iso
mkdir iso
mount -o loop -t vfat bootfloppy.img iso
cp boot/grub.conf iso/boot/grub/grub.conf
umount iso
mv bootfloppy.img UFO-VirtualBox-boot.img

# mkisofs -R -b boot/grub/stage2_eltorito -no-emul-boot -boot-load-size 4 -boot-info-table -o UFO-VirtualBox-boot.iso iso

rm -rf iso

%build
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT TARGET_PATH=%{TARGET_PATH}


%post guest
# Temporarely disables pam_vbox
# if [ $1 == 1 ]; then
#     authconfig --enablevbox --update
# fi

%postun guest
# Temporarely disables pam_vbox
# if [ $1 == 0 ]; then
#     authconfig --disablevbox --update
# fi


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
%{TARGET_PATH}/.VolumeIcon.icns
%{TARGET_PATH}/._
%{TARGET_PATH}/UFO.app
%{TARGET_PATH}/.data/settings
%{TARGET_PATH}/.data/.VirtualBox/HardDisks
%{TARGET_PATH}/.data/.VirtualBox/Images/UFO-VirtualBox-boot.img
%{TARGET_PATH}/.data/images/updater-download.png
%{TARGET_PATH}/.data/images/updater-install.png
%{TARGET_PATH}/.data/images/animated-bar.mng
%{TARGET_PATH}/.data/images/UFO.svg
%{TARGET_PATH}/.data/images/advanced.png
%{TARGET_PATH}/.data/images/graphics.png
%{TARGET_PATH}/.data/images/personal.png
%{TARGET_PATH}/.data/images/behavior.png
%{TARGET_PATH}/.data/images/UFO.png
%{TARGET_PATH}/.data/images/credentials.png
%{TARGET_PATH}/.data/images/close.png
%{TARGET_PATH}/.data/images/settings.png
%{TARGET_PATH}/.data/images/about.png
%{TARGET_PATH}/.data/images/attach.png
%{TARGET_PATH}/.data/images/eject.png
%{TARGET_PATH}/.data/images/exit.png
%{TARGET_PATH}/.data/images/force.png
%{TARGET_PATH}/.data/images/system.png

%{TARGET_PATH}/.data/launcher.filelist
%{TARGET_PATH}/.data/locale/fr/LC_MESSAGES/vlaunch.mo
%dir %{TARGET_PATH}/.data/logs

#%{TARGET_PATH}/Windows/msvcr71.dll
#%{TARGET_PATH}/Windows/msvcp71.dll
%{TARGET_PATH}/Windows/python26.dll
%{TARGET_PATH}/Windows/ufo.exe
%{TARGET_PATH}/Windows/bin
%{TARGET_PATH}/Windows/bin64

%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/MacOS
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/PkgInfo
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Info.plist
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Frameworks
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/include
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/lib
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/UFO.py*
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/site.py*
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/ufo.icns
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/__boot__.py*
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/__error__.sh
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/VirtualBox.app

%{TARGET_PATH}/Linux/ufo
%{TARGET_PATH}/Linux/bin

"%{TARGET_PATH}/Manuel d'utilisation.pdf"

%files guest
%{_sysconfdir}/pam.d/vbox-client-dnd
%{_sysconfdir}/pam.d/vbox-client-symlink
%{_sysconfdir}/pam.d/vbox-get-property
%{_sysconfdir}/pam.d/toggle-fullscreen
%{_sysconfdir}/pam.d/notify-logged-in
%{_sysconfdir}/security/console.apps/vbox-client-dnd
%{_sysconfdir}/security/console.apps/vbox-client-symlink
%{_sysconfdir}/security/console.apps/vbox-get-property
%{_sysconfdir}/security/console.apps/toggle-fullscreen
%{_sysconfdir}/security/console.apps/notify-logged-in
%{_bindir}/vbox-client-symlink
%{_bindir}/vbox-client-dnd
%{_bindir}/vbox-get-property
%{_bindir}/toggle-fullscreen
%{_bindir}/notify-logged-in
%{_sbindir}/vbox-client-symlink
%{_sbindir}/vbox-client-dnd
%{_sbindir}/vbox-get-property
%{_sbindir}/toggle-fullscreen
%{_sbindir}/notify-logged-in
%{_sysconfdir}/xdg/autostart/vbox-client-symlink.desktop
%{_sysconfdir}/xdg/autostart/vbox-client-dnd.desktop
%{_sysconfdir}/xdg/autostart/notify-logged-in.desktop
%{_datadir}/applications/toggle-fullscreen.desktop
%{_datadir}/locale/fr/LC_MESSAGES/vlaunch-guest.mo

%files generic
%{TARGET_PATH}/.data/images/ufo-generic.bmp
%{TARGET_PATH}/.data/images/ufo-generic.png

%files polenumerique
%{TARGET_PATH}/.data/images/ufo-polenumerique.bmp
%{TARGET_PATH}/.data/images/ufo-polenumerique.png

%files descartes
%{TARGET_PATH}/.data/images/ufo-generic.bmp
%{TARGET_PATH}/.data/images/ufo-generic.png


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
