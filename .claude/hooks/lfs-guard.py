#!/usr/bin/env python3
"""Stops and asks Mohammed before risky commands, even ones an allow rule would pass
(e.g. inside `sudo chroot /mnt/lfs ...`). Prints a PreToolUse 'ask' decision."""
import json, re, sys

try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    sys.exit(0)

RISKY = [
    (r"/etc/pam\.d|pam_|Linux-PAM|linux-pam", "يلمس PAM — غلطة هنا ممكن تقفلك برا LFS"),
    (r"\bshadow\b|/etc/passwd|/etc/shadow|/etc/group|\bpasswd\b|\busermod\b|\buseradd\b|\bchpasswd\b", "يعدّل المستخدمين أو كلمات السر"),
    (r"/boot\b|vmlinuz|grub|efibootmgr|/efi\b", "يلمس الإقلاع أو النواة أو GRUB"),
    (r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\s+(?!/sources/build/[\w.+-]+(\s|$|[;&|'\"]))", "حذف (rm -r/-f) خارج /sources/build"),
    (r"/etc/fstab|/etc/sudoers", "يعدّل fstab أو sudoers"),
    (r"nvme0n1p[0-57-9]\b|/dev/nvme0n1\b", "يلمس قسم غير قسم LFS (p6)"),
    (r"systemctl\s+(disable|mask)|/etc/systemd/network|wpa_supplicant", "يغيّر خدمات أو إعداد الشبكة الحالي"),
    (r"\bmake\s+modules_install|\bmake\s+install\b.*linux-", "يثبت نواة أو وحدات نواة"),
    (r"chmod\s+-R|chown\s+-R\s+\S+\s+/(?!home|sources)", "تغيير صلاحيات بشكل واسع"),
]

hits = [why for pat, why in RISKY if re.search(pat, cmd, re.I)]
if hits:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "⚠️ وقفة أمان: " + " · ".join(dict.fromkeys(hits)),
    }}, ensure_ascii=False))
sys.exit(0)
