# Rufus for Mac — Create a Bootable Windows 11 USB on macOS

Create a bootable Windows or Linux USB from an ISO on an Apple Silicon or Intel Mac. No virtual machine, no Boot Camp, and no Windows PC required.

[![Fork of yaviral17/macos-rufus](https://img.shields.io/badge/fork-yaviral17%2Fmacos--rufus-blue)](https://github.com/yaviral17/macos-rufus)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![macOS 12+](https://img.shields.io/badge/macOS-12%2B-000000?style=flat-square&logo=apple&logoColor=white)](https://github.com/yaviral17/macos-rufus)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Windows 11](https://img.shields.io/badge/Windows-11-0078D6?style=flat-square&logo=windows11&logoColor=white)](https://www.microsoft.com/software-download/windows11)

**macos-rufus** is a free, open-source bootable USB creator for macOS. It is the Rufus-style tool people look for with searches such as "rufus for mac", "rufus macos", "create bootable windows 11 usb on mac", "windows 11 bootable usb mac apple silicon", "bootable usb creator macos", "iso to usb mac", and "linux bootable usb mac".

## Credits

This repository is a fork of [yaviral17/macos-rufus](https://github.com/yaviral17/macos-rufus) by [@yaviral17](https://github.com/yaviral17). All original credit goes to them. The [MIT license](LICENSE) is preserved, and the copyright notice in that file is unchanged.

Homebrew and the in-app update check follow the upstream project. See [Install](#install) for how to run **this** fork.

## Contents

- [What it does](#what-it-does)
- [Features](#features)
- [Supported systems](#supported-systems)
- [Install](#install)
- [Usage](#usage)
- [GUI](#gui)
- [Troubleshooting and FAQ](#troubleshooting-and-faq)
  - [Errno 16 Resource busy on /dev/rdisk](#resource-busy)
- [How a Windows USB is built](#how-a-windows-usb-is-built)
- [Requirements](#requirements)
- [Updating](#updating)
- [Credits](#credits-1)
- [License](#license)

## What it does

Point it at a Windows or Linux ISO and a USB stick. It lists external drives, asks you to confirm, erases the stick, and writes a layout the target PC can boot.

For Windows it formats FAT32 with an MBR partition table and copies the ISO **contents** onto the stick, including a legacy BIOS boot sector when the ISO provides one. Copying the `.iso` file itself with `dd` does not make a bootable Windows USB.

For a hybrid Linux ISO it can raw-write the image (the same idea as `dd`). For a non-hybrid Linux ISO that contains UEFI boot files, it copies those files to a FAT32 stick.

The stick is for booting a PC. This tool only offers external disks, so it does not install Windows onto the Mac's internal drive.

## Features

- Windows 11, 10, 8.1, and 7 from the menu, plus any Windows ISO you already have (including Windows 8)
- Linux menu entries for Ubuntu, Arch Linux, Kali Linux, Pop!_OS, and Omarchy, plus any ISO you already have
- Windows 10 and 11 ISO download from Microsoft, saved under `~/Downloads/macos-rufus/isos` and reused on the next run
- Resumable downloads, including a fresh link when Microsoft's URL has expired
- `install.wim` / `install.esd` larger than 4 GiB split with `wimlib` so they fit on FAT32; solid WIMs (current Windows 11 images) are re-exported to LZX first
- MBR active-partition flag and Windows FAT32 boot sector for legacy BIOS, written in Python
- Hybrid Linux ISOs written raw, with an optional read-back verify
- Non-hybrid Linux ISOs copied to FAT32, MBR or GPT, UEFI boot
- External-drive picker with name, size, and bus; you confirm before anything is erased
- Asks for an administrator password itself (no `sudo` prefix)
- Offers to `brew install wimlib` when a large WIM needs splitting
- Drag a `.iso` onto the terminal, or paste a path, including `file://` links and escaped spaces
- Optional PySide6 window (`gui.py`) on the same write path
- Retries raw `/dev/rdisk` writes when macOS remounts the stick (`Resource busy`)

## Supported systems

| System | How you get the ISO | How the USB boots |
|---|---|---|
| Windows 11 | Menu downloads it from Microsoft, or use your own file | UEFI via `efi/boot/bootx64.efi`. Windows 11 setup expects UEFI. |
| Windows 10 | Menu downloads it from Microsoft, or use your own file | UEFI and legacy BIOS |
| Windows 8.1 | Menu offers 32-bit and 64-bit direct images, or use your own file | UEFI and legacy BIOS |
| Windows 7 | Menu offers a direct 32-bit Professional image, or use your own file | Legacy BIOS. Enable CSM on the target PC. Typical Windows 7 ISOs have no UEFI boot file. |
| Windows 8 and other Windows ISOs | Choose "I already have an ISO file" | Same Windows path when the image contains `bootmgr` or `sources/install.wim` / `install.esd` |
| Ubuntu, Arch Linux, Kali Linux, Pop!_OS, Omarchy | Menu looks up a current image, or use your own file | Hybrid images: raw write, UEFI and legacy BIOS. Others: file copy, UEFI only |
| Other Linux ISOs | "I already have an ISO file" | Hybrid images raw-write. A non-hybrid image needs UEFI boot files |

The menu's Windows 7 and 8.1 entries download fixed images (archive.org), not a live Microsoft catalog. Windows 10 and 11 use Microsoft's download page.

Apple Silicon and Intel Macs both run the tool. The USB they produce is a PC boot disk. An Apple Silicon Mac does not boot a standard x64 Windows stick.

## Install

### Homebrew installs upstream

```bash
brew install yaviral17/macos-rufus/macos-rufus
macos-rufus
```

That formula tracks [yaviral17/macos-rufus](https://github.com/yaviral17/macos-rufus). It does not install this fork, so it does not include the `/dev/rdisk` resource-busy fix below. `wimlib` is pulled in as a dependency of the formula.

### Run this fork

```bash
git clone https://github.com/RyanAnthonyGibo/macos-rufus.git
cd macos-rufus
python3 -m pip install -r requirements.txt
python3 rufus.py
```

On a Mac where system `pip` is blocked, install into a virtual environment and run the same script:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 rufus.py
```

The script asks for your password when it needs root. You do not prefix it with `sudo`.

The first Windows 10 or 11 download offers to run `python3 -m playwright install chromium` (one-time, about 150–300 MB) so it can get past Microsoft's download-page bot check. Large `install.wim` files need `wimlib` (`brew install wimlib`); the script offers to install it.

## Usage

```bash
python3 rufus.py
```

```
╭──────────────────────────────────────────────────────────────╮
│  macos-rufus  —  Windows & Linux bootable USB creator        │
│  macOS · UEFI + Legacy BIOS · Win7/8/8.1/10/11 · Ubuntu/…    │
╰──────────────────────────────────────────────────────────────╯
```

1. Pick an OS, or choose "I already have an ISO file" and give the path. Drag the file in from Finder if you like.
2. The tool lists external USB drives (device, name, size, bus). Pick one.
3. Confirm the erase. The stick is wiped.
4. For Windows it mounts the ISO, formats the stick as FAT32/MBR, writes boot sectors, copies the files, and splits `install.wim` when it is over 4 GiB.
5. For a hybrid Linux ISO, choose the raw write (and optional verify) or fall back to file copy. Non-hybrid images with UEFI files use file copy and ask for MBR or GPT plus a volume label.
6. Unplug the stick when it says it is safe. On the PC, open the firmware boot menu and select the USB entry.

```bash
python3 rufus.py --version
python3 rufus.py --check-update
python3 rufus.py --update
```

`--check-update` and `--update` look at upstream releases. See [Updating](#updating).

## GUI

`gui.py` is a PySide6 wizard on the same `rufus.py` operations: pick an OS, download or browse, pick a USB drive, confirm, watch the flash.

```bash
python3 -m pip install -r requirements.txt
python3 gui.py
```

The window stays unprivileged. The flash step runs `rufus_worker.py` as root through macOS's administrator-password dialog.

A double-clickable app is optional and needs `py2app`, which is not in `requirements.txt`:

```bash
python3 -m pip install py2app
python3 setup.py py2app
open dist/macos-rufus.app
```

## Troubleshooting and FAQ

<a id="resource-busy"></a>

### Error: [Errno 16] Resource busy: '/dev/rdiskN'

Seen on macOS (including Apple Silicon, upstream 1.3.0 from Homebrew) right after the stick is formatted. The log shows `Writing boot sectors...` and then:

```text
Error: [Errno 16] Resource busy: '/dev/rdisk13'
```

The traceback runs `main()` → `set_mbr_active_partition()` → `open(..., "r+b")` on `/dev/rdiskN`.

macOS DiskArbitration remounts the new FAT32 volume immediately after `diskutil unmountDisk`. The raw disk is busy while that volume is mounted. A read-only open can succeed, and the following write open fails with Errno 16.

This fork force-unmounts and retries the MBR write, the Windows boot-sector write, and Linux raw ISO writes on one file descriptor (`pread` / `pwrite` or a single read-write fd), so the volume cannot remount between the read and the write. If the MBR flag or the FAT32 boot sector still cannot be written, the tool prints a warning and continues. Those sectors matter for legacy BIOS. Windows 8.1, 10, and 11 boot with UEFI from `efi/boot/bootx64.efi` and do not need them. A Linux raw write still stops if the disk never frees up, because that write is the entire image.

`brew install` does not include this fix. Clone this fork and run `python3 rufus.py` as in [Install](#install).

If a warning still appears, quit Disk Utility and anything else using the stick, then run the tool again. Legacy BIOS (Windows 7, and older PCs) needs those sectors; UEFI does not.

### install.wim is larger than 4 GB (FAT32)

FAT32 cannot store a file of 4 GiB or more. Windows 11's `sources/install.wim` is often bigger than that. macos-rufus calls `wimlib-imagex split` and writes `install.swm`, `install2.swm`, and so on, in 3800 MB pieces. Windows Setup reads the split set itself.

Some Windows 11 images store a solid WIM, which `wimlib` cannot split directly. The tool re-exports it to a normal LZX WIM in a temporary directory, then splits that. That step needs free space on the Mac on the order of the WIM size, and it is checked before the USB is erased.

If splitting fails, install wimlib yourself (`brew install wimlib`) and check free disk space. A Linux file-copy (non-hybrid) stick is also FAT32: a single file over 4 GiB in that ISO stops the copy. Hybrid Linux images are raw-written, so that per-file limit does not apply.

### UEFI and legacy BIOS

- **UEFI.** Modern PCs, and every Windows 11 install, boot `efi/boot/bootx64.efi` from the FAT32 partition. In the firmware boot menu, choose the USB entry that is marked UEFI. Windows 11 does not need the MBR active flag.
- **Legacy BIOS / CSM.** Older PCs boot the MBR, then the FAT32 volume boot record, then `bootmgr`. The tool sets the first MBR partition active (`0x80`) and, when `boot/bootsect.dat` is in the ISO, merges that Windows boot sector with the FAT32 BIOS parameter block diskutil wrote. Windows 7 ISOs usually need CSM enabled on the target PC.
- **Secure Boot.** Turn it off if Windows Setup does not start, and turn it back on after install if you want it.
- **Which entry to pick.** Windows 8.1, 10, and 11: the UEFI USB entry. Windows 7: the legacy / CSM USB entry.

### Apple Silicon and Intel

The script is Python and runs on Apple Silicon (M1 and later) and on Intel Macs.

"Windows 11 bootable USB on Mac Apple Silicon" means building the stick **on** that Mac for a PC. The Mac itself is not the machine that boots the stick. Apple Silicon Macs do not boot official x64 Windows from USB. Intel Macs are the same from this tool's point of view: it writes an external PC installer, and it never targets the internal disk. Installing Windows onto an Intel Mac's internal drive is Boot Camp's job, not this program's.

Use a USB stick the ISO fits on. 16 GB is a practical size for Windows 11.

### The USB does not boot on the PC

1. Open the firmware boot menu (often F12, F2, Esc, or Del).
2. For Windows 8.1, 10, and 11, select the **UEFI** USB entry.
3. For Windows 7, enable CSM / legacy boot and select the legacy USB entry.
4. If Setup does not launch, disable Secure Boot for the install.
5. Rewrite the stick if the copy was interrupted. A half-written FAT32 volume will not boot.

### No external USB drives detected

The picker uses `diskutil list` limited to external physical disks. Internal drives are omitted on purpose. If the stick is missing, check the cable and port, confirm it shows up in Disk Utility, and run `diskutil list`.

### Automatic Windows download failed

Windows 10 and 11 links are fetched by driving Microsoft's download page in headless Chromium, because a plain HTTP client is blocked. Install the browser with `python3 -m playwright install chromium`, confirm `microsoft.com` loads, or download the ISO yourself and pass the path when asked.

Windows 7 and 8.1 in the menu are direct image links. If one of those fails, supply your own ISO.

### Pasted text shows `^[[200~` or `00~`, or a dropped path is "not found"

That is the terminal's bracketed-paste wrapping. The prompts strip those markers. If a path is still rejected, the message quotes it exactly as received; include that line in a bug report.

### hdiutil: attach failed

The ISO may be incomplete, or already mounted. Compare its size with the download, eject any existing mount, and try again. Cleanup uses `hdiutil detach -force` and retries when the mount is busy.

### The password prompt never appears

Run `python3 rufus.py` or `macos-rufus` directly. The process re-executes itself with `sudo` and macOS asks for the password. Starting it under `sudo` yourself is unnecessary.

### Garbled box-drawing characters

The terminal is not using UTF-8. `export LANG=en_US.UTF-8` and run the tool again.

## How a Windows USB is built

1. Mount the ISO read-only with `hdiutil`.
2. Erase the external stick as FAT32 with an MBR partition map (`diskutil eraseDisk`).
3. Force-unmount and set the first MBR partition active, retrying if `/dev/rdiskN` is busy.
4. If `boot/bootsect.dat` exists, merge it with the FAT32 BIOS parameter block (bytes 3–89 stay as diskutil wrote them; the jump and the boot code come from the ISO) and write that sector to the partition. Windows 8.1 and newer images sometimes omit this file; UEFI boot still works.
5. Copy every file except `sources/install.wim` and `sources/install.esd` with four threads.
6. Copy the WIM, or split it when it is over 4 GiB.
7. Force-unmount the stick.

MBR + FAT32 is the Windows layout because UEFI boots the FAT32 EFI file from an MBR disk, and legacy BIOS needs an MBR. Linux file-copy mode can use GPT instead. Linux hybrid mode overwrites the whole disk with the ISO.

## Requirements

| Requirement | Notes |
|---|---|
| macOS | 12 Monterey or later, Apple Silicon or Intel. The project documents 12+ as the floor. |
| Python | 3.11+ |
| USB stick | Large enough for the ISO. 16 GB is a practical minimum for Windows 11. |
| Homebrew | Used to install `wimlib` when a WIM must be split. Optional if you already have `wimlib-imagex` on `PATH` or your image has no oversized WIM. |
| Network | Only for downloads and the upstream update check |

Built-in macOS tools used: `diskutil`, `hdiutil`. Python packages are listed in `requirements.txt` (`rich`, `requests`, `playwright`, `PySide6`).

## Updating

On startup the tool asks GitHub, at most once a day, whether [yaviral17/macos-rufus](https://github.com/yaviral17/macos-rufus) has a release newer than the version in this tree (`_GITHUB_REPO` in `rufus.py`). That check is upstream by design.

- A Homebrew install updates with `brew upgrade macos-rufus` (upstream).
- A git clone updates with `git pull` **of whatever remote that clone uses**. This fork's clone pulls this fork, which may not match the upstream version the check just offered.
- If the install method is unclear, or the tree has local changes, it prints the upstream release URL and leaves the files alone.

To stay on this fork's resource-busy fix, run it from this clone rather than switching over to the Homebrew formula.

## Project layout

```
macos-rufus/
├── rufus.py           # CLI and shared disk, download, and boot-sector code
├── rufus_worker.py    # Root helper the GUI launches for the flash step
├── gui.py             # PySide6 wizard
├── setup.py           # optional py2app build
├── requirements.txt
├── tests/             # unit tests; they do not write to real disks
├── CHANGELOG.md
├── LICENSE            # MIT, copyright (c) 2026 yaviral17
└── README.md
```

## Credits

This repository is a fork of [yaviral17/macos-rufus](https://github.com/yaviral17/macos-rufus) by [@yaviral17](https://github.com/yaviral17). All original credit goes to them. The software, including this fork's changes, remains under the MIT license they chose. Their copyright notice in [LICENSE](LICENSE) is preserved.

Upstream is the source of the Windows and Linux USB workflow, the Microsoft ISO download, the WIM split, the GUI, and the boot-sector layout. This fork's change is the raw-disk retry described in the [resource-busy FAQ](#resource-busy) and in [CHANGELOG.md](CHANGELOG.md).

Also:

- [Rufus](https://rufus.ie) — the Windows USB tool this project is named after
- [wimlib](https://wimlib.net) — splits and exports Windows images on macOS
- [rich](https://github.com/Textualize/rich) — terminal layout and progress

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2026 yaviral17. All original credit goes to [@yaviral17](https://github.com/yaviral17).
