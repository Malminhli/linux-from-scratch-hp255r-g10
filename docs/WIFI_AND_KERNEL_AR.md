# تفاصيل Wi-Fi ونواة amdgpu

هذا الملف يوثق الحالة الفعلية كما هي على قسم LFS (`/dev/nvme0n1p6`)، وقد جُمعت المعلومات بفحص القسم للقراءة فقط من Arch Linux. ملفات إعداد النواة المذكورة هنا محفوظة في مجلد [`configs/`](../configs/).

| الملف | النواة | الدور |
|---|---|---|
| `configs/config-6.18.10-lfs-hptarget` | `vmlinuz-6.18.10-lfs-hptarget` | النواة التي فيها تعريف Wi-Fi (`rtw89`)، وهي مطابقة لملف `.config` في `/sources/linux-6.18.10` |
| `configs/config-6.18.10-amdgpu` | `vmlinuz-6.18.10-lfs-amdgpu` | النواة الحالية التي يقلعها GRUB الخاص بـArch، وفيها amdgpu مدمج مع firmware |

## 1. بطاقة الشبكة والتعريف الصحيح

اسم البطاقة التجاري **RTL8852BE-VT**، لكن الشريحة الفعلية من عائلة **8852BT**. لذلك فالتعريف المناسب هو `rtw89_8852bte` وليس `rtw89_8852be`. هذا واضح في إعداد نواة hptarget، حيث فُعّل خيار 8852BTE فقط وبقي 8852BE معطلاً:

```text
CONFIG_RTW89=m
CONFIG_RTW89_CORE=m
CONFIG_RTW89_PCI=m
CONFIG_RTW89_8852B_COMMON=m
CONFIG_RTW89_8852BT=m
CONFIG_RTW89_8852BTE=m
# CONFIG_RTW89_8852BE is not set
```

الوحدات المبنية موجودة في `/usr/lib/modules/6.18.10-lfs-hptarget/kernel/drivers/net/wireless/realtek/rtw89/`:

```text
rtw89_core.ko
rtw89_pci.ko
rtw89_8852b_common.ko
rtw89_8852bt.ko
rtw89_8852bte.ko
```

هذه هي نفس سلسلة الوحدات التي يحمّلها Arch للبطاقة نفسها (`rtw89_8852bte → rtw89_8852bt → rtw89_8852b_common → rtw89_core`)، والواجهة تظهر باسم `wlo1`.

## 2. سبب المشكلة الحقيقي: firmware مضغوط

حزمة linux-firmware تثبّت ملفات Realtek بصيغة `.zst`، لكن النواة في كلا الإعدادين مبنية بدون دعم فك ضغط firmware:

```text
CONFIG_FW_LOADER=y
# CONFIG_FW_LOADER_COMPRESS is not set
```

يعني ذلك أن النواة تبحث عن `rtw89/rtw8852bt_fw.bin` بالاسم الحرفي، ولا تقرأ `rtw8852bt_fw.bin.zst`. لهذا كانت الوحدة تُحمّل ولكن لا تظهر واجهة شبكة.

الحل كان وضع نسخة غير مضغوطة بجانب الملف المضغوط في `/usr/lib/firmware/rtw89/`:

```text
rtw8852bt_fw.bin        918376 بايت   (أضيف يدوياً)
rtw8852bt_fw.bin.zst    243063 بايت   (من linux-firmware)
```

وبالتحقق، الملف غير المضغوط مطابق تماماً لمحتوى `rtw8852bt_fw.bin.zst` بعد فكه.

استُخدم الأسلوب نفسه مع firmware البلوتوث في `/usr/lib/firmware/rtl_bt/` (`rtl8852btu_fw.bin`) ومع firmware كرت الشاشة في `/usr/lib/firmware/amdgpu/` (مذكور في القسم 4). كذلك يوجد `regulatory.db` و`regulatory.db.p7s` لقاعدة بيانات الترددات المطلوبة من `cfg80211`.

> **ملاحظة:** البديل الدائم لفك الملفات يدوياً هو تفعيل `CONFIG_FW_LOADER_COMPRESS` و`CONFIG_FW_LOADER_COMPRESS_ZSTD` في النواة القادمة، وعندها تقرأ النواة ملفات `.zst` مباشرة.

## 3. برامج الشبكة في مساحة المستخدم

بُنيت من `/sources` الحزم التالية:

| الحزمة | الإصدار | الدور |
|---|---|---|
| libnl | 3.12.0 | مكتبة netlink المطلوبة لـwpa_supplicant وNetworkManager |
| wpa_supplicant | 2.12 | المصادقة على شبكات WPA/WPA2 |
| NetworkManager | 1.58.1 | إدارة الاتصال، ومفعّل في `multi-user.target.wants` |

