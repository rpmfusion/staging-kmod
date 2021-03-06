# akmods not supported

# which drivers to built
%global stgdrvs FB_XGI FT1000 LTE_GDM724X PRISM2_USB RTL8192U SPEAKUP TOUCHSCREEN_SYNAPTICS_I2C_RMI4 USB_WPAN_HCD VT6655 VT6656 WIMAX_GDM72XX
%ifnarch %{arm}
%global stgdrvs %{stgdrvs} SLICOSS R8188EU
%endif

# fixme: DVB_AS102 DVB_CXD2099

# avoid this error: 
# /usr/lib/rpm/debugedit: canonicalization unexpectedly shrank by one character
%define debug_package %{nil}

# makes handling for rc kernels a whole lot easier:
#global prever rc8

Name:          staging-kmod
Version:       4.1.4
Release:       %{?prever:0.}1%{?prever:.%{prever}}%{?dist}.9
Summary:       Selected kernel modules from linux-staging

Group:         System Environment/Kernel
License:       GPLv2
URL:           http://www.kernel.org/
# a script to create this archive is part of staging-kmod-addons
Source0:       linux-staging-%{version}%{?prever:-%{prever}}.tar.xz

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: %{_bindir}/kmodtool

# kmodtool does its magic here
%{!?kernels:BuildRequires: buildsys-build-rpmfusion-kerneldevpkgs-newest-%{_target_cpu} }
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} --newest %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }


%description
Selected kernel modules from linux-staging


%prep
# kmodtool check and debug output:
%{?kmodtool_check}
kmodtool --target %{_target_cpu}  --repo rpmfusion --kmodname %{name} --newest %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null

# prepare
%setup -q -c -T -a 0

# disable drivers that are enabled in Fedora's kernel or not yet relevant, as those otherweise would get build
sed -i '/.COMMON_CLK_XLNX_CLKWZRD/ d; /.FIREWIRE_SERIAL/ d;  /.LIRC/ d; /.MTD_SPINAND/ d; /.R8712U/ d; /.RTL8192E/ d; /.R8192EE/ d; /.R8723AU/ d; /.SENSORS_ISL29/ d; /.IMX/ d; /.DWC2/ d; /.VIDEO_TLG2300/ d; /.GS_FPGABOOT/ d; /.I2O/ d; /.NVEC/ d;' $(find linux-staging-%{version}%{?prever:-%{prever}}/drivers/staging/ -name 'Makefile')

# Disable specifically for arm
%ifarch %{arm} aarch64
sed -i '/.R8188EU/ d;' $(find linux-staging-%{version}%{?prever:-%{prever}}/drivers/staging/ -name 'Makefile')
%endif

# broken in 3.13
sed -i 's!#include "dot11d.h"!#include "ieee80211/dot11d.h"!' linux-staging-%{version}/drivers/staging/rtl8192u/{r8192U_core.c,r8192U_wx.c,r819xU_phy.c}

# seperate directories for each kernel variant (PAE, non-PAE, ...) we build the modules for
for kernel_version in %{?kernel_versions} ; do
 cp -a linux-staging-%{version}%{?prever:-%{prever}}/ _kmod_build_${kernel_version%%___*}
done



