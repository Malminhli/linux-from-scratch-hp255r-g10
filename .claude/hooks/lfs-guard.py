#!/usr/bin/env python3
"""LFS safety guard (PreToolUse hook for Bash).

Stops and asks Mohammed ONLY when a command both
  1) actually changes something (writes, installs, deletes, edits users/services/boot), and
  2) touches a sensitive area (PAM, users, boot/GRUB/kernel, fstab/sudoers, other partitions,
     network setup) — or deletes outside /sources/build.
Pure reads never stop, however they are written. Prints a PreToolUse 'ask' decision or nothing.

After ANY change here run:  python3 -I .claude/hooks/test_guard.py   (must report all passed).
"""
import json, re, sys

try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    sys.exit(0)

text = cmd.replace("2>&1", " ").replace("2>/dev/null", " ").replace("&>/dev/null", " ").replace(">/dev/null", " ")

# ---- Inline interpreter code (python -c, perl -e, awk '...', python/perl heredocs) is DATA ----
# A `>` inside `awk '$3 > 100'` or `python3 -c "print(a > b)"` is not a shell redirect.
# Such code is blanked out before the checks below — unless it writes, deletes or spawns
# commands, in which case it is kept (so its paths are checked) and counts as a write.
# Only interpreters in command position count, so `grep "python3 -c" f > x` is not mistaken for one.
_BOUND = (r"""(?:^|[;&|(`\n{]|\b(?:do|then|else|exec|time|nohup|sudo|env|xargs)\b(?:\s+-\S+)*(?:\s+\w+=\S*)*"""
          r"""|\bchroot\s+\S+|-c\s+["'])\s*(?:\w+=\S*\s+)*(?:[\w./-]*/)?""")
_HEADS = [
    ("py",   re.compile(_BOUND + r"""python[\d.]*(?:\s+-[A-Za-z]+)*?\s+-[A-Za-z]*c\s*""")),
    ("perl", re.compile(_BOUND + r"""perl(?:\s+-\S+)*?\s+-[A-Za-z]*[eE]\s*""")),
    ("awk",  re.compile(_BOUND + r"""[gmn]?awk(?:\s+-(?:[Fv]\s*(?:'[^']*'|"[^"]*"|\S+)|-?[\w-]+(?:=\S+)?))*\s+""")),
]
_HEREDOC = re.compile(_BOUND + r"""(python[\d.]*|perl)\b[^\n]*?<<-?\s*(['"]?)(\w+)\2[^\n]*\n""")
_DANGER = {
    "py": re.compile(r"""\bopen\s*\([^)]*?['"][rwxabt+]*[wax+][rwxabt+]*['"]|\.write_(?:text|bytes)\s*\(
        | \bos\.(?:remove|unlink|rmdir|removedirs|rename|renames|replace|system|popen|spawn\w*|exec\w*|
                  chmod|chown|lchown|truncate|mkdir|makedirs|symlink|link|mknod|open)\b
        | \bO_(?:WRONLY|RDWR|CREAT|TRUNC|APPEND)\b | \bshutil\b | \bsubprocess\b | \bpty\b | \bctypes\b
        | \bsystem\s*\( | \bunlink\s*\( | \.(?:rmdir|rename|replace|touch|symlink_to|chmod|unlink)\s*\(""", re.X),
    "perl": re.compile(r"""\bopen\w*\b[^;]*?(?:['"]\s*(?:\+?>|\+<|\|)|\|\s*['"])
        | \b(?:unlink|rename|rmdir|mkdir|chmod|chown|symlink|link|truncate|system|exec|qx|syswrite|rmtree)\b
        | ` | \bFile::(?:Copy|Path|Temp)\b | \bIPC::""", re.X),
    "awk": re.compile(r"""\bprintf?\b[^;}\n]*?(?<![<>=!])>(?!=) | \bprintf?\b[^;}\n]*?(?<!\|)\|(?!\|)
        | (?<!\|)\|(?!\|)\s*getline | \|& | \bsystem\s*\(""", re.X),
}

