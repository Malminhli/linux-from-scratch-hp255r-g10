#!/usr/bin/env python3
"""LFS safety guard (PreToolUse hook for Bash).

Stops and asks Mohammed ONLY when a command both
  1) actually changes something (writes, installs, deletes, edits users/services/boot), and
  2) touches a sensitive area (PAM, users, boot/GRUB/kernel, fstab/sudoers, other partitions,
     network setup) — or deletes outside /sources/build.
Pure reads never stop, however they are written. Prints a PreToolUse 'ask' decision or nothing.
"""
import json, re, sys

try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    sys.exit(0)

text = cmd.replace("2>&1", " ").replace("2>/dev/null", " ").replace("&>/dev/null", " ").replace(">/dev/null", " ")

# Write operations that are unambiguous wherever they appear.
WRITE_OPS = re.compile(r"""
    (?<![<>=!-])>(?![=&])                                  # output redirect (not >=, ->, 2>&1)
  | \btee\b | \bsed\s+(?:-\w+\s+)*-\w*i | \bperl\s+-\w*i
  | \bsystemctl\s+(?:\S+\s+)*(?:enable|disable|mask|unmask|edit|set-default|link|preset)\b
  | \b(?:make|ninja|meson|cmake)\b[^;&|]*\binstall\b
  | \btar\s+(?:-\w*x|x)
  | \befibootmgr\b[^;&|]*\s(?:--(?:create|delete|bootorder|bootnext|active|inactive)|-[cBbonNaAt]\b)
""", re.X)
# Programs that write — but only when they are actually run (in command position),
# so a list like `for b in passwd useradd` or a path like /etc/passwd doesn't count.
WRITE_PROGS = (r"cp|mv|rm|install|ln|chmod|chown|chgrp|touch|truncate|shred|unlink|rmdir|patch|dd|"
               r"useradd|usermod|userdel|groupadd|groupmod|groupdel|gpasswd|passwd|chpasswd|chsh|chage|vipw|vigr|visudo|pwconv|grpconv|"
               r"grub-(?:install|mkconfig|set-default|reboot|editenv|mkimage)|update-grub|mkinitcpio|dracut|bootctl|"
               r"mount|umount|swapon|swapoff|mkswap|losetup|modprobe|insmod|rmmod|depmod")
CMD_POS = re.compile(r"""(?:^|[;&|(`\n{]|\bdo|\bthen|\belse|\bsudo(?:\s+-\S+)*|\bchroot\s+\S+(?:\s+/usr/bin/env(?:\s+-\S+)*(?:\s+\w+=\S*)*)?|-c\s+["']|\bxargs(?:\s+-\S+)*|\bexec|\btime|\bnohup)\s*(?:\w+=\S*\s+)*(?:/usr)?(?:/s?bin/)?(?:""" + WRITE_PROGS + r""")\b""")

def writes(t):
    t = re.sub(r"\bfor\s+\w+\s+in\b[^;\n]*", "for x in LIST", t)   # loop word-lists are data
    return bool(WRITE_OPS.search(t) or CMD_POS.search(t))

TOPICS = [
    (r"/etc/pam\.d|\bpam_|linux-pam", "يلمس PAM — غلطة هنا ممكن تقفلك برا LFS"),
    (r"/etc/(?:passwd|shadow|group|gshadow)\b|\b(?:useradd|usermod|userdel|passwd|chpasswd|gpasswd|vipw)\b", "يعدّل المستخدمين أو كلمات السر"),
    (r"/boot\b|vmlinuz|\bgrub|efibootmgr|bootctl|/efi\b|\bmodules_install\b", "يلمس الإقلاع أو النواة أو GRUB"),
    (r"/etc/fstab|/etc/sudoers", "يعدّل fstab أو sudoers"),
    (r"nvme0n1p[0-57-9]\b|/dev/nvme0n1\b(?!p6)", "يلمس قسم غير قسم LFS (p6)"),
    (r"/etc/systemd/network|wpa_supplicant|systemctl\s+(?:\S+\s+)*(?:disable|mask)\b", "يغيّر الشبكة الحالية أو يطفّي خدمات"),
    (r"\bmount\b|\bumount\b", "يركّب أو يفك أقسام"),
]

RM_OUTSIDE_BUILD = re.compile(r"""\brm['"]?\s+(?:-\w+\s+)*-\w*[rf]\w*\s+(?!/sources/build/[\w.+-]+(?:\s|$|[;&|'"]))""")

reasons = []
if RM_OUTSIDE_BUILD.search(text):
    reasons.append("حذف (rm -r/-f) خارج /sources/build")
if writes(text):
    reasons += [why for pat, why in TOPICS if re.search(pat, text, re.I)]

if reasons:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "⚠️ وقفة أمان: " + " · ".join(dict.fromkeys(reasons)),
    }}, ensure_ascii=False))
sys.exit(0)