%build
for kernel_version in %{?kernel_versions}; do
 oldcount=0
 # sanity check: nothing should be build
 make %{?_smp_mflags} -C "${kernel_version##*___}" SUBDIRS=${PWD}/_kmod_build_${kernel_version%%___*}/drivers/staging/
 newcount=$(find ${PWD}/_kmod_build_${kernel_version%%___*}/ -name '*.ko' | wc -l)
 if (( ${oldcount} != ${newcount} )); then
   echo "Modules build when none should get build; aborting" >&2
   exit 1
 fi

 # preparations
 for module in %{stgdrvs} ; do 
   echo
   echo "### ${module}"

   # sanity check
   if ! find . -name 'Makefile' | xargs grep "CONFIG_${module}"; then
      echo "CONFIG_${module} does not exist; aborting"  >&2
      exit 1
   fi

   # set options
   configops="CONFIG_${module}=m"
   case "${module}" in
     FT1000)
       configops="${configops} CONFIG_FT1000_USB=m CONFIG_FT1000_PCMCIA=m"
       ;;
     R8188EU)
       configops="${configops} CONFIG_88EU_AP_MODE=y"
       ;;
     SPEAKUP)
        configops="${configops} CONFIG_SPEAKUP_SYNTH_ACNTSA=m CONFIG_SPEAKUP_SYNTH_ACNTPC=m CONFIG_SPEAKUP_SYNTH_APOLLO=m CONFIG_SPEAKUP_SYNTH_AUDPTR=m CONFIG_SPEAKUP_SYNTH_BNS=m CONFIG_SPEAKUP_SYNTH_DECTLK=m CONFIG_SPEAKUP_SYNTH_DECEXT=m CONFIG_SPEAKUP_SYNTH_DECPC=m CONFIG_SPEAKUP_SYNTH_DTLK=m CONFIG_SPEAKUP_SYNTH_KEYPC=m CONFIG_SPEAKUP_SYNTH_LTLK=m CONFIG_SPEAKUP_SYNTH_SOFT=m CONFIG_SPEAKUP_SYNTH_SPKOUT=m CONFIG_SPEAKUP_SYNTH_TXPRT=m CONFIG_SPEAKUP_SYNTH_DUMMY=m "
       ;;
     WIMAX_GDM72XX)
       # broken, as of 3.8.1: CONFIG_WIMAX_GDM72XX_QOS=y CONFIG_WIMAX_GDM72XX_SDIO=y  
       configops="${configops} CONFIG_WIMAX_GDM72XX_WIMAX2=y CONFIG_WIMAX_GDM72XX_K_MODE=y CONFIG_WIMAX_GDM72XX_USB=y CONFIG_WIMAX_GDM72XX_USB_PM=y"
       ;;
   esac

   make %{?_smp_mflags} -C "${kernel_version##*___}" SUBDIRS=${PWD}/_kmod_build_${kernel_version%%___*}/drivers/staging/ modules CONFIG_STAGING_MEDIA=y ${configops}

   # sanity check
   newcount=$(find ${PWD}/_kmod_build_${kernel_version%%___*}/ -name '*.ko' | wc -l)
   if (( ${oldcount} == ${newcount} )); then
     echo "Seems no modules were build; aborting" >&2
     exit 1
   fi
   oldcount=${newcount}
 done
done


%install
rm -rf ${RPM_BUILD_ROOT}
for kernel_version in %{?kernel_versions}; do
 mkdir -p ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/
 install -D -m 755 -t ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/ $(find _kmod_build_${kernel_version%%___*}/drivers/staging/ -name '*.ko')
done
# akmods hint:
# no akomds for now; packager is working on a solution where each driver will get its own akmod
# package, as everything else would be ridiculous due to long build times -- especially for
# netbooks that might need just one of the staging drivers; packaging each staging module 
# seperateley OTOH would be ridiculous for buildsys, package maintanance and users


%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Mar 01 2018 RPM Fusion Release Engineering <leigh123linux@googlemail.com> - 4.1.4-1.9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Aug 31 2017 RPM Fusion Release Engineering <kwizart@rpmfusion.org> - 4.1.4-1.8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Mar 20 2017 RPM Fusion Release Engineering <kwizart@rpmfusion.org> - 4.1.4-1.7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Oct 06 2015 Nicolas Chauvet <kwizart@gmail.com> - 4.1.4-1.6
- Rebuilt for kernel

* Wed Sep 23 2015 Nicolas Chauvet <kwizart@gmail.com> - 4.1.4-1.5
- Rebuilt for kernel

* Wed Sep 16 2015 Nicolas Chauvet <kwizart@gmail.com> - 4.1.4-1.4
- Rebuilt for kernel

* Fri Aug 21 2015 Nicolas Chauvet <kwizart@gmail.com> - 4.1.4-1.3
- Rebuilt for kernel

* Thu Aug 13 2015 Nicolas Chauvet <kwizart@gmail.com> - 4.1.4-1.2
- Rebuilt for kernel

* Fri Aug 07 2015 Nicolas Chauvet <kwizart@gmail.com> - 4.1.4-1.1
- Rebuilt for kernel

* Tue Aug 4 2015 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 4.1.4-1
- Update to 4.1.4

* Tue May 26 2015 Nicolas Chauvet <kwizart@gmail.com> - 4.0.4-1.1
- Fix build on ARM

* Mon May 25 2015 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 4.0.4-1
- Update to 4.0.4
- Drop LINE6_USB and TOUCHSCREEN_CLEARPAD_TM1217 (dropped upstream)
- Disable I2O (enabled in Fedora-x86-32)

* Wed Apr  8 2015 Nicolas Chauvet <kwizart@gmail.com> - 3.19.2-2
- Update for ARM

* Tue Mar 24 2015 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.19.2-1
- Update to 3.19.2
- Drop BCM_WIMAX, dropped upstream
- Disable VIDEO_TLG2300, which is enabled in Fedora

* Sun Jan 11 2015 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.18.2-1
- Update to 3.18.2
- drop ET131X, dropped upstream

* Sat Nov 15 2014 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.17.2-1
- Update to 3.17.2
- drop drivers that werre dropped upstream: DGRP IDE_PHISON NET_VENDOR_SILICOM
  SOLO6X10 TRANZPORT USB_ENESTORAGE USB_SERIAL_QUATECH2 USBIP_CORE  WLAGS49_H25
  W35UND WLAGS49_H2