def _quoted_at(t, i):
    """(start, end) of the quoted shell word starting at t[i] — '…', "…" or \\"…\\" — else None.
    Errs toward ending early, which only leaves more text for the checks (never less)."""
    if t.startswith('\\"', i):
        j = t.find('\\"', i + 2)
        return (i, j + 2) if j != -1 else None
    if t[i:i+1] == "'":
        j = t.find("'", i + 1)
        return (i, j + 1) if j != -1 else None
    if t[i:i+1] == '"':
        j = i + 1
        while j < len(t):
            if t[j] == "\\":
                j += 2
                continue
            if t[j] == '"':
                return (i, j + 1)
            j += 1
    return None

def neutralize_inline_code(t):
    """Return (text with harmless inline code blanked, True if any inline code writes/deletes/spawns)."""
    spans = []
    for lang, head in _HEADS:
        for m in head.finditer(t):
            q = _quoted_at(t, m.end())
            if q:
                spans.append((q[0], q[1], lang))
    for m in _HEREDOC.finditer(t):
        end = re.compile(r"\n[ \t]*" + re.escape(m.group(3)) + r"[ \t]*(?=\n|$)").search(t, m.end() - 1)
        if end:
            spans.append((m.end(), end.start(), "perl" if m.group(1) == "perl" else "py"))
    spans.sort()
    out, pos, risky = [], 0, False
    for s, e, lang in spans:
        if s < pos:                       # nested inside a span already handled
            continue
        code = t[s:e]
        if lang == "awk":                 # awk string literals ("a -> b") can't redirect; the target of
            code = re.sub(r'"(?:[^"\\]|\\.)*"', '""', code)   # `print > "f"` stays visible as `> ""`
        if _DANGER[lang].search(code):
            risky = True                  # keep it: its paths must still be checked
            continue
        out.append(t[pos:s]); out.append(" CODE "); pos = e
    out.append(t[pos:])
    return "".join(out), risky

text, inline_code_writes = neutralize_inline_code(text)

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

# Destructive no matter where: filesystem/partition tools, find -delete, rm --recursive/--force.
DESTRUCTIVE = re.compile(r"""\b(?:mkfs[\w.]*|mke2fs|mkswap|wipefs|blkdiscard|sfdisk|cfdisk|gdisk|sgdisk|fdisk|parted|cryptsetup)\b
    | \bdd\b[^;&|]*\bof=
    | \bfind\b[^;&|]*\s-(?:delete|exec(?:dir)?\s+(?:/usr/bin/|/bin/)?(?:rm|shred|unlink|mv|chmod|chown)\b)
    | \bshred\b""", re.X)
import shlex
BUILD_PATH = re.compile(r"^/sources/build/[\w.+-]+/?$")
def rm_is_risky(t):
    """True if any rm call is recursive/forced and targets anything other than plain /sources/build/<dir> paths."""
    for m in re.finditer(r"""(?:^|[;&|(`\n{"']|\bdo|\bthen|\bsudo|\bxargs)\s*(?:/usr)?(?:/bin/)?['"]?rm['"]?(?=\s|$)([^;&|\n`"')]*)""", t):
        try:
            args = shlex.split(m.group(1))
        except ValueError:
            args = m.group(1).split()
        flags = [a for a in args if a.startswith("-")]
        paths = [a for a in args if not a.startswith("-")]
        strong = any(f in ("--recursive", "--force", "--no-preserve-root") or
                     (not f.startswith("--") and re.search(r"[rRf]", f)) for f in flags)
        if strong and (not paths or not all(BUILD_PATH.match(p) for p in paths)):
            return True
    return False


reasons = []
if DESTRUCTIVE.search(text):
    reasons.append("أمر تدميري (فورمات/تقسيم/حذف جماعي)")
if rm_is_risky(text):
    reasons.append("حذف (rm -r/-f) خارج /sources/build")
if writes(text) or inline_code_writes:
    reasons += [why for pat, why in TOPICS if re.search(pat, text, re.I)]

if reasons:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "⚠️ وقفة أمان: " + " · ".join(dict.fromkeys(reasons)),
    }}, ensure_ascii=False))
sys.exit(0)
