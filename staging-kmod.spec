# buildforkernels macro hint: when you build a new version or a new release
# that contains bugfixes or other improvements then you must disable the
# "buildforkernels newest" macro for just that build; immediately after
# queuing that build enable the macro again for subsequent builds; that way
# a new akmod package will only get build when a new one is actually needed
%define buildforkernels newest

# which drivers to built
%global stgdrvs AGNX ASUS_OLED EPL ET131X HECI LINE6_USB RT2860 RT2870 RT3070 RTL8187SE SLICOSS W35UND PRISM2_USB VIDEO_GO7007

Name:          staging-kmod
Version:       2.6.31.5
Release:       1%{?dist}
Summary:       Selected kernel modules from linux-staging

Group:         System Environment/Kernel
License:       GPLv2
URL:           http://www.kernel.org/
# a script to create this archive is part of staging-kmod-addons
Source0:       linux-staging-%{version}.tar.bz2

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: %{_bindir}/kmodtool

# needed for plague to make sure it builds for i586 and i686
ExclusiveArch:       i586 i686 x86_64 ppc ppc64

# kmodtool does its magic here
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }
%{!?kernels:BuildRequires: buildsys-build-rpmfusion-kerneldevpkgs-%{?buildforkernels:%{buildforkernels}}%{!?buildforkernels:current}-%{_target_cpu} }


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
* Sun Nov 01 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.31.5-1
- update to 2.6.31.5

* Fri Oct 23 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.30.8-2
- enable VIDEO_GO7007

* Tue Oct 20 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.30.8-1
- initial package
