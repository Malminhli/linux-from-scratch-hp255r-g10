---
name: lfs-chroot
description: Safely back up, mount, enter, and leave the LFS chroot on /dev/nvme0n1p6 from the Arch host. Use before any build or write to the LFS system.
---

# LFS chroot from Arch

Target: `/dev/nvme0n1p6` → mount point `/mnt/lfs`. **Only this partition.** Never mount p1/p2/p3/p4/p5/p7/p8 read-write.

## 1. Backup (once, before the first write — Mohammed runs it, needs sudo)

```bash
mkdir -p ~/lfs-backup
sudo mount -o ro /dev/nvme0n1p6 /mnt/p6 2>/dev/null || true
sudo tar --xattrs --acls --numeric-owner -I 'zstd -T0 -3' \
  -cpf ~/lfs-backup/lfs-p6-$(date +%F).tar.zst -C /mnt/p6 .
ls -lh ~/lfs-backup/
```
Restore (emergency only, with Mohammed's approval): mount p6 rw on /mnt/lfs, wipe, `tar -xpf ... -C /mnt/lfs`.

## 2. Mount read-write + virtual filesystems

If it is mounted read-only somewhere (e.g. `/mnt/p6`), unmount that first: `sudo umount /mnt/p6`.

```bash
export LFS=/mnt/lfs
sudo mkdir -p $LFS
findmnt $LFS >/dev/null || sudo mount /dev/nvme0n1p6 $LFS
sudo mount --bind /dev $LFS/dev
sudo mount -t devpts devpts -o gid=5,mode=0620 $LFS/dev/pts
sudo mount -t proc proc $LFS/proc
sudo mount -t sysfs sysfs $LFS/sys
sudo mount -t tmpfs tmpfs $LFS/run
[ -h $LFS/dev/shm ] && sudo install -d -m 1777 $LFS$(realpath /dev/shm) || sudo mount -t tmpfs -o nosuid,nodev tmpfs $LFS/dev/shm
sudo cp -L /etc/resolv.conf $LFS/etc/resolv.conf   # network inside chroot
```
Always check with `findmnt -R $LFS` that nothing is mounted twice.

## 3. Run commands inside

Non-interactive (what Claude Code should use — one command per call):
```bash
sudo chroot "$LFS" /usr/bin/env -i HOME=/root TERM="$TERM" \
  PATH=/usr/bin:/usr/sbin MAKEFLAGS="-j$(nproc)" \
  /bin/bash --login -c 'cd /sources && <commands>'
```
Inside, `/sources` holds tarballs, `/sources/build` is the scratch dir, `/sources/logs` holds build logs.

## 4. Leave and unmount (end of every session, before rebooting into LFS)

```bash
sudo umount -R $LFS/dev/shm $LFS/dev/pts $LFS/dev $LFS/proc $LFS/sys $LFS/run 2>/dev/null
sudo umount $LFS
findmnt | grep -c lfs   # must be 0
```

## sudo note

Claude Code cannot type a sudo password. Mohammed either approves each command and enters the password in his own terminal, or creates a temporary rule (remove it when the project ends):
```bash
echo 'mohammed ALL=(ALL) NOPASSWD: /usr/bin/mount, /usr/bin/umount, /usr/bin/chroot, /usr/bin/tar, /usr/bin/cp, /usr/bin/mkdir, /usr/bin/install' | sudo tee /etc/sudoers.d/90-lfs-build
sudo chmod 440 /etc/sudoers.d/90-lfs-build
# when done:  sudo rm /etc/sudoers.d/90-lfs-build
```
