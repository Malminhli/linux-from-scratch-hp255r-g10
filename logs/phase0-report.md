# المرحلة 0: الاستطلاع (2026-11-22)

كل الفحوصات كانت قراءة فقط، وما انكتب شي على `/dev/nvme0n1p6`. المصادر: lfs-auditor وkernel-checker وdesktop-ricer، ومعها فحص يدوي للإقلاع.

## الإقلاع والنواة
- ملف `/mnt/lfs/boot/grub/grub.cfg` هو GRUB الداخلي في LFS، ومدخله الأول `vmlinuz-6.18.10-lfs-hptarget`. أما GRUB اللي يقلع فعلاً فهو حق Arch (`\EFI\grub\grubx64.efi`)، وملفه `/boot/grub/grub.cfg` على Arch ما يقراه إلا root. **لازم نتأكد أي نواة تقلع فعلاً.**
- `vmlinuz-6.18.10-lfs-amdgpu` (و`uname -r` له `6.18.10-amdgpu`):
  - الرسوميات كاملة، وfirmware الـ amdgpu مضمّن في النواة.
  - **ما فيها** `RTW89`، ولا صوت HDA Realtek/HDMI، ولا لوحة لمس (I2C DesignWare/PINCTRL_AMD/I2C_HID_ACPI)، ولا بلوتوث، ولا `USER_NS`.
- `hptarget` فيها الوايفاي، بس ما فيها صوت ولا لوحة لمس.
- **الحكم: لازم نبني نواة جديدة** باسم `6.18.10-lfs-desktop` كمدخل إضافي، على أساس config الـ amdgpu. التعديلات المقترحة كاملة في تقرير kernel-checker تحت.
- الأجهزة:
  - لوحة اللمس: `SYNA32D8:00` على I2C (`i2c_hid_acpi`)
  - الصوت: Realtek ALC236 (`SND_HDA_CODEC_ALC269`)، وصوت HDMI من ATI
  - الوايفاي: `10ec:b520`، والدرايفر `rtw89_8852bte`

## النظام (lfs-auditor)
- الأدوات: GCC 15.2.0، وglibc 2.43، وPython 3.14.3، وmeson 1.12.1، وcmake 4.0.5، وRust 1.99.0 (نسخة binary).
- **موجود:**
  - الشهادات: make-ca وp11-kit
  - الأساس: dbus، وgit/wget/curl، وglslang
  - الرسوميات: libdrm 2.4.134، وlibinput 1.32، وwayland 1.26، وwayland-protocols 1.49، وxkbcommon 1.13.2
  - الرسم والخطوط: cairo وpango وfontconfig وfreetype وharfbuzz وfribidi، وglib 2.90.1
  - اعتماديات Hyprland: libseat (مع logind)، وlibdisplay-info، وhwdata، وre2، وmuparser، وtomlplusplus، وpugixml
  - الشبكة: NetworkManager 1.58.1 مع wpa_supplicant (بدون `nmcli`)
- **ناقص:**
  - Linux-PAM، فلازم نعيد بناء shadow وsystemd معه
  - sudo، وwhich، وpolkit، وPyYAML، وMesa، وvulkan-loader
  - xcb-util*، وXwayland، وgtk3/gtk4، وlibliftoff، وlua 5.5، وglaze، وكل مكتبات hypr*
  - الصوت: alsa، وpipewire، وwireplumber
  - bluez، والمستخدم `mohammed`، ومجموعة `render`، وlocale `ar_SA.UTF-8`
- **محاولة قديمة:** فيه سكربت آلي سابق في `/mnt/lfs/sources/hyprland/` بنى 52 حزمة (السجلات في `/mnt/lfs/sources/hypr-logs/`)، ووقف عند Mesa. السبب الحقيقي `No module named 'yaml'`، مو مشكلة إصدار Python. وهالحزم ما انسجلت في `build-log.md`.
- **Mesa 26.2.3 تقدر تبني radeonsi بدون LLVM** (`-Damd-use-llvm=false`)، وهذا يعارض ملف الخبرة. الثمن إننا نخسر llvmpipe وzink كخيار احتياطي.
- **firmware:**
  - ملفات `.zst` ما تنقرا لأن `FW_LOADER_COMPRESS` مطفي.
  - `rtl_bt/rtl8852btu_config.bin` موجود بس كـ `.zst`.
  - firmware الـ amdgpu والـ rtw89 الأساسي موجود بدون ضغط.
- المساحة: 16G فاضية. مجلد `/sources` حجمه 6.6G ونقدر ننظفه.

## الثيمات (desktop-ricer)
Hyprland صار يستخدم ملفات إعداد Lua من الإصدار 0.55. أحدث إصدار هو 0.57.2، والمصادر الموجودة إصدار 0.56.2، والثيمات الثلاثة كلها تحتاج 0.55 أو أحدث.

| الثيم | الطابع | الترخيص | سهولة النقل | ملاحظات |
|---|---|---|---|---|
| [cybrcore/cybrdots](https://github.com/cybrcore/cybrdots) | نيون سايبربانك | GPL-3.0 | متوسطة (3.5/5) | ألوان مركزية في `colors.lua`، بس هو طبقة ثيم بس: ما فيه اختصارات ولا تشغيل تلقائي |
| [r4ppz/Arch-dotfiles](https://github.com/r4ppz/Arch-dotfiles) | Gruvbox هادئ | Unlicense | سهلة (4.5/5) | ملفات Lua مقسمة، وخدمات systemd للمستخدم، وما فيه شي ثقيل |
| [ad1822/hyprdots](https://github.com/ad1822/hyprdots) | Catppuccin | MIT | متوسطة (3.5/5) | يحتاج تنظيف (Quickshell وghostty وblur ثقيل) |

توصية الوكيل: هجين، هيكل r4ppz مع ألوان cybrdots وثيمه. أو r4ppz بروحه لو تبي شي هادئ.

## قرارات محمد (2026-11-22)
- **الثيم:** ad1822/hyprdots (Catppuccin). نشيل منه Quickshell وghostty وسكربتات swww وسكربت CPU حق Python، ونخفف الـ blur إلى مرورين.
- **النواة:** موافق على `6.18.10-lfs-desktop` كمدخل إضافي، بشرط أعرض عليه الأوامر قبل ما ألمس GRUB أو `/boot`.
- **Firefox:** النسخة الجاهزة الرسمية من موزيلا في `/opt`.
- **افتراضات القائد (ما اعترض عليها):** Mesa بدون LLVM (`amd-use-llvm=false`، `vulkan-drivers=amd`)، وHyprland 0.56.2 من المصادر الموجودة.
