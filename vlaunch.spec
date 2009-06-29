Name:           vlaunch
Version:        0.5
Release:        1%{?dist}
Summary:        Install files for virtualization on the UFO vfat partition

BuildArch:      i386
Group:          Applications/System
License:        GPLv2
URL:            http://www.glumol.com
Source0:        http://www.glumol.com/chicoutimi/vlaunch-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:	python /usr/bin/VirtualBox
Requires:       kernel-vbox kernel-vbox-devel

%define TARGET_PATH /media/UFO
%define VM_NAME UFO

%description
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
#TODO: probably compile au3 windows script
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT TARGET_PATH=%{TARGET_PATH} VM_NAME=%{VM_NAME}


%post


%preun


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc README COPYING
%{TARGET_PATH}/Linux/
%{TARGET_PATH}/Windows/
%{TARGET_PATH}/Mac-Intel/
"%{TARGET_PATH}/Kit de survie.pdf"
/usr/bin/VBoxClientSymlink
/etc/xdg/autostart/vboxclientsymlink.desktop
/usr/bin/VBoxClientDnD
/etc/xdg/autostart/vboxclientdnd.desktop


%changelog
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