* Tue Sep 09 2014 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.16.2-1
- Update to 3.16.2
- disable R8192EE here, enabled in Fedora
- drop RTS5139 (left stating)

* Sun Jul 13 2014 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.15.4-1
- Update to 3.15.4
- drop ECHI and R8187SE (left stating)

* Wed Apr 30 2014 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.14.2-1
- Update to 3.14.2
- remove ZRAM and ZSMALLOC, as they left staging

* Sat Feb 15 2014 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.13.3-1
- Update to 3.13.3
- switch from bz2 to xz

* Fri Dec 20 2013 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.12.6-1
- Update to 3.12.6
- drop ASUS_OLED, dropped upstream
- enable LTE_GDM724X and R8188EU

* Fri Sep 20 2013 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.11.1-1
- Update to 3.11.1
- drop csr, dropped upstream

* Wed Aug 14 2013 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.10.5-1
- Update to 3.10.5

* Sat May 18 2013 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.9.2-1
- Update to 3.9.2
- disable SB105X - does not compile
- disable ZCACHE - latest version not buildable as module

* Sat Apr 13 2013 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.8.1-3
- disable RTL8192E, now shipped upstream

* Sat Mar 02 2013 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.8.1-2
- disable SBE_2T3E3 and CXT1E1, need something that is disabled in Fedora

* Fri Mar 01 2013 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.8.1-1
- Update to 3.8.1
- lot of misc small cleanups -- includes enabling a few more drivers and 
  remove code and options not relevant anymore
- add sanity check: make sure we do not built modules that are build by Fedora
- add sanity check: make sure each config builds at least one ko file

* Mon Jan 14 2013 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.7.2-1
- Update to 3.7.2

* Thu Oct 11 2012 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.6.1-1
- Update to 3.6.1
- drop declare_zsmalloc_license_and_init_exit_functions.patch

* Sat Aug 25 2012 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.5-3.1
- Fix stupid thinko to make crypto stuff for rtl8192e work

* Tue Jul 31 2012 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.5-2.1
- Fix zram

* Tue Jul 31 2012 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.5-1.1
- Update to 3.5
- Disable Mei, now a proper driver

* Mon Jul 16 2012 Jonathan Dieter <jdieter@gmail.com> - 3.4.2-2.1
- Enable USBIP

* Sun Jun 17 2012 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.4.2-1.1
- Update to 3.4.2
- Enable USB_WPAN_HCD 
- disable XVMALLOC and enable replacement ZSMALLOC
- disable R8712U, as it is enabled in Fedora

* Sun May 20 2012 William F. Acker <wacker@octothorp.org>
- enable Speakup

