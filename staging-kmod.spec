# buildforkernels macro hint: when you build a new version or a new release
# that contains bugfixes or other improvements then you must disable the
# "buildforkernels newest" macro for just that build; immediately after
# queuing that build enable the macro again for subsequent builds; that way
# a new akmod package will only get build when a new one is actually needed
%define buildforkernels newest

# which drivers to built
%global stgdrvs ASUS_OLED BATMAN_ADV ECHO EPL ET131X FB_UDL HECI HYPERV LINE6_USB RT2860 RT2870 RT3070 RT3090 RAMZSWAP R8187SE RTL8192SU RTL8192E RTL8192U SAMSUNG_LAPTOP SLICOSS W35UND PRISM2_USB VIDEO_GO7007 VT6655 VT6656
# todo: VIDEO_CX25821

# makes handling for rc kernels a whole lot easier:
#global prever rc8

Name:          staging-kmod
Version:       2.6.33.2
Release:       %{?prever:0.}2%{?prever:.%{prever}}%{?dist}.10
Summary:       Selected kernel modules from linux-staging

Group:         System Environment/Kernel
License:       GPLv2
URL:           http://www.kernel.org/
# a script to create this archive is part of staging-kmod-addons
Source0:       linux-staging-%{version}%{?prever:-%{prever}}.tar.bz2

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: %{_bindir}/kmodtool

# kmodtool does its magic here
%{!?kernels:BuildRequires: buildsys-build-rpmfusion-kerneldevpkgs-%{?buildforkernels:%{buildforkernels}}%{!?buildforkernels:current}-%{_target_cpu} }
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }


%description
Selected kernel modules from linux-staging


%prep
# kmodtool check and debug output:
%{?kmodtool_check}
kmodtool --target %{_target_cpu}  --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null

# prepare
%setup -q -c -T -a 0

# disable drivers that are enabled in Fedora's kernel, as those otherweise will get build
sed -i 's|.*at76.*||; s|.*WAVELAN.*||; s|.*PCMCIA_NETWAVE.*||' linux-staging-%{version}%{?prever:-%{prever}}/drivers/staging/Makefile

# seperate directories for each kernel variant (PAE, non-PAE, ...) we build the modules for
for kernel_version in %{?kernel_versions} ; do
 cp -a linux-staging-%{version}%{?prever:-%{prever}}/ _kmod_build_${kernel_version%%___*}
done


%build
for kernel_version in %{?kernel_versions}; do
 for module in %{stgdrvs} ; do 
   configops="CONFIG_${module}=m"
   case "${module}" in
     CX25821)
       configops="${configops} CONFIG_CX25821_ALSA"
       ;;
     HYPERV)
       ( [[ "%{_target_cpu}" == "ppc" ]] || [[ "%{_target_cpu}" == "ppc64" ]] ) && continue
       configops="${configops} CONFIG_${module}_STORAGE=m CONFIG_${module}_BLOCK=m CONFIG_${module}_NET=m"
       ;;
     PRISM2_USB)
       # does not build on ppc and ppc64 as of 011109; tested with 2.6.31.5
       ( [[ "%{_target_cpu}" == "ppc" ]] || [[ "%{_target_cpu}" == "ppc64" ]] ) && continue
       ;;
     RAMZSWAP)
       configops="${configops} CONFIG_RAMZSWAP_STATS=y"
       ;;
     RT3090)
       configops="${configops} -I ${PWD}/_kmod_build_${kernel_version%%___*}/"
       ;;
     RTL8192SU)
       # does not build on ppc and ppc64 as of 011109; tested with 2.6.31.5
       ( [[ "%{_target_cpu}" == "ppc" ]] || [[ "%{_target_cpu}" == "ppc64" ]] ) && continue
       ;;
     SLICOSS)
       # does not build on ppc and ppc64 as of 011109; tested with 2.6.30.9 and 2.6.31.5
       ( [[ "%{_target_cpu}" == "ppc" ]] || [[ "%{_target_cpu}" == "ppc64" ]] ) && continue
       ;;
     VIDEO_GO7007)
       configops="${configops} CONFIG_${module}_USB=m"
       ;;
     VIDEO_CX25821)
       configops="${configops} CONFIG_${module}_ALSA=m"
       ;;
   esac
   make %{?_smp_mflags} -C "${kernel_version##*___}" SUBDIRS=${PWD}/_kmod_build_${kernel_version%%___*}/drivers/staging/ modules ${configops}
 done
done


%install
rm -rf ${RPM_BUILD_ROOT}
for kernel_version in %{?kernel_versions}; do
 mkdir -p ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/
 install -D -m 755 _kmod_build_${kernel_version%%___*}/drivers/staging/*/*.ko ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/
done
# akmods hint:
# no akomds for now; packager is working on a solution where each driver will get its own akmod
# package, as everything else would be ridiculous due to long build times -- especially for
# netbooks that might need just one of the staging drivers; packaging each staging module 
# seperateley OTOH would be ridiculous for buildsys, package maintanance and users


%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Fri Aug 20 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.10
- rebuild for new kernel

* Tue Jul 27 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.8
- rebuild for new kernel

* Wed Jul 07 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.7
- rebuild for new kernel

* Fri Jun 18 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.6
- rebuild for new kernel

* Fri May 28 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.5
- rebuild for new kernel

* Thu May 20 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.4
- rebuild for new kernel

* Fri May 07 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.3
- rebuild for new kernel

* Tue May 04 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.2
- rebuild for new kernel

* Thu Apr 29 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2.1
- rebuild for new kernel

* Sun Apr 25 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-2
- enable echo

* Sun Apr 25 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-1.1
- rebuild for new kernel

* Fri Apr 10 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-1
- update to 2.6.33.2
- enable RAMZSWAP R8187SE RTL8192U BATMAN_ADV SAMSUNG_LAPTOP
- disable RTL8187SE (renamed)
- disable WAVELAN.* and PCMCIA_NETWAVE, as they are enabled in Fedora

* Sat Feb 20 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.32.8-1
- update to 2.6.32.8 for updates-testing kernel
- disable hv on ppc as it's useless and does not build

* Sun Dec 02 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.32-0.1.rc1
- enable HYPERV, RT3090, RTL8192E, VT6656
- drop AGNX, dropped upstream
- point to drivers/staging/ explicitely 
- support RC's better

* Sun Nov 22 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-2.5
- rebuild for new kernel, disable i586 builds

* Tue Nov 10 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-2.4
- rebuild for F12 release kernel

* Mon Nov 09 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-2.3
- rebuild for new kernels

* Fri Nov 06 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-2.2
- rebuild for new kernels

* Wed Nov 04 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-2.1
- rebuild for new kernels

* Sun Nov 01 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-2
- enable FB_UDL RTL8192SU VT6655
- disable RTL8192SU on ppc* due to build errors

* Sun Nov 01 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-1
- update to 2.6.31.5
- disable SLICOSS and PRISM2_USB on ppc* due to build errors

* Fri Oct 23 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.30.8-2
- enable VIDEO_GO7007

* Tue Oct 20 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.30.8-1
- initial package
