#!/usr/bin/env python3
"""Regression tests for lfs-guard.py: each command must produce the expected ASK / allowed decision.

Run after ANY change to the hook:   python3 -I .claude/hooks/test_guard.py
(optionally pass another hook path as the first argument). Exit code 0 = all pass.
Add a case here for every new gap or false positive before fixing it.
"""
import json, os, subprocess, sys

HOOK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "lfs-guard.py")
CH = "sudo chroot /mnt/lfs /usr/bin/env -i HOME=/root PATH=/usr/bin:/usr/sbin /bin/bash --login -c "

CASES = [
    # ---- previous 19 cases ----
    ("rm -rf /sources/build/foo /mnt/lfs/etc", "ASK"),
    ("rm --recursive --force /sources/build/foo /etc", "ASK"),
    ("rm -rf /sources/build/mesa-26.2.3", "allowed"),
    ("rm -rf /sources/build/a /sources/build/b", "allowed"),
    ('sudo chroot /mnt/lfs /bin/bash -c "rm -rf /sources/build/mesa-26.2.3"', "allowed"),
    ('sudo chroot /mnt/lfs /bin/bash -c "rm -rf /sources/build/x /usr"', "ASK"),
    ("rm -rf /sources/build/x && make -j6", "allowed"),
    ("rm -rf /sources/build/x\nmake install", "allowed"),
    ("rm -R /mnt/lfs/etc", "ASK"),
    ("rm -rf", "ASK"),
    ("rm -rf /sources/build/*", "ASK"),
    ("rm --recursive --force /mnt/lfs/etc", "ASK"),
    ("rm -r -f /mnt/lfs/etc", "ASK"),
    ("rm foo.o", "allowed"),
    ("mkfs.ext4 /dev/nvme0n1p7", "ASK"),
    ("find /mnt/lfs/etc/pam.d -delete", "ASK"),
    ("cat /etc/pam.d/login", "allowed"),
    ("docker run --rm -it img", "allowed"),
    ("git status --short", "allowed"),
    # ---- inline code that only reads: must be allowed ----
    ("awk -F: '$3 > 999' /mnt/lfs/etc/passwd", "allowed"),
    ("awk '{if ($2 > 3) print $1}' /mnt/lfs/etc/group", "allowed"),
    ("gawk -v n=5 'NF > n' /mnt/lfs/etc/shadow", "allowed"),
    ('python3 -c "import sys; print(len(sys.argv) > 1)" /mnt/lfs/etc/pam.d/login', "allowed"),
    ("python3 -I -c 'print(open(\"/mnt/lfs/etc/passwd\").read().count(\"x\") > 2)'", "allowed"),
    ("perl -ne 'print if length > 80' /mnt/lfs/etc/pam.d/system-auth", "allowed"),
    ("perl -e 'print 1 > 0' /boot/grub/grub.cfg", "allowed"),
    (CH + "'cd /sources && python3 -c \"print(1 > 0)\" /etc/pam.d/other'", "allowed"),
    (CH + "\"awk -F: '\\$3 >= 1000' /etc/passwd\"", "allowed"),
    ("python3 - <<'EOF'\nimport json\nprint(1 > 0, '/etc/pam.d/login')\nEOF", "allowed"),
    ("ls /mnt/lfs/etc/pam.d | awk '{print $1 \" -> ok\"}'", "allowed"),
    # ---- shell writes around/after benign code: must still ASK (sensitive = /boot, GRUB, kernel, other partitions) ----
    (CH + "'cat > /boot/grub/custom.cfg'", "ASK"),
    ('sudo chroot /mnt/lfs bash -c "cat > /boot/grub/x"', "ASK"),
    ('sudo chroot /mnt/lfs bash -c "cat > /etc/grub.d/40_custom <<EOF\nmenuentry x {}\nEOF"', "ASK"),
    ("python3 -c 'print(1)' > /mnt/lfs/boot/x", "ASK"),
    ("awk '{print}' /mnt/lfs/boot/grub/grub.cfg > /mnt/lfs/boot/grub/grub.cfg.new", "ASK"),
    ("python3 - <<'EOF' > /boot/grub/grub.cfg\nprint('menuentry x {}')\nEOF", "ASK"),
    ("awk '$3 > 0' /etc/group && echo x >> /mnt/lfs/boot/notes", "ASK"),
    ('grep "python3 -c" notes.txt > /mnt/lfs/boot/x', "ASK"),
    # ---- inline code that writes/deletes/spawns: must ASK on sensitive paths ----
    ("python3 -c \"open('/mnt/lfs/boot/grub/grub.cfg','w').write('x')\"", "ASK"),
    ("python3 -c \"open('/etc/grub.d/40_custom', mode='a').write('menuentry')\"", "ASK"),
    ("python3 -c \"import os; os.remove('/mnt/lfs/boot/vmlinuz-6.18.10-lfs-amdgpu')\"", "ASK"),
    ("python3 -c \"import shutil; shutil.rmtree('/mnt/lfs/boot')\"", "ASK"),
    ("python3 -c \"import subprocess; subprocess.run(['mkfs.ext4','/dev/nvme0n1p7'])\"", "ASK"),
    ("python3 -c \"import os; os.system('grub-mkconfig -o /boot/grub/grub.cfg')\"", "ASK"),
    ("python3 - <<'EOF'\nopen('/boot/grub/grubenv','w').write('')\nEOF", "ASK"),
    ("perl -e 'open(F, \">/mnt/lfs/boot/x\"); print F 1'", "ASK"),
    ("perl -e 'unlink \"/mnt/lfs/boot/vmlinuz-6.18.10-lfs-hptarget.bak\"'", "ASK"),
    ("perl -pi -e 's/ro/rw/' /etc/grub.d/40_custom", "ASK"),
    ("awk '{print > \"/mnt/lfs/boot/x\"}' /dev/null", "ASK"),
    ("awk 'BEGIN{system(\"rm -rf /mnt/lfs/etc\")}'", "ASK"),
    (CH + "\"python3 -c \\\"open('/boot/x','w')\\\"\"", "ASK"),
    # ---- writing code to a non-sensitive place: allowed (same rule as shell writes) ----
    ("python3 -c \"open('/tmp/x.txt','w').write('hi')\"", "allowed"),
    # ---- policy since 2026-11-22: PAM, users/passwords, network, mount, fstab/sudoers do NOT stop ----
    (CH + "'cat > /etc/pam.d/login <<\"EOF\"\nauth include system-auth\nEOF'", "allowed"),
    ("python3 -c \"open('/mnt/lfs/etc/pam.d/login','w').write('x')\"", "allowed"),
    ("perl -pi -e 's/x/y/' /mnt/lfs/etc/pam.d/system-auth", "allowed"),
    (CH + "'useradd -m -G video,audio,input,wheel mohammed'", "allowed"),
    (CH + "'echo root:x | chpasswd'", "allowed"),
    (CH + "'usermod -aG video mohammed && passwd -S mohammed'", "allowed"),
    ("echo 'render:x:28:' >> /mnt/lfs/etc/group", "allowed"),
    ("sudo mount --bind /dev /mnt/lfs/dev && sudo mount -t proc proc /mnt/lfs/proc", "allowed"),
    ("sudo umount /mnt/lfs/dev/shm /mnt/lfs/dev/pts", "allowed"),
    (CH + "'systemctl disable systemd-networkd && systemctl enable NetworkManager'", "allowed"),
    ("echo 'Defaults timestamp_timeout=5' >> /mnt/lfs/etc/sudoers.d/10-x", "allowed"),
    ("echo '/dev/nvme0n1p6 / ext4 defaults 1 1' > /mnt/lfs/etc/fstab", "allowed"),
    # ---- policy since 2026-11-22: these DO still stop ----
    ("sudo mount /dev/nvme0n1p7 /mnt/arch", "ASK"),
    ("sudo mount -o rw /dev/nvme0n1p1 /mnt/efi", "ASK"),
    ("sudo cp arch/x86/boot/bzImage /mnt/lfs/boot/vmlinuz-6.18.10-lfs-desktop", "ASK"),
    ("make modules_install INSTALL_MOD_PATH=/mnt/lfs", "ASK"),
    ("sudo grub-mkconfig -o /boot/grub/grub.cfg", "ASK"),
    ("sudo installkernel 6.18.10-lfs-desktop arch/x86/boot/bzImage System.map", "ASK"),
    ("sudo efibootmgr --bootorder 0000,0002", "ASK"),
    ("sudo dd if=/dev/zero of=/dev/nvme0n1p8 bs=1M count=1", "ASK"),
    ("rm -rf /mnt/lfs/etc/pam.d", "ASK"),
]

fail = 0
for cmd, want in CASES:
    out = subprocess.run([sys.executable, HOOK], input=json.dumps({"tool_input": {"command": cmd}}),
                         capture_output=True, text=True).stdout.strip()
    got = "ASK" if out else "allowed"
    ok = got == want
    fail += not ok
    print(f"{'ok  ' if ok else 'FAIL'} want={want:<7} got={got:<7} {cmd!r}")
print(f"\n{len(CASES) - fail}/{len(CASES)} passed")
sys.exit(1 if fail else 0)