* Mon Apr 30 2012 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.3-2.1
- make a few things more robust for drivers that have subdirectories (fixes 
  #2265)
- enbable a few options r8192e driver needs since 3.3 

* Wed Mar 21 2012 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.3-1.1
- update to 3.3
- disable the HV driver, as HYPERV is not set in Fedora

* Tue Jan 24 2012 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.2.1-1.1
- update to 3.2.1
- drop ATH6K_LEGACY (replaced by a proper driver)
- drop DRM_PSB (enabled in Fedora)
- add RTS5139

* Tue Jan 24 2012 Nicolas Chauvet <kwizart@gmail.com> - 3.1-3.5
- rebuild for updated kernel

* Sun Jan 15 2012 Nicolas Chauvet <kwizart@gmail.com> - 3.1-3.4
- rebuild for updated kernel

* Mon Jan 09 2012 Nicolas Chauvet <kwizart@gmail.com> - 3.1-3.3
- rebuild for updated kernel

* Wed Jan 04 2012 Nicolas Chauvet <kwizart@gmail.com> - 3.1-3.2
- rebuild for updated kernel

* Tue Dec 27 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.1-3.1
- disable SBE_2T3E3, leads to missing symbols (#2107)

* Fri Dec 23 2011 Nicolas Chauvet <kwizart@gmail.com> - 3.1-2.9
- rebuild for updated kernel

* Sat Dec 17 2011 Nicolas Chauvet <kwizart@gmail.com> - 3.1-2.8
- rebuild for updated kernel

* Tue Dec 13 2011 Nicolas Chauvet <kwizart@gmail.com> - 3.1-2.7
- rebuild for updated kernel

* Sat Dec 10 2011 Nicolas Chauvet <kwizart@gmail.com> - 3.1-2.6
- rebuild for updated kernel

* Thu Dec 01 2011 Nicolas Chauvet <kwizart@gmail.com> - 3.1-2.5
- rebuild for updated kernel

* Wed Nov 23 2011 Nicolas Chauvet <kwizart@gmail.com> - 3.1-2.4
- rebuild for updated kernel

* Wed Nov 16 2011 Nicolas Chauvet <kwizart@gmail.com> - 3.1-2.3
- rebuild for updated kernel

* Mon Nov 14 2011 Nicolas Chauvet <kwizart@gmail.com> - 3.1-2.2
- rebuild for updated kernel

* Sun Nov 13 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.1-2.1
- Drop brcm80211 drivers; included in Fedora kernels since 3.1.1-1.rc1 with 
  changelog-enty "Backport brcm80211 from 3.2-rc1"

* Sun Nov 06 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 3.1-1.1
- update to 3.1 (no new drivers)

* Fri Aug 05 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.40-4
- fix BRCM drivers by building their util module for real

* Mon Aug 01 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.40-3
- bump release to 3 to avoid tagging problems in cvs
- make it obvious that akmods are not supported and remove buildforkernels
  variable to avoid mistakes

* Mon Aug 01 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.40-1
- update to 3.0 aka 2.6.40
- Enable BRCMSMAC, BRCMFMAC, DRM_PSB, INTEL_MEI, RTS_PSTOR, XVMALLOC, ZCACHE 
- Drop RT2860, RT2870, RT3070, RT3090, SAMSUNG_LAPTOP dropped upstream
- some adjustments for stupid brcm drivers that were renamed

* Sun Jul 31 2011 Nicolas Chauvet <kwizart@gmail.com> - 2.6.38.7-2.5
- rebuild for updated kernel

* Tue Jul 12 2011 Nicolas Chauvet <kwizart@gmail.com> - 2.6.38.7-2.4
- Rebuild for updated kernel

* Wed Jun 15 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.38.7-2.3
- rebuild for updated kernel

* Sat Jun 04 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.38.7-2.2
- rebuild for updated kernel

* Sun May 29 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.38.7-2.1
- Enable ATH6K_LEGACY BCM_WIMAX BRCM80211 EASYCAP FT1000_USB R8712U SBE_2T3E3
  SLICOSS SOLO6X10 TOUCHSCREEN_CLEARPAD_TM1217 TOUCHSCREEN_SYNAPTICS_I2C_RMI4
  USB_ENESTORAGE ZRAM
- disable a few drivers in Makefile as Fedora ships them 

* Sat May 28 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.38.7-1.1
- rebuild for updated kernel

* Tue May 24 2011 Nicolas Chauvet <kwizart@gmail.com> - 2.6.36.7-1
- Update to 2.6.38.7

* Thu May 05 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.10-1.4
- rebuild for updated kernel

* Sun Apr 24 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.10-1.3
- rebuild for updated kernel

* Mon Apr 04 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.10-1.2
- rebuild for updated kernel

* Sat Feb 12 2011 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.10-1.1
- rebuild for updated kernel

* Sat Dec 25 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.10-1
- update to 2.6.35.10
- disable VIDEO_GO7007, broken upstream

* Fri Dec 24 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.6-1.6
- rebuild for updated kernel

* Wed Dec 22 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.6-1.5
- rebuild for updated kernel

* Mon Dec 20 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.6-1.4
- rebuild for updated kernel

* Fri Dec 17 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.6-1.3
- rebuild for updated kernel

* Sun Dec 05 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.6-1.2
- rebuild for F-14 kernel

* Mon Nov 01 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.6-1.1
- rebuild for F-14 kernel

* Sat Oct 30 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.35.6-1
- update to 2.6.35.6 for F14
- enable FB_XGI
- disable debuginfo generation to avoid a build problem 

* Thu Oct 21 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.34.2-1.7
- rebuild for new kernel

* Sun Sep 19 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.34.2-1.6
- rebuild for new kernel

* Sat Sep 11 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.34.2-1.5
- rebuild for new kernel

* Fri Sep 10 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.34.2-1.4
- rebuild for new kernel

* Sun Aug 29 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.34.2-1.3
- rebuild for new kernel

* Wed Aug 11 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.34.2-1.2
- rebuild for new kernel

* Sun Aug 08 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.34.2-1.1
- update to 2.6.34.2, which is hitting updates-testing for F13
- enable phison (#1338)

* Sat Apr 10 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.33.2-1
- update to 2.6.33.2
- enable RAMZSWAP R8187SE RTL8192U BATMAN_ADV SAMSUNG_LAPTOP
- disable RTL8187SE (renamed)
- disable WAVELAN.* and PCMCIA_NETWAVE, as they are enabled in Fedora

* Sat Feb 20 2010 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.32.8-1
- update to 2.6.32.8 for updates-testing kernel
- disable hv on ppc as it's useless and does not build

* Wed Dec 02 2009 Thorsten Leemhuis <fedora [AT] leemhuis [DOT] info> - 2.6.32-0.1.rc1
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
