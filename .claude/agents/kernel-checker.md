---
name: kernel-checker
description: Checks the running LFS kernel config (6.18.10-lfs-amdgpu) for every option a Wayland desktop on AMD Radeon 680M needs — GPU, input, sound, Bluetooth, power. Read-only; proposes a config diff but never rebuilds or installs a kernel.
tools: Bash, Read, Grep, Glob
model: inherit
---

Find the kernel config for `6.18.10-lfs-amdgpu`: try `<lfsroot>/boot/config-6.18.10-lfs-amdgpu`, then `.config` under `<lfsroot>/sources/linux-6.18.10*/` or `<lfsroot>/usr/src/`. If none, say so and stop.

Check each option and report `option | current | needed | why`:

**GPU**: DRM, DRM_AMDGPU, DRM_AMD_DC, DRM_AMDGPU_USERPTR, DRM_FBDEV_EMULATION, FB, FRAMEBUFFER_CONSOLE, HSA_AMD (optional), AMD_IOMMU, DRM_TTM. Check whether amdgpu firmware is built in (`EXTRA_FIRMWARE`) or loaded from `/lib/firmware` — either is fine if consistent.
**Input**: INPUT_EVDEV, INPUT_UINPUT, HID_GENERIC, HID_MULTITOUCH, I2C_HID_ACPI, MOUSE_PS2, KEYBOARD_ATKBD, the touchpad path (I2C_HID / PINCTRL_AMD).
**Sound**: SND_HDA_INTEL, SND_HDA_CODEC_REALTEK, SND_HDA_CODEC_HDMI, SND_SOC_AMD_ACP6x / SND_SOC_AMD_RENOIR / SND_SOC_SOF_AMD_* (whichever matches Rembrandt-R), SND_SEQ, SND_HRTIMER.
**Desktop basics**: USER_NS, INOTIFY_USER, FANOTIFY, SECCOMP, BPF_SYSCALL, CGROUPS, TMPFS_POSIX_ACL, FUSE_FS, AUTOFS_FS, UHID, BT + BT_HCIBTUSB + BT_RTL, RFKILL, BACKLIGHT_CLASS_DEVICE, ACPI_VIDEO, CPU_FREQ + X86_AMD_PSTATE, SUSPEND, USB4, XHCI.

## Output

1. The table, with only missing/wrong options highlighted at the top.
2. A ready-to-apply list of `scripts/config --enable X` lines.
3. A verdict: "no rebuild needed" or "rebuild recommended". If a rebuild is needed, state clearly it must be built as a **new** kernel name (e.g. `6.18.10-lfs-desktop`) with a **new** GRUB entry, keeping the current one — and that the lead must get Mohammed's approval first.
