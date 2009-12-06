# buildforkernels macro hint: when you build a new version or a new release
# that contains bugfixes or other improvements then you must disable the
# "buildforkernels newest" macro for just that build; immediately after
# queuing that build enable the macro again for subsequent builds; that way
# a new akmod package will only get build when a new one is actually needed
%define buildforkernels newest

# which drivers to built
%global stgdrvs AGNX ASUS_OLED EPL ET131X FB_UDL HECI LINE6_USB RT2860 RT2870 RT3070 RTL8187SE RTL8192SU SLICOSS W35UND PRISM2_USB VIDEO_GO7007 VT6655

Name:          staging-kmod
Version:       2.6.31.5
Release:       2%{?dist}.7
Summary:       Selected kernel modules from linux-staging

Group:         System Environment/Kernel
License:       GPLv2
URL:           http://www.kernel.org/
# a script to create this archive is part of staging-kmod-addons
Source0:       linux-staging-%{version}.tar.bz2

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
sed -i 's|.*at76.*||' linux-staging-%{version}/drivers/staging/Makefile

# seperate directories for each kernel variant (PAE, non-PAE, ...) we build the modules for
for kernel_version in %{?kernel_versions} ; do
 cp -a linux-staging-%{version}/drivers/staging/ _kmod_build_${kernel_version%%___*}
done


%build
for kernel_version in %{?kernel_versions}; do
 for module in %{stgdrvs} ; do 
   case "${module}" in
     PRISM2_USB)
       # does not build on ppc and ppc64 as of 011109; tested with 2.6.31.5
       ( [[ "%{_target_cpu}" == "ppc" ]] || [[ "%{_target_cpu}" == "ppc64" ]] ) && continue
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
       configops="CONFIG_${module}=m CONFIG_${module}_USB=m"
       ;;
     **)
       configops="CONFIG_${module}=m"
       ;;
   esac
   make %{?_smp_mflags} -C "${kernel_version##*___}" SUBDIRS=${PWD}/_kmod_build_${kernel_version%%___*}/ modules ${configops}
 done
done


%install
rm -rf ${RPM_BUILD_ROOT}
for kernel_version in %{?kernel_versions}; do
 mkdir -p ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/
 install -D -m 755 _kmod_build_${kernel_version%%___*}/*/*.ko ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/
done
# akmods hint:
# no akomds for now; packager is working on a solution where each driver will get its own akmod
# package, as everything else would be ridiculous due to long build times -- especially for
# netbooks that might need just one of the staging drivers; packaging each staging module 
# seperateley OTOH would be ridiculous for buildsys, package maintanance and users


%clean
rm -rf $RPM_BUILD_ROOT


%changelog
* Sun Dec 06 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-2.7
- rebuild for new kernel

* Wed Nov 25 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-2.6
- rebuild for new kernel

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
