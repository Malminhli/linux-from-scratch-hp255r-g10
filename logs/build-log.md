# سجل بناء واجهة LFS

| الحزمة | الإصدار | الحالة | الوقت | ملاحظات |
|---|---|---|---|---|
| Linux-PAM | 1.7.3 | installed | 6 | BLFS systemd book; md5 OK; meson --prefix=/usr --buildtype=release -D docdir=/usr/share/doc/Linux-PAM-1.7.3 **+ -D docs=disabled** (docs=auto breaks without /etc/xml/catalog: xmllint fails on docbookxi.rng); prebuilt docs tarball installed instead; ninja test 78 OK / 0 fail; unix_chkpwd 4755; /etc/pam.d: system-{account,auth,session,password} + other per book; temp test `other` overwritten instead of rm; optional deps absent: audit, libeconf, libtirpc, libnsl, libselinux, BDB (gdbm used for pam_userdb); logind support on (libsystemd 259); log /sources/logs/linux-pam-1.7.3.log |
| Shadow (reinstall with PAM) | 4.19.3 | installed | 1 | BLFS 13.0-systemd stable book; md5 OK; book seds + `./configure --sysconfdir=/etc --disable-static --without-libbsd --with-{b,yes}crypt` → "PAM support: yes"; /etc/pam.d files created verbatim **before** `make exec_prefix=/usr pamddir= install`; man not reinstalled; login.defs.orig saved + book for-loop (19 keys commented incl. ENCRYPT_METHOD); login.access/limits → .NOUSE; login/su/passwd/chpasswd/chfn/chsh/groupmems/newusers link libpam, useradd/userdel/usermod/group*/chage/chgpasswd do not (upstream: need --enable-account-tools-setuid, not in book); PAM tests OK (login/su correct 0, wrong 7, root wrong 7; passwd chauthtok 0 → $y$); pamtest removed; checker kept at /sources/build/pamcheck.py; log /sources/logs/shadow-4.19.3-pam.log |
| ownership fix | — | done | 1 | chown --from=1001 → root on /usr /etc /var /opt (2477+2476 in /usr, 2+2 in /var); setuid untouched; /sources not changed |
| ownership fix 2 | — | done | 1 | leftovers found by QA: /lib64 + its 2 loader symlinks (uid 1001), /usr/share/{unimaps,consoletrans} 113 files + 3 in /usr/share/doc/libxcb (uid/gid 1000) → root:root; whole LFS root (excl. /sources,/home,/tmp,/root) now has 0 files with uid/gid 1000/1001; no setuid involved |
| systemd (rebuild with PAM) | 259.1 | installed | 2 | BLFS 13.0-systemd stable book, version unchanged; md5 OK; fresh tree in /sources/build (old /sources/systemd-259.1 untouched); utmp-runlevel unit rm (was already absent); **udev sed: GROUP="render"→"video", GROUP="sgx" removed** (renderD* now GROUP="video" MODE="0666"); meson --prefix=/usr --buildtype=release -D default-dnssec=no -D firstboot=false -D install-tests=false -D ldconfig=false -D man=auto -D sysusers=false -D rpmmacrosdir=no -D homed=disabled -D mode=release -D pam=enabled -D pamconfdir=/etc/pam.d -D dev-kvm-mode=0660 -D nobody-group=nogroup -D sysupdate=disabled -D ukify=disabled -D docdir=/usr/share/doc/systemd-259.1 → PAM enabled (pam 1.7.3); ninja 76 s; **ninja test skipped** (book: needs a system booted with this systemd; fails in chroot as root); systemctl --version now +PAM (also newly +CURL +PCRE2 +P11KIT +XKBCOMMON, deps now present); pam_systemd.so + pam_systemd_loadkey.so installed; libpam is dlopen()ed by libsystemd-shared-259.so (ELF dlopen note), not a NEEDED lib; system-session got book's pam_loginuid/pam_systemd block; systemd-user per book; install also added /etc/pam.d/systemd-run0 (upstream) and /etc/systemd/journal-upload.conf; other 20 pam.d files md5-identical; 50-profile.sh generator 755; daemon-reexec skipped (no running systemd in chroot); /etc/systemd symlinks 30 before = 30 after, no diff; log /sources/logs/systemd-259.1-pam.log, state in /sources/logs/systemd-pam-state/ |
| Which | 2.23 | installed | 1 | BLFS 13.0-systemd stable; md5 OK; `./configure --prefix=/usr && make && make install`; no test suite (book); `which --version` → GNU which v2.23; log /sources/logs/which-2.23.log |
| sudo | 1.9.17p2 | installed | 1 | BLFS 13.0-systemd stable; md5 OK; book configure verbatim (--libexecdir=/usr/lib --with-secure-path --with-env-editor --docdir --with-passprompt) → AUTH_OBJS=pam.lo, sudoers.so links libpam; `LC_ALL=C make check` all suites 0 errors, `grep failed` empty; /etc/pam.d/sudo verbatim from book (644); /etc/sudoers.d/00-sudo = book content (secure_path + %wheel ALL=(ALL) ALL), **chmod 0440 added** (book heredoc leaves 0644 → `visudo -c` "bad permissions, should be mode 0440"); `visudo -c` OK; no NOPASSWD; log /sources/logs/sudo-1.9.17p2.log |
| libyaml | 0.2.5 | installed | 1 | BLFS 13.0-systemd; built as PyYAML recommended dep; md5 OK; `--prefix=/usr --disable-static`; make check 2/2 PASS; yaml-0.1.pc 0.2.5; log /sources/logs/libyaml-0.2.5.log |
| Cython | 3.2.4 | installed | 3 | BLFS 13.0-systemd python-modules; built as PyYAML recommended dep (needed to compile yaml/_yaml.pyx against libyaml); md5 OK; pip3 wheel --no-build-isolation / pip3 install --no-index; 137 s; tests skipped (book: >40 SBU); log /sources/logs/cython-3.2.4.log |
| PyYAML | 6.0.3 | installed | 1 | BLFS 13.0-systemd python-modules; md5 OK; book pip3 wheel/install; `import yaml` → 6.0.3 True (C ext _yaml links libyaml-0.so.2; CSafeLoader works); tests not run (pytest not installed, optional); log /sources/logs/pyyaml-6.0.3.log |
| duktape | 2.7.0 | installed | 1 | BLFS 13.0-systemd; polkit required dep; md5 OK; book sed -Os→-O2 + Makefile.sharedlibrary INSTALL_PREFIX=/usr; duktape.pc 2.7.0; no test suite in book; log /sources/logs/duktape-2.7.0.log |
| polkit | 127 | installed | 1 | BLFS 13.0-systemd; md5 OK; user/group per book: groupadd -fg 27 polkitd, useradd -u 27 -g polkitd -d /etc/polkit-1 -s /bin/false; meson --prefix=/usr --buildtype=release -D session_tracking=logind -D tests=true **-D man=false** (libxslt/docbook absent) **-D introspection=false** (gobject-introspection not installed; glib built without GI); os_type auto=lfs, authfw=pam, PAM includes system-{auth,account,password,session}; PAM file → /usr/lib/pam.d/polkit-1 (book default pam_prefix; libpam 1.7.3 searches /usr/lib/pam.d), no /etc/pam.d/polkit-1; **tests built but not run**: all 5 fail at wrapper.py `import dbus` (D-Bus Python + dbusmock absent, no system bus in chroot, wrapper bind-mounts over /etc in a namespace) → rerun after boot once those are installed; polkit.service static (D-Bus activated), not enabled per book; polkitd ldd 0 not found; log /sources/logs/polkit-127.log, test output /sources/logs/polkit-127-test.out |
| locale ar_SA.UTF-8 | glibc 2.43 | done | 1 | `localedef -i ar_SA -f UTF-8 ar_SA.UTF-8`; en_US.UTF-8 already present; /etc/locale.conf stays LANG=en_US.UTF-8 |
| user mohammed | — | created | 1 | `useradd -m -s /bin/bash -G video,audio,input,wheel mohammed` → uid/gid 1000; no `render` group (BLFS 13.0 maps renderD128 to video); /etc/skel absent so home is empty; password set by Mohammed via chpasswd (PAM) |
| Mako (pre-existing) | 1.4.3 | present | — | installed earlier by pip (2026-10-13, before this log); book 13.0 has 1.3.10; kept (newer, works with Mesa) |
| fix systemd-oom passwd entry | — | done | 1 | pre-existing LFS typo `…Daemon:/://:/usr/bin/false` (8 fields, getent error) → `…Daemon:/:/usr/bin/false`; `pwconv` added the missing shadow line; backup /etc/passwd.pre-oomfix |
| password for mohammed | — | set | 1 | set by Mohammed with chpasswd through PAM (yescrypt); pamcheck: login and sudo → PAM_SUCCESS |
| **Phase 1 QA** | — | **VERIFIED** | — | qa-verifier: PAM, Shadow, systemd+PAM, sudo, polkit, PyYAML, locale, user, ownership, boot safety all PASS; runtime logind/polkit checks wait for the first real boot |

