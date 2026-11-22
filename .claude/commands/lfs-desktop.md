---
description: المهمة الكاملة — تحويل LFS على /dev/nvme0n1p6 إلى نظام بواجهة رسومية متكاملة وثيم من GitHub
---

# المهمة: LFS Desktop — نظام أسطوري متكامل

أنت القائد (orchestrator). تكلّم محمد بالعامية الخليجية وبصيغة المذكر. هدفك تحويل نظام **LFS 13.0-systemd** الشغّال على جهاز HP 255R G10 إلى نظام سطح مكتب كامل: واجهة رسومية، صوت، شبكة من الواجهة، خطوط، ثيم مركّب من GitHub، وكل شي يشتغل من أول إقلاع بدون نواقص.

## الحقائق الثابتة (لا تفترض غيرها — تحقق منها بنفسك أول)

| العنصر | القيمة |
|---|---|
| قسم LFS | `/dev/nvme0n1p6` (ext4، ~30G، مستخدم ~13G) |
| النظام المضيف | Arch Linux على `/dev/nvme0n1p7` |
| الإقلاع | GRUB على Arch: `linux /boot/vmlinuz-6.18.10-lfs-amdgpu root=/dev/nvme0n1p6 ro` |
| المعالج / الرسوميات | AMD Ryzen 5 7535U / Radeon 680M (amdgpu, RDNA2) |
| الشبكة | Realtek RTL8852BE-VT (rtw89) — شغّالة |
| init | systemd، الحالة `running` |
| **ممنوع اللمس** | `nvme0n1p1` (EFI)، `p2`، `p3`، `p4`/`p5` (Windows)، `p7` (Arch)، `p8` (Gentoo) |

## القواعد الذهبية

1. **نسخة احتياطية قبل أي كتابة.** أول شي: تأكد من وجود `~/lfs-backup/lfs-p6-<date>.tar.zst` وإلا اطلب من محمد يشغّل أمر النسخ (في skill `lfs-chroot`). لا تبدأ بناء بدونها.
2. **كل البناء داخل chroot** بالطريقة الموجودة في skill `lfs-chroot`. لا تثبت شي على Arch بالغلط.
3. **حزمة وحدة في كل مرة، بالتسلسل.** البناء ما ينفع بالتوازي داخل نفس الـchroot. الـsubagents اللي يشتغلون بالتوازي هم بس اللي يقرون أو يبحثون.
4. **كتاب BLFS (systemd edition) هو المرجع** للإصدارات والأوامر والاعتماديات. أي حزمة مو في BLFS: من مصدرها الرسمي وبإصدار موثّق.
5. **لا تحذف مدخل GRUB الحالي ولا النواة الحالية.** أي نواة جديدة تنضاف كمدخل إضافي.
6. **وقّف واسأل محمد** قبل: تعديل النواة، أي أمر `rm -rf` خارج `/sources` أو مجلدات البناء، أي شي يلمس GRUB أو أقسام ثانية، واختيار الثيم.
7. **سجّل كل شي** في `logs/` داخل هذا المستودع: كل حزمة اسمها وإصدارها ونتيجتها. وفي النهاية حدّث `README.md` و`docs/PROJECT_STORY_AR.md` بمرحلة جديدة عن الواجهة.

## المعرفة

اقرأ `.claude/skills/lfs-desktop-expertise/SKILL.md` قبل ما تبدأ، وخل كل وكيل يقرأه. فيه الفخاخ اللي تضيّع ساعات لو ما انتبهت لها.

## فريقك (subagents في `.claude/agents/`)

| الوكيل | دوره | متى تستدعيه |
|---|---|---|
| `lfs-auditor` | يفحص النظام: وش مثبت، وش ناقص، firmware، إعدادات النواة | البداية، وبعد كل مرحلة |
| `kernel-checker` | يتأكد إن النواة فيها كل خيارات الرسوميات/الإدخال/الصوت | المرحلة 0 |
| `blfs-builder` | يبني ويثبت الحزم داخل chroot حسب BLFS | كل مراحل البناء |
| `desktop-ricer` | يدور ثيم على GitHub، يعرض خيارات، ويركّب الـdotfiles | المرحلة 4–5 |
| `qa-verifier` | يتحقق بشكل مستقل إن كل مرحلة فعلاً شغّالة | بعد كل مرحلة — قبل ما تقول "تم" |

## الخطة

**المرحلة 0 — الاستطلاع (بالتوازي: `lfs-auditor` + `kernel-checker` + `desktop-ricer` للبحث فقط)**
- جرد الموجود في LFS، فحص firmware `amdgpu` و`rtw89`، فحص `.config` النواة.
- `desktop-ricer` يجيب 3 ثيمات مرشحة (انظر المرحلة 4) — بس بحث، بدون تركيب.
- اعرض على محمد: التقرير + الناقص + الثيمات الثلاثة + تقدير الوقت. **انتظر موافقته واختياره للثيم.**

**المرحلة 1 — الأساس (أهم مرحلة، لا تستعجل):** النسخة الاحتياطية، `make-ca` + `p11-kit`، **Linux-PAM ← إعادة بناء Shadow ← إعادة بناء systemd مع PAM** (اقرأ skill `lfs-desktop-expertise` قبلها، وتحقق إن `login` يشتغل قبل ما تكمل)، `sudo`، `which`، polkit، أدوات البناء الناقصة (cmake/meson/ninja/rust حسب الحاجة)، Python modules (Mako, PyYAML)، مستخدم عادي `mohammed` بمجلد home ومجموعات `video,audio,input,wheel` (ما فيه مجموعة `render`: كتاب BLFS 13.0 يحوّل `renderD128` لمجموعة `video` عند إعادة بناء systemd).

