# Linux From Scratch 13.0-systemd على HP 255R G10

> مشروع عملي لبناء نظام Linux From Scratch يدويًا، وتشخيص مشكلات الإقلاع حتى الوصول إلى نظام عامل على عتاد حقيقي.

[![Status: Operational](https://img.shields.io/badge/Status-Operational-238636?style=flat-square&labelColor=161b22&logo=checkmarx&logoColor=3fb950)](#الحالة-النهائية) [![LFS: 13.0-systemd](https://img.shields.io/badge/LFS-13.0--systemd-58a6ff?style=flat-square&labelColor=161b22&logo=linux&logoColor=white)](https://www.linuxfromscratch.org/lfs/view/13.0-systemd/) [![Boot: UEFI + GRUB](https://img.shields.io/badge/Boot-UEFI%20%2B%20GRUB-a371f7?style=flat-square&labelColor=161b22&logo=gnu&logoColor=white)](#بيئة-المشروع)

## الفكرة

هذا المستودع يوثق تجربتي في بناء **Linux From Scratch 13.0-systemd** على جهاز **HP 255R G10** في إعداد إقلاع مزدوج، بدأ إلى جانب **Zorin OS** ثم انتقل لاحقًا إلى جانب **Arch Linux** كنظام مضيف. المصدر الأساسي للعمل كان كتاب **Linux From Scratch 13.0-systemd**، بينما استُخدمت أدوات الذكاء الاصطناعي ومصادر الإنترنت للبحث عن الأخطاء، فهم التشخيصات، ومراجعة الحلول قبل اختبارها عمليًا على الجهاز. [1]

لم تكن التجربة مجرد اتباع أوامر الكتاب؛ فقد بدأت ببناء حزم النظام داخل `chroot`، ثم إعداد النظام والنواة وGRUB، ومرّت بتشخيص أخطاء إقلاع حقيقية مرتبطة بوحدة التحكم النصية وقسم الجذر وغياب `systemd` وD-Bus، وانتهت بتشغيل الشبكة اللاسلكية.

## النتيجة باختصار

تم الوصول إلى نظام LFS يقلع بنجاح، يركّب قسم الجذر، يصل إلى شاشة تسجيل الدخول، ويعمل فيه `systemd` بحالة `running`. كما تم تثبيت Fastfetch لعرض معلومات النظام في الطرفية بعد تسجيل الدخول، وتشغيل Wi‑Fi بعد تثبيت تعريفات الشبكة. النظام ما زال يقلع بنجاح بعد الانتقال إلى Arch Linux كنظام مضيف.

| العنصر | النتيجة |
|---|---|
| بناء حزم LFS الأساسية | مكتمل |
| الإقلاع عبر UEFI وGRUB | يعمل |
| النواة الحالية | `6.18.10-lfs-amdgpu` |
| إخراج النص أثناء الإقلاع | يعمل |
| `systemd` وD-Bus | يعملان؛ الحالة `running` |
| Fastfetch | مثبت ويعمل |
| Wi‑Fi Realtek RTL8852BE-VT | يعمل |
| الإقلاع بعد الانتقال إلى Arch Linux | يعمل |

## بيئة المشروع

| المكوّن | التفاصيل |
|---|---|
| النظام المبني | Linux From Scratch 13.0-systemd |
| الجهاز | HP 255R 15.6 inch G10 Notebook PC |
| المعالج | AMD Ryzen 5 7535U |
| الرسوميات | AMD Radeon 680M المدمجة |
| التخزين | NVMe |
| قسم جذر LFS | `/dev/nvme0n1p6` |
| النظام المضيف | Arch Linux (سابقًا Zorin OS، وتم حذفه)، مع Windows في نفس قائمة الإقلاع |
| الإقلاع | UEFI عبر GRUB |
| النواة العاملة | `Linux 6.18.10-lfs-amdgpu` |

## رحلة المشروع

### 1. بناء النظام الأساسي

بدأ العمل من الفصل الثامن داخل بيئة `chroot`. تم بناء حزم أساسية مثل Bash وOpenSSL وPython وMeson وNinja وKmod وCoreutils وGawk وFindutils، ثم الحزم المتأخرة مثل Util-linux وE2fsprogs. إجراءات البناء اتبعت تسلسل الكتاب: فك المصدر، التهيئة، البناء، الاختبار عند توفره، ثم التثبيت. [1]

### 2. إعداد النظام والإقلاع الأول

تم إعداد ملفات النظام مثل `hostname` و`hosts` و`fstab` والمنطقة الزمنية واللغات، ثم بناء نواة Linux 6.18.10 مع دعم NVMe وإنشاء مدخل GRUB مخصص لقسم جذر LFS. تكوين وبناء النواة واعتماد GRUB جزء من مراحل LFS الرسمية. [2]

### 3. حل الشاشة السوداء

بعد الإقلاع الأول لم تظهر رسائل النظام، رغم وجود مؤشرات على أن النواة تعمل. تم تشخيص المشكلة على أنها مرتبطة بإخراج framebuffer وDRM console، ثم إعادة بناء النواة بعد تفعيل دعم fbdev المطلوب. كان العامل الحاسم هو تفعيل:

```text
CONFIG_DRM_FBDEV_EMULATION=y
```

وبعد ذلك ظهرت رسائل الإقلاع النصية بدلًا من الشاشة السوداء.

### 4. تصحيح GRUB وقسم الجذر

فشل النظام لاحقًا في تركيب جذر النظام بسبب استخدام `root=UUID=...` في إقلاع لا يعتمد على `initramfs`. تم تعديل مدخل GRUB ليستخدم المسار الذي ثبت عمله:

```text
root=/dev/nvme0n1p3
```

كما تم تصحيح ملف مداخل GRUB المخصصة وإعادة توليد الإعدادات. بقيت مداخل احتياطية للنوى السابقة عمدًا لتجنب فقدان مسار إقلاع عامل أثناء التجارب.

### 5. إصلاح systemd وD-Bus

كشف الإقلاع أن `/sbin/init` غير موجود، ولذلك تم تدقيق القسم من Zorin والتأكد من أن تثبيت `systemd` لم يكتمل. تم تثبيت MarkupSafe ثم Jinja2 ثم systemd من المصدر، وفق متطلبات البناء في LFS. [3]

بعد ذلك ظهرت حالة `degraded` بسبب غياب وحدات D-Bus والهدف الافتراضي. أعيد تثبيت D-Bus، وتم إنشاء `default.target` باتجاه `multi-user.target`. أصبحت النتيجة النهائية:

```text
systemctl is-system-running
running
```

### 6. نواة موجهة لعتاد الجهاز

تم بناء نواة أخف موجهة للعتاد الفعلي تحت الاسم `6.18.10-lfs-hptarget`. استُبعدت محاولة بناء نواة من إعداد Zorin الكامل لأنها كانت ضخمة، بطيئة، وتضمنت إعدادات تصحيح لا تناسب بيئة LFS.

### 7. تشغيل Wi‑Fi

بطاقة Realtek RTL8852BE-VT لم تكن تظهر كواجهة شبكة رغم تحميل وحدات `rtw89`. تم حل المشكلة بتثبيت firmware وتعريفات الشبكة المطلوبة داخل LFS، وأصبح الاتصال اللاسلكي يعمل.

### 8. الانتقال إلى Arch Linux

تم استبدال Zorin OS بـ**Arch Linux** كنظام مضيف وحذف Zorin بالكامل. نظام LFS يقلع بنجاح بعد الانتقال من GRUB الخاص بـArch، من القسم `/dev/nvme0n1p6` وبنواة `6.18.10-lfs-amdgpu`.

## أبرز المشكلات والدروس

| المشكلة | ما تم عمله | الحالة |
|---|---|---|
| فشل تنزيل Inetutils | استخدام مصدر GNU بديل بعد انتهاء مهلة مرآة تنزيل | حُلّت |
| خطأ `bc: command not found` أثناء بناء النواة | تثبيت حزمة Bc المفقودة داخل LFS | حُلّت |
| شاشة سوداء عند الإقلاع | مراجعة إعدادات DRM وframebuffer وتفعيل fbdev | حُلّت |
| فشل تركيب قسم الجذر | استخدام `root=/dev/nvme0n1p3` بدل UUID دون initramfs | حُلّت |
| غياب `/sbin/init` | تثبيت systemd وسلسلة اعتمادياته الناقصة | حُلّت |
| حالة `systemd` كانت `degraded` | إعادة تثبيت D-Bus وإنشاء `default.target` | حُلّت |
| Wi‑Fi لا يظهر كواجهة شبكة | تثبيت firmware وتعريفات الشبكة اللازمة لبطاقة Realtek | حُلّت |

## الحالة النهائية

النظام يقلع الآن من GRUB على Arch Linux بهذا السطر:

```text
linux /boot/vmlinuz-6.18.10-lfs-amdgpu root=/dev/nvme0n1p6 ro
```

الشبكة اللاسلكية تعمل، والنظام يقلع بجانب Arch Linux. التحسينات المتبقية شكلية واختيارية، مثل تنظيف قائمة GRUB من المداخل الاحتياطية القديمة وتخصيص شعار Fastfetch. هذه النقاط لا تمنع النظام من الإقلاع أو تشغيل خدماته الأساسية.

## محتويات المستودع

```text
.
├── README.md
└── docs/
    └── PROJECT_STORY_AR.md
```

- `README.md`: ملخص واضح للمشروع والنتيجة وأهم التحديات.
- `docs/PROJECT_STORY_AR.md`: السرد التقني الكامل من البناء إلى الاستقرار، بما يشمل الأخطاء والحلول والحالة النهائية.

## ملاحظات مهمة

هذا المشروع ليس توزيعة عامة ولا دليل تثبيت عالميًا لكل جهاز. الإعدادات، وخصوصًا إعدادات النواة وGRUB، موجهة إلى العتاد وقسم الجذر المذكورين في هذا المستودع. لا ينبغي حذف مداخل GRUB الاحتياطية أو تعديل النواة دون تحقق مسبق من مسار إقلاع بديل.

## المراجع

[1] [Linux From Scratch 13.0-systemd — الكتاب الرسمي](https://www.linuxfromscratch.org/lfs/view/13.0-systemd/)

[2] [LFS: تكوين وبناء النواة](https://www.linuxfromscratch.org/lfs/view/13.0-systemd/chapter10/kernel.html)

[3] [LFS: تثبيت systemd](https://www.linuxfromscratch.org/lfs/view/13.0-systemd/chapter08/systemd.html)

[4] [LFS: تثبيت D-Bus](https://www.linuxfromscratch.org/lfs/view/13.0-systemd/chapter08/dbus.html)

[5] [Fastfetch](https://github.com/fastfetch-cli/fastfetch)