## Built earlier (2026-10-13) by the automated script, before this log

57 packages listed in `/sources/hypr-logs/done/`; versions from `/sources/hyprland/packages.txt` (planned version; actual installed version may differ, e.g. CMake reports 4.0.5). The script stopped at Mesa (missing PyYAML).

| Package | Version | Status | Time | Notes |
|---|---|---|---|---|
| abseil-cpp | 20260817.0 | installed (2026-10-13) | — | cmake; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| cairo | 1.18.6 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| cargo-c-bin | 0.10.26 | installed (2026-10-13) | — | prebuilt; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| cmake | 4.4.4 | installed (2026-10-13) | — | cmake-if-old; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| curl | 8.22.0 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| fontconfig | 2.18.3 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| freetype | 2.14.3 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| fribidi | 1.0.17 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| git | 2.56.0 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| glib | 2.90.1 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| glslang | 16.6.0 | installed (2026-10-13) | — | cmake; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| harfbuzz | 14.6.0 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| hwdata | 0.412 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| iniparser | 4.3.2 | installed (2026-10-13) | — | cmake; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| lcms2 | 2.19.1 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libdisplay-info | 0.4.0 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libdrm | 2.4.134 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libei | 1.6.0 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libevdev | 1.14.0 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libinput | 1.32.0 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libjpeg-turbo | 3.2.0 | installed (2026-10-13) | — | cmake; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libpng | 1.6.59 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| librsvg | 2.63.2 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libtasn1 | 4.21.0 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libwebp | 1.6.0 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libX11 | 1.8.13 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libXau | 1.0.12 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libxcb | 1.17.0 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libXcursor | 1.2.3 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libXdmcp | 1.1.5 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libXfixes | 6.0.2 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libxkbcommon | 1.13.2 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libxml2 | 2.15.4 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libXrender | 0.9.12 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| libzip | 1.12 | installed (2026-10-13) | — | cmake; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| make-ca | 1.16.1 | installed (2026-10-13) | — | make; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| mtdev | 1.1.7 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| muparser | 2.3.5 | installed (2026-10-13) | — | cmake; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| p11-kit | 0.26.5 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| pango | 1.58.2 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| pcre2 | 10.49 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| pixman | 0.46.4 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| pugixml | 1.16 | installed (2026-10-13) | — | cmake; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| py-mako | 1.4.3 | installed (2026-10-13) | — | wheel; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| py-meson | 1.12.1 | installed (2026-10-13) | — | wheel; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| py-packaging | 26.3 | installed (2026-10-13) | — | wheel; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| re2 | 2025-11-05 | installed (2026-10-13) | — | cmake; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| rust-bin | 1.99.0 | installed (2026-10-13) | — | prebuilt; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| seatd | 0.9.3 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| tomlplusplus | 3.4.0 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| wayland | 1.26.0 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| wayland-protocols | 1.49 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| wget | 1.25.0 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| xcb-proto | 1.17.0 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| xkeyboard-config | 2.48 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| xorgproto | 2026.1 | installed (2026-10-13) | — | meson; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
| xtrans | 1.6.0 | installed (2026-10-13) | — | autotools; earlier automated script `/sources/hyprland/build-in-chroot.sh`, not following the BLFS book |