يوجد أيضاً `/etc/wpa_supplicant/wpa_supplicant-wlo1.conf` (لم يُنسخ للمستودع لأنه يحتوي بيانات الشبكة). أما ملف `systemd-networkd` الموجود `10-eth-dhcp.network` فيطابق `en*` فقط، أي أنه للشبكة السلكية.

## 4. نواة `6.18.10-lfs-amdgpu`

بُنيت هذه النواة في 14 أكتوبر لتشغيل Radeon 680M بتعريف amdgpu كامل بدلاً من framebuffer فقط. أهم الفروق بينها وبين hptarget:

| الخيار | hptarget | amdgpu |
|---|---|---|
| `CONFIG_LOCALVERSION` | `-lfs-hptarget` | `-amdgpu` |
| `CONFIG_DRM_AMDGPU` | `m` | `y` (مدمج) |
| `CONFIG_DRM_AMD_DC` | — | `y`، مع `DRM_AMD_DC_FP=y` |
| `CONFIG_DRM_FBDEV_EMULATION` | `y` | `y` |
| `CONFIG_EXTRA_FIRMWARE` | فارغ | 16 ملف firmware لـamdgpu |
| `CONFIG_CFG80211` / `CONFIG_MAC80211` | `m` | `y` |
| `CONFIG_RTW89` | `m` | **غير مفعّل** |

### لماذا firmware مدمج داخل النواة؟

النظام يقلع بدون initramfs. لما يكون amdgpu مدمجاً (`=y`) يبدأ قبل تركيب قسم الجذر، فلا يقدر يقرأ firmware من `/usr/lib/firmware`. الحل كان دمج الملفات داخل `vmlinuz` نفسه:

```text
CONFIG_EXTRA_FIRMWARE="amdgpu/psp_13_0_5_asd.bin amdgpu/psp_13_0_5_ta.bin amdgpu/psp_13_0_5_toc.bin amdgpu/vcn_3_1_2.bin amdgpu/yellow_carp_asd.bin amdgpu/yellow_carp_ce.bin amdgpu/yellow_carp_dmcub.bin amdgpu/yellow_carp_me.bin amdgpu/yellow_carp_mec2.bin amdgpu/yellow_carp_mec.bin amdgpu/yellow_carp_pfp.bin amdgpu/yellow_carp_rlc.bin amdgpu/yellow_carp_sdma.bin amdgpu/yellow_carp_ta.bin amdgpu/yellow_carp_toc.bin amdgpu/yellow_carp_vcn.bin"
CONFIG_EXTRA_FIRMWARE_DIR="/home/mohammed/lfs-kernel/fw"
```

`yellow_carp` هو الاسم الداخلي لجيل Rembrandt الذي ينتمي له Radeon 680M، و`psp_13_0_5` و`vcn_3_1_2` هما معالج الأمان ووحدة فك الفيديو الخاصة به. ولهذا كبر حجم النواة من حوالي 13.4MB (hptarget) إلى حوالي 20.3MB.

## 5. ملاحظة مهمة: Wi-Fi غير موجود في نواة amdgpu

إعداد `config-6.18.10-amdgpu` فيه:

```text
# CONFIG_RTW89 is not set
```

كذلك لا يحتوي مجلد `/usr/lib/modules/6.18.10-amdgpu` إلا 9 وحدات (netfilter وefivarfs وغيرها)، وليس فيه أي وحدة `rtw89`. يعني ذلك أن تعريف Wi-Fi الذي يعمل موجود في نواة **hptarget**، وأن نواة **amdgpu** التي يقلعها GRUB حالياً لا تحتوي تعريف البطاقة.

لكي يعمل Wi-Fi مع amdgpu، يُفعّل في إعدادها نفس خيارات القسم 1 (`CONFIG_RTW89_8852BTE=m` ومتعلقاتها)، ثم يُعاد البناء وينفّذ `make modules_install`. ويُفضّل تفعيل `CONFIG_FW_LOADER_COMPRESS_ZSTD` في نفس الخطوة.

## 6. مداخل GRUB

| المصدر | المدخل | النواة |
|---|---|---|
| GRUB الخاص بـArch (`/etc/grub.d/40_custom`) | `Linux From Scratch` | `vmlinuz-6.18.10-lfs-amdgpu root=/dev/nvme0n1p6 ro` |
| `/boot/grub/grub.cfg` داخل LFS | `HP targeted hardware` | `vmlinuz-6.18.10-lfs-hptarget` |
| `/boot/grub/grub.cfg` داخل LFS | `console fix backup` | `vmlinuz-6.18.10-lfs-consolefix` |

> **ملاحظة:** ملفات hptarget وconsolefix في `/boot` محفوظة حالياً باسم `.bak` (`vmlinuz-6.18.10-lfs-hptarget.bak`)، بينما مداخل `grub.cfg` الموجود داخل LFS تشير للاسم بدون `.bak`. هذا الملف لا يستخدمه GRUB الخاص بـArch، لكنه يحتاج تحديث إذا أردت الرجوع لنواة hptarget.
