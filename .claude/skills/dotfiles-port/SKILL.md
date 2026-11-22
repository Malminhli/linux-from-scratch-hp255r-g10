---
name: dotfiles-port
description: How to port a GitHub Hyprland/Wayland dotfiles repo (written for Arch/AUR) onto LFS for user mohammed — audit, adapt, unify colors, Arabic support, credit. Use in the theming phase.
---

# Porting dotfiles to LFS

## 1. Audit before copying
```bash
cd /home/mohammed/.local/src/<repo>
grep -rnE 'pacman|yay|paru|apt|dnf|flatpak|systemctl --user enable' . | head -50   # installer assumptions
grep -rhoE '^\s*exec(-once)?\s*=\s*\S+' . | sort -u                                # what Hyprland launches
grep -rhoE '"exec"\s*:\s*"[^"]+"' . | sort -u                                       # what waybar modules call
```
Make a table: `binary | needed by | installed in LFS? | action (build / replace / drop)`.

## 2. Never run the repo's install.sh
It installs packages with pacman/AUR and may overwrite things. Copy files by hand:
```bash
cp -r hypr waybar kitty rofi mako swww hyprlock fastfetch /home/mohammed/.config/   # only dirs that exist
```

## 3. Adapt
- Replace absolute paths like `/usr/share/<arch-specific>` with what exists on LFS.
- Replace `pamixer` → `wpctl`, `light` → `brightnessctl`, `nm-applet` → waybar network module + `nmtui`/`iwctl` if not built.
- Remove `exec-once` lines for tools that are not built, unless the lead agrees to build them.
- Keep the original color palette; put it in one place (e.g. `~/.config/hypr/colors.conf`) and source it everywhere possible.

## 4. Arabic + English
In `~/.config/hypr/hyprland.conf`:
```
input {
    kb_layout = us,ar
    kb_options = grp:alt_shift_toggle
}
```
Waybar: add a `hyprland/language` module. Fontconfig `~/.config/fontconfig/fonts.conf`: Noto Sans Arabic as fallback for sans-serif and monospace. Test by typing `مرحبا بالعالم` in the terminal and rofi.

## 5. Finish
```bash
chown -R mohammed:mohammed /home/mohammed
```
Copy the final tree to the repo `dotfiles/` (exclude caches, history, tokens) and write `dotfiles/README.md`: original repo URL, author, license, list of changes.
