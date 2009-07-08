Name:           vlaunch
Version:        0.5
Release:        2%{?dist}
Summary:        Install files for virtualization on the UFO vfat partition

BuildArch:      i386
Group:          Applications/System
License:        GPLv2
URL:            http://www.glumol.com
Source0:        http://www.glumol.com/chicoutimi/vlaunch-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:	python /usr/bin/VirtualBox
Requires:       kernel-vbox kernel-vbox-devel python-augeas

%define TARGET_PATH /media/UFO
%define VM_NAME UFO

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

%prep
%setup -q
# wget all binaries
wget http://kickstart.agorabox.org/private/virtualization/mac-intel.tgz
wget http://kickstart.agorabox.org/private/virtualization/windows.tgz
wget http://kickstart.agorabox.org/private/virtualization/fake_vmdk.tgz
wget -O "Kit de survie.pdf" http://ufo.agorabox.fr/sites/myufo/media/files/KIT_DE_SURVIE_BETA.pdf

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
make install DESTDIR=$RPM_BUILD_ROOT TARGET_PATH=%{TARGET_PATH} VM_NAME=%{VM_NAME}


%post guest


%preun guest


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc README COPYING
%{TARGET_PATH}/Windows/tcl84.dll
%{TARGET_PATH}/Windows/tix84.dll
%{TARGET_PATH}/Windows/tk84.dll
%{TARGET_PATH}/Windows/MSVCR71.dll
%{TARGET_PATH}/Windows/ufo.exe
%{TARGET_PATH}/Windows/tcl
%{TARGET_PATH}/Windows/bin
%{TARGET_PATH}/Windows/settings
%{TARGET_PATH}/Windows/.VirtualBox/HardDisks
%{TARGET_PATH}/Windows/.VirtualBox/Machines
%{TARGET_PATH}/Windows/.VirtualBox/Isos
%{TARGET_PATH}/Windows/.VirtualBox/VirtualBox.xml

%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/MacOS/UFO
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/MacOS/python
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
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Machines
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/Isos
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/VirtualBox.xml
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/Updater.app

%{TARGET_PATH}/Linux/ufo
%{TARGET_PATH}/Linux/bin
%{TARGET_PATH}/Linux/settings
%{TARGET_PATH}/Linux/.VirtualBox/HardDisks
%{TARGET_PATH}/Linux/.VirtualBox/Machines
%{TARGET_PATH}/Linux/.VirtualBox/Isos
%{TARGET_PATH}/Linux/.VirtualBox/VirtualBox.xml

"%{TARGET_PATH}/Kit de survie.pdf"

%files guest
%{_sysconfdir}/pam.d/VBoxClientDnD
%{_sysconfdir}/pam.d/VBoxClientSymlink
%{_sysconfdir}/security/console.apps/VBoxClientDnD
%{_sysconfdir}/security/console.apps/VBoxClientSymlink
%{_bindir}/VBoxClientSymlink
%{_bindir}/VBoxClientDnD
%{_sbindir}/VBoxClientSymlink
%{_sbindir}/VBoxClientDnD
%{_sysconfdir}/xdg/autostart/vboxclientsymlink.desktop
%{_sysconfdir}/xdg/autostart/vboxclientdnd.desktop

%files generic
%{TARGET_PATH}/Linux/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Linux/.VirtualBox/ufo-generic.gif
%{TARGET_PATH}/Windows/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Windows/.VirtualBox/ufo-generic.gif
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-generic.bmp
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-generic.gif

%files polenumerique
%{TARGET_PATH}/Linux/.VirtualBox/ufo-polenumerique.bmp
%{TARGET_PATH}/Linux/.VirtualBox/ufo-polenumerique.gif
%{TARGET_PATH}/Windows/.VirtualBox/ufo-polenumerique.bmp
%{TARGET_PATH}/Windows/.VirtualBox/ufo-polenumerique.gif
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-polenumerique.bmp
%{TARGET_PATH}/Mac-Intel/UFO.app/Contents/Resources/.VirtualBox/ufo-polenumerique.gif

%changelog
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
