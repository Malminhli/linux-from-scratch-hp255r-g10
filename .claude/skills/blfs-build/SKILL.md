---
name: blfs-build
description: Standard procedure for building one package inside the LFS chroot per the BLFS systemd book — version lookup, download, verify, configure/meson/cmake, build, install, log. Use for every package.
---

# Building one package (BLFS way)

## 0. Look it up
- Open the package page in the BLFS **systemd** book: https://www.linuxfromscratch.org/blfs/view/systemd/ (use the search or the index). Note: version, download URL, MD5, **Required** and **Recommended** deps, and the exact commands.
- Not in BLFS (Hyprland stack, waybar, swww, …)? Use the latest tagged release from the official repo and its README build steps. Record the exact tag.
- Check deps exist: `pkg-config --exists <dep> && pkg-config --modversion <dep>`.

## 1. Fetch and verify (inside chroot, in /sources)
```bash
cd /sources && wget -nc <url>
md5sum <tarball>        # compare with BLFS
```

## 2. Build in a clean dir
```bash
mkdir -p /sources/build /sources/logs && cd /sources/build
rm -rf /sources/build/<pkg>-<ver> && tar -xf /sources/<tarball> && cd <pkg>-<ver>
```
Pick the build system the book shows:

- **autotools**: `./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static && make && make install`
- **meson**: `mkdir build && cd build && meson setup --prefix=/usr --buildtype=release .. && ninja && ninja install`
- **cmake**: `cmake -B build -D CMAKE_INSTALL_PREFIX=/usr -D CMAKE_BUILD_TYPE=Release -G Ninja && ninja -C build && ninja -C build install`

Always wrap with a log: `( ... ) 2>&1 | tee /sources/logs/<pkg>-<ver>.log`, and check `${PIPESTATUS[0]}`.

## 3. After install
- `ldconfig`
- If the package ships systemd units the book enables, enable with `systemctl enable <unit>` (works offline in chroot).
- Quick check: `<bin> --version` and `pkg-config --modversion <name>`.
- Clean: `rm -rf /sources/build/<pkg>-<ver>`.

## 4. Log on the host
Append to `logs/build-log.md` in the repo:
`| <pkg> | <ver> | installed | <minutes> | <flags or notes> |`

## Known heavy hitters on this machine (Ryzen 5 7535U, 6c/12t)
| Package | Rough time | Notes |
|---|---|---|
| LLVM | 1–2 h | needed for radeonsi; build with `-D LLVM_TARGETS_TO_BUILD="host;AMDGPU"` |
| Rust | 1–2 h | only if something needs it (e.g. some Wayland tools) |
| Mesa | 15–30 min | `-D gallium-drivers=radeonsi -D vulkan-drivers=amd -D platforms=wayland,x11` |
| Firefox | 2–4 h + lots of RAM | ask Mohammed first; the official Mozilla binary tarball is the pragmatic alternative |
| GTK4 / Qt6 | 30–90 min | only build if a chosen app needs them |

## Failure protocol
1. Read the last 60 lines of the log, then `config.log` / `build/meson-logs/meson-log.txt`.
2. Classify: missing dep → build dep first · wrong version → check BLFS errata · compiler error → search the upstream issue tracker for the exact error.
3. Max two identical retries. Then report to the lead with the error and a diagnosis.

## Permissions note
Cleanup must use the absolute path `rm -rf /sources/build/<pkg>-<ver>` — the project guard hook lets that through silently and stops for any other `rm -rf`. Commands that touch PAM, users, `/boot`/GRUB, fstab, sudoers, other partitions, or network services will always pause for Mohammed's approval; that is intended, don't try to phrase around it.
