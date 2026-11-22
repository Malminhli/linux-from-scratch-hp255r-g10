# سجل بناء واجهة LFS

| الحزمة | الإصدار | الحالة | الوقت | ملاحظات |
|---|---|---|---|---|
| Linux-PAM | 1.7.3 | installed | 6 | BLFS systemd book; md5 OK; meson --prefix=/usr --buildtype=release -D docdir=/usr/share/doc/Linux-PAM-1.7.3 **+ -D docs=disabled** (docs=auto breaks without /etc/xml/catalog: xmllint fails on docbookxi.rng); prebuilt docs tarball installed instead; ninja test 78 OK / 0 fail; unix_chkpwd 4755; /etc/pam.d: system-{account,auth,session,password} + other per book; temp test `other` overwritten instead of rm; optional deps absent: audit, libeconf, libtirpc, libnsl, libselinux, BDB (gdbm used for pam_userdb); logind support on (libsystemd 259); log /sources/logs/linux-pam-1.7.3.log |