**المرحلة 2 — الرسوميات:** libdrm → LLVM (مطلوب لـradeonsi؛ بناؤه طويل) → Mesa (`-Dgallium-drivers=radeonsi -Dvulkan-drivers=amd`) → libinput/libevdev/mtdev → libxkbcommon → wayland + wayland-protocols → pixman/cairo/pango/fontconfig/freetype/harfbuzz → Xwayland (للتوافق). إدارة الـseat عن طريق systemd-logind (مو seatd daemon). وفي النهاية xdg-desktop-portal + portal-hyprland + portal-gtk. خطوط: Noto + Noto Arabic + Nerd Font واحد (JetBrainsMono).

**المرحلة 3 — الواجهة:** الافتراضي **Hyprland** (Wayland، أقوى مجتمع ثيمات على GitHub). اعتمادياته: hyprutils, hyprlang, hyprcursor, hyprgraphics, hyprwayland-scanner, aquamarine, tomlplusplus, re2, muparser… — ابنها بإصداراتها المتوافقة. **خطة بديلة:** لو Hyprland علّق بعد محاولات جادة، اقترح Sway (wlroots) على محمد بدل ما تضيع وقت. شاشة دخول: greetd + tuigreet (خفيفة وما تحتاج X).

**المرحلة 4 — التطبيقات اللي تخلي النظام "متكامل":**
- طرفية: kitty أو foot · لانشر: rofi-wayland أو wofi · شريط: waybar · إشعارات: mako أو dunst · خلفيات: swww أو hyprpaper · قفل: hyprlock · لقطات شاشة: grim + slurp · حافظة: wl-clipboard
- صوت: PipeWire + WirePlumber (+ pipewire-pulse) — جرّب إن الصوت يطلع فعلياً
- شبكة من الواجهة: NetworkManager أو iwd + أداة تحكم في waybar
- بلوتوث: bluez + أمر تحكم
- سطوع وطاقة: brightnessctl، تحكم بأزرار الكيبورد
- متصفح: Firefox (بناؤه ثقيل جداً — ناقش مع محمد: يبنيه، ولا يستخدم Firefox binary الرسمي من موزيلا كحل عملي)
- مدير ملفات: Thunar أو yazi (طرفي)
- fastfetch موجود — اربطه بالثيم
- **اللغتين العربية والإنجليزية (إلزامي):**
  - locales: ولّد `en_US.UTF-8` و`ar_SA.UTF-8` (`localedef`)، و`/etc/locale.conf` يكون `LANG=en_US.UTF-8` مع إمكانية التبديل للعربي
  - كيبورد: `kb_layout = us,ar` في Hyprland مع تبديل بـ Alt+Shift، ومؤشر اللغة الحالية في waybar
  - خطوط: Noto Sans Arabic / Noto Naskh Arabic كـ fallback في fontconfig، والعربي يطلع متصل وصحيح (harfbuzz + fribidi) في الطرفية والمتصفح وrofi
  - الكونسول النصي (TTY): خط يدعم الحروف ولا يطلع مربعات
  - اختبار: اكتب جملة عربية في الطرفية وفي المتصفح وفي rofi، وتأكد إنها متصلة ومن اليمين لليسار

**المرحلة 5 — الثيم:** `desktop-ricer` يركّب الثيم اللي اختاره محمد، يعدّل المسارات والأوامر لتناسب LFS (ما فيه pacman/apt)، ويشيل أي جزء يعتمد على أداة ما انبنت أو يبنيها. نفس الألوان على: Hyprland، waybar، الطرفية، rofi، mako، GTK theme، أيقونات، cursor، fastfetch، tuigreet.

**المرحلة 6 — التحقق النهائي (`qa-verifier`):** إقلاع حقيقي ← tuigreet ← دخول ← Hyprland يشتغل بتسريع amdgpu (`glxinfo -B`/`vulkaninfo` يطلع radeonsi/RADV مو llvmpipe) ← صوت ← وايفاي من الواجهة ← لقطة شاشة ← قفل الشاشة ← إعادة إقلاع ثانية بدون أخطاء في `journalctl -b -p err`. أعط محمد قائمة اختبار يسويها بنفسه بعد الإقلاع (أنت ما تقدر تشوف الشاشة).

**المرحلة 7 — التوثيق:** `logs/build-log.md`، dotfiles النهائية في `dotfiles/` داخل المستودع، وتحديث README وقصة المشروع. commit على فرع جديد.

## أسلوب الشغل

- قبل كل مرحلة: قول لمحمد وش بتسوي وكم تتوقع تاخذ.
- استخدم TaskCreate لقائمة مهام تمشي عليها.
- إذا فشلت حزمة: اقرأ السجل كامل، شخّص السبب، صلّح. لا تعيد نفس الأمر بشكل أعمى أكثر من مرتين.
- لا تقول "خلصت" إلا إذا `qa-verifier` أكد.

ابدأ الحين بالمرحلة 0.
