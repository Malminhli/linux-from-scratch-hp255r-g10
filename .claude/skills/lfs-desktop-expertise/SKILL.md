---
name: lfs-desktop-expertise
description: Expert knowledge base for turning LFS 13.0-systemd into a Hyprland desktop on AMD Radeon 680M — the non-obvious dependencies, ordering traps, and failure patterns. Every agent reads this before acting.
---

# What an expert knows that the book doesn't shout about

## Which book (read first)
The reference is the **stable BLFS 13.0-systemd** book — https://www.linuxfromscratch.org/blfs/view/13.0-systemd/ — because it matches LFS 13.0. **Do not use the development book** (`/blfs/view/systemd/`): its pages look identical but list newer versions (systemd 262.2, shadow 4.20.3, Linux-PAM 1.7.3 vs 259.1, 4.19.3, 1.7.2 in 13.0). Following it once already pulled in Linux-PAM 1.7.3 instead of 1.7.2. When the book says "reinstall Shadow/systemd", reinstall the **installed** version (Shadow 4.19.3, systemd 259.1) — never upgrade a core package as a side effect.

## The hidden foundation (do these BEFORE any graphics)
1. **Linux-PAM is not in base LFS, and the desktop needs it.** greetd, hyprlock, sudo, polkit all authenticate through PAM. BLFS order: build Linux-PAM → **rebuild Shadow** (so `login`/`passwd` use PAM) → **rebuild systemd** (so `pam_systemd` exists and logind registers sessions). Skip the systemd rebuild and you get a desktop where logind never creates a session, `XDG_RUNTIME_DIR` is missing, and nothing has GPU/input access.
   Before rebuilding Shadow, make sure `/etc/pam.d/{login,passwd,su,system-*,other}` follow BLFS exactly — a broken `/etc/pam.d` locks you out of the LFS system. Keep a root shell inside the chroot until `login` is verified.
2. **Seat management: use systemd-logind, not seatd.** On a systemd system, `libseat` talks to logind. Build `seatd` only for `libseat` if a package demands it, and configure it with `-Dlibseat-logind=systemd` — do not enable the seatd daemon alongside logind.
3. **D-Bus user session + polkit.** NetworkManager, bluez control, portals, and power actions need the session bus and polkit (+ a polkit agent in the session, e.g. `hyprpolkitagent` or `polkit-gnome`).
4. **make-ca + p11-kit first.** Without CA certificates, `wget`/`git`/`curl` over HTTPS fail inside the chroot and every later download breaks.

## Graphics stack — the traps
- **LLVM is mandatory for radeonsi** (and RADV uses ACO but Mesa still wants LLVM for radeonsi). Build with `-D LLVM_TARGETS_TO_BUILD="host;AMDGPU" -D LLVM_BUILD_LLVM_DYLIB=ON -D LLVM_LINK_LLVM_DYLIB=ON`. Use `-j6`: `-j12` on this 16G machine can OOM during linking.
- Mesa: `-D gallium-drivers=radeonsi,zink -D vulkan-drivers=amd -D platforms=wayland,x11 -D gbm=enabled -D egl=enabled -D glvnd=disabled -D valgrind=disabled`. Needs: libdrm (with amdgpu), wayland-protocols, `python3 -m pip` modules `mako` and `pyyaml` (in BLFS as Mako/PyYAML), glslang for Vulkan, libva optional, `libclc`/`SPIRV-*` only if rusticl is enabled (leave it off).
- **Firmware**: the 680M (Rembrandt-R / `yellow_carp`) needs `/lib/firmware/amdgpu/yellow_carp_*.bin` plus `dcn_3_1_*`/`psp_13_0_*` per `dmesg`. Missing firmware = amdgpu falls back to simpledrm = llvmpipe = slow desktop. Verify with `dmesg | grep -i amdgpu` after boot.
- The user must be in `video` and `render` groups, and `/dev/dri/renderD128` must exist.
- Success signal: `glxinfo -B` shows `AMD Radeon 680M (radeonsi, rembrandt, …)`, `vulkaninfo --summary` shows `RADV REMBRANDT`. `llvmpipe` anywhere = failure.

## Hyprland stack — version lock-step
- The hypr* libraries (`hyprutils`, `hyprlang`, `hyprcursor`, `hyprgraphics`, `hyprwayland-scanner`, `aquamarine`, `hyprland-qtutils` optional) move in lock-step. **Pick a Hyprland release tag first, then read its `CMakeLists.txt`/`meson.build`/`nix` files to get the exact minimum versions of each hypr* dep** — never mix "latest of everything".
- Hyprland needs a modern C++ compiler (GCC 14+, C++26 features) — LFS 13's GCC is fine; if a build complains about `std::format`/`<print>`, check the compiler actually used is `/usr/bin/g++`.
- Other deps commonly forgotten: `tomlplusplus`, `re2`, `muparser`, `libinput ≥ 1.26`, `libdisplay-info`, `libliftoff` (for aquamarine), `hwdata`, `xcb-util-errors` (for XWayland support), `pugixml` (hyprwayland-scanner), `file`/libmagic, `glaze` (newer releases).
- `xdg-desktop-portal` + `xdg-desktop-portal-hyprland` + `xdg-desktop-portal-gtk` — without them screenshots-from-apps, file pickers in browsers, and screen sharing break.
- Fallback rule: if Hyprland's tree exceeds ~3 serious build failures, propose **Sway** (single wlroots dep, in-tree-ish, very LFS-friendly) to Mohammed instead of burning hours.

## Sound
- PipeWire + WirePlumber + `pipewire-pulse`; ALSA needs `alsa-lib`, `alsa-ucm-conf` (AMD laptops often need UCM profiles), and SOF/ACP firmware if `dmesg` asks for it. WirePlumber needs Lua. Enable as **user** units: `systemctl --global enable pipewire.socket pipewire-pulse.socket wireplumber.service`.

## Network in the session
- NetworkManager needs: polkit, libndp, newt (for nmtui), wpa_supplicant **or** `iwd` backend. If Wi‑Fi is currently handled by systemd-networkd + wpa_supplicant, **disable** those when enabling NM — two managers fighting = Wi‑Fi drops. Do the switch last and keep the old config files.

## Fonts, locale, Arabic
- `fontconfig` + `freetype` (with harfbuzz) + `fribidi`. Fonts: Noto Sans/Serif, **Noto Sans Arabic + Noto Naskh Arabic**, JetBrainsMono Nerd Font, Noto Color Emoji.
- `localedef -i ar_SA -f UTF-8 ar_SA.UTF-8` and `en_US.UTF-8`. Terminals: kitty and foot both shape Arabic; check with real text.

## General expert habits
- Read the **BLFS errata** and the package's release notes before building a version that differs from the book.
- After each library: `ldconfig`. After installing `.desktop` files / icons: `update-desktop-database`, `gtk-update-icon-cache`, `fc-cache -f`, `glib-compile-schemas /usr/share/glib-2.0/schemas`.
- When a configure step fails, the real error is in `config.log` / `meson-log.txt`, not the last line of stdout.
- Check `pkg-config --modversion` against the minimum required **before** starting a 2-hour build.
- Prefer fixing root causes over `--disable-feature` hacks; when you must disable something, record it in `logs/build-log.md` with the reason.
