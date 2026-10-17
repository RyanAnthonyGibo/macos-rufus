# Changelog

Changes in this fork of [yaviral17/macos-rufus](https://github.com/yaviral17/macos-rufus). The upstream version these notes sit on is 1.3.0. Original copyright remains with yaviral17; see [LICENSE](LICENSE).

## Unreleased

### Fixed

- Creating a Windows USB no longer stops with `Error: [Errno 16] Resource busy: '/dev/rdiskN'` immediately after "Writing boot sectors...". After `diskutil eraseDisk`, DiskArbitration can remount the new FAT32 volume before the raw device is opened for writing (a read-only open can still succeed). The MBR active-flag write, the Windows FAT32 boot-sector write, and Linux raw ISO writes now force-unmount and retry on a single file descriptor. If the legacy BIOS sectors still cannot be written, the tool warns and continues: UEFI boot for Windows 8.1, 10, and 11 does not need them. A raw Linux image write still fails if the disk never becomes free, because that write is the whole USB.
- ISO cleanup retries `hdiutil detach -force` when the first attempt reports the volume busy.
