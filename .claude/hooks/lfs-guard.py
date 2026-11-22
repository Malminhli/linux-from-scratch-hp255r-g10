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

# Pure read-only commands never need a safety stop, even if they mention /boot or other partitions.
READONLY = {"ls","cat","head","tail","less","grep","egrep","rg","find","stat","file","du","df","lsblk","findmnt",
            "blkid","free","nproc","uname","lspci","lsusb","lsmod","ldd","readelf","pkg-config","wc","sort","uniq",
            "echo","printf","pwd","which","type","tree","diff","cmp","md5sum","sha256sum","journalctl","dmesg",
            "git","awk","cut","tr","column","true","test","[","realpath","readlink","basename","dirname","id","groups","date",
            "for","done","fi","command","printf","",
            "sed","zcat","zgrep","xzcat","bzcat","strings","comm","join","paste","nl","od","xxd","hexdump","jq","shopt","set","local","export","modinfo","objdump","nm","lddtree","stat","sha1sum","b2sum"}
WRITE_HINT = re.compile(r">|\btee\b|-delete\b|-exec\b|\bsed\s+-i|git\s+(push|reset|clean|checkout|rebase)")
flat = re.sub(r"\$\(|`|\)", " ; ", cmd)   # expose commands inside $( ) and backticks
parts = [p.strip() for p in re.split(r"&&|\|\||[;|\n]", flat) if p.strip()]
def prog(part):
    toks = part.split()
    while toks and ("=" in toks[0] and not toks[0].startswith("=")):  # VAR=x prefix
        toks = toks[1:]
    while toks and toks[0] in ("do","then","else","elif","if","while","until","!","{","(","time"):
        toks = toks[1:]          # look past shell keywords to the real program
        while toks and ("=" in toks[0] and not toks[0].startswith("=")):
            toks = toks[1:]
    if toks and toks[0] == "for":
        return "for"             # loop header only lists words, runs nothing
    return toks[0].rsplit("/", 1)[-1] if toks else ""
if parts and all(prog(p) in READONLY | {"cd"} for p in parts) and not WRITE_HINT.search(cmd.replace("2>&1","").replace("2>/dev/null","")):
    sys.exit(0)

hits = [why for pat, why in RISKY if re.search(pat, cmd, re.I)]
if hits:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "⚠️ وقفة أمان: " + " · ".join(dict.fromkeys(hits)),
    }}, ensure_ascii=False))
sys.exit(0)
