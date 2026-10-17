"""Raw-device writes must survive DiskArbitration remounting the USB.

macOS can return EBUSY (Errno 16, "Resource busy") on /dev/rdiskN when a
freshly formatted FAT32 volume is mounted again between unmount and open.
These tests stub diskutil and the device node; they never touch a real disk.
"""

import errno
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import rufus


class _Dev:
    def __init__(self, monkeypatch, tmp_path, *, fail_times=0, fail_errno=errno.EBUSY, fail_all=False):
        self.dest = tmp_path / "devnode"
        self.dest.write_bytes(b"\x01" * 512)
        self.opens = 0
        self.paths = []
        self.cmds = []
        real_open = os.open

        def fake_run(cmd, check=True, capture=True, **kw):
            self.cmds.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")

        def fake_open(path, flags, mode=0o777, **kw):
            if isinstance(path, str) and path.startswith("/dev/"):
                self.opens += 1
                self.paths.append(path)
                if fail_all or self.opens <= fail_times:
                    raise OSError(fail_errno, os.strerror(fail_errno), path)
                return real_open(self.dest, flags)
            return real_open(path, flags, mode)

        monkeypatch.setattr(rufus.time, "sleep", lambda *a, **k: None)
        monkeypatch.setattr(rufus, "run", fake_run)
        monkeypatch.setattr(rufus.os, "open", fake_open)


def test_raw_device_and_whole_disk_names():
    assert rufus._raw_device("/dev/disk13") == "/dev/rdisk13"
    assert rufus._raw_device("/dev/disk13s1") == "/dev/rdisk13s1"
    assert rufus._raw_device("/dev/rdisk2") == "/dev/rdisk2"
    assert rufus._whole_disk("/dev/disk13s1") == "/dev/disk13"
    assert rufus._whole_disk("/dev/disk13") == "/dev/disk13"


def test_legacy_boot_sector_notice():
    assert rufus.legacy_boot_sector_notice(True, True) is None
    mbr = rufus.legacy_boot_sector_notice(False, True)
    assert "MBR active flag" in mbr
    assert "FAT32 boot sector" not in mbr
    assert "UEFI" in mbr
    both = rufus.legacy_boot_sector_notice(False, False)
    assert "MBR active flag and FAT32 boot sector" in both


def test_mbr_flag_set_after_busy_retry(tmp_path, monkeypatch):
    dev = _Dev(monkeypatch, tmp_path, fail_times=2)
    assert rufus.set_mbr_active_partition("/dev/disk4") is True
    assert dev.opens == 3
    assert dev.paths == ["/dev/rdisk4"] * 3
    data = dev.dest.read_bytes()
    assert data[446] == 0x80
    assert data[462] == data[478] == data[494] == 0x00
    assert data[445] == data[447] == data[510] == 0x01
    assert dev.cmds.count(["diskutil", "unmountDisk", "force", "/dev/disk4"]) == 3


def test_mbr_busy_gives_up_without_raising(tmp_path, monkeypatch):
    dev = _Dev(monkeypatch, tmp_path, fail_all=True)
    assert rufus.set_mbr_active_partition("/dev/disk4") is False
    assert dev.opens == rufus._RAW_OPEN_ATTEMPTS
    assert dev.dest.read_bytes() == b"\x01" * 512


def test_mbr_non_busy_error_is_fatal(tmp_path, monkeypatch):
    dev = _Dev(monkeypatch, tmp_path, fail_all=True, fail_errno=errno.ENOENT)
    with pytest.raises(OSError) as caught:
        rufus.set_mbr_active_partition("/dev/disk4")
    assert caught.value.errno == errno.ENOENT
    assert dev.opens == 1


def test_vbr_merges_boot_code_and_keeps_bpb(tmp_path, monkeypatch):
    dev = _Dev(monkeypatch, tmp_path, fail_times=1)
    iso = tmp_path / "iso"
    (iso / "boot").mkdir(parents=True)
    new = bytearray(b"\x22" * 512)
    new[0:3] = b"\xeb\x58\x90"
    new[510:512] = b"\x55\xaa"
    (iso / "boot" / "bootsect.dat").write_bytes(new)

    assert rufus.write_windows_vbr("/dev/disk9", str(iso)) is True
    assert dev.paths[0] == "/dev/rdisk9s1"
    data = dev.dest.read_bytes()
    assert data[0:3] == b"\xeb\x58\x90"
    assert data[3:90] == b"\x01" * 87
    assert data[90:510] == b"\x22" * 420
    assert data[510:512] == b"\x55\xaa"
    assert ["diskutil", "unmount", "force", "/dev/disk9s1"] in dev.cmds
    assert ["diskutil", "unmountDisk", "force", "/dev/disk9"] in dev.cmds
    assert ["diskutil", "mount", "/dev/disk9s1"] in dev.cmds


def test_vbr_busy_skips_and_still_remounts(tmp_path, monkeypatch):
    dev = _Dev(monkeypatch, tmp_path, fail_all=True)
    iso = tmp_path / "iso"
    (iso / "boot").mkdir(parents=True)
    (iso / "boot" / "bootsect.dat").write_bytes(b"\x00" * 512)
    assert rufus.write_windows_vbr("/dev/disk9", str(iso)) is False
    assert dev.dest.read_bytes() == b"\x01" * 512
    assert ["diskutil", "mount", "/dev/disk9s1"] in dev.cmds


def test_vbr_missing_bootsect_does_not_touch_disk(tmp_path, monkeypatch):
    dev = _Dev(monkeypatch, tmp_path)
    iso = tmp_path / "iso"
    iso.mkdir()
    assert rufus.write_windows_vbr("/dev/disk9", str(iso)) is True
    assert dev.opens == 0
    assert dev.cmds == []


def test_dd_write_retries_then_verifies(tmp_path, monkeypatch):
    dev = _Dev(monkeypatch, tmp_path, fail_times=1)
    iso = tmp_path / "linux.iso"
    payload = b"iso-image" * 50 + b"tail"  # not a multiple of 512
    iso.write_bytes(payload)
    seen = []
    assert rufus.dd_write_iso(
        iso, "/dev/disk3",
        progress_cb=lambda done, total: seen.append((done, total)),
        verify=True,
        verify_cb=lambda done, total: seen.append(("v", done, total)),
    ) is None
    padded = payload + b"\0" * ((-len(payload)) % 512)
    assert dev.dest.read_bytes()[:len(padded)] == padded
    assert seen[0] == (len(payload), len(payload))
    assert seen[-1] == ("v", len(payload), len(payload))
    assert dev.paths[0] == "/dev/rdisk3"
    # one failed open + write open + verify open
    assert dev.opens == 3
    assert dev.cmds[-1] == ["diskutil", "unmountDisk", "force", "/dev/disk3"]


def test_dd_write_stays_fatal_when_disk_stays_busy(tmp_path, monkeypatch):
    dev = _Dev(monkeypatch, tmp_path, fail_all=True)
    iso = tmp_path / "linux.iso"
    iso.write_bytes(b"xyz")
    with pytest.raises(RuntimeError, match="(?i)resource busy"):
        rufus.dd_write_iso(iso, "/dev/disk3", progress_cb=lambda done, total: None)
    assert dev.opens == rufus._RAW_OPEN_ATTEMPTS
    assert dev.dest.read_bytes() == b"\x01" * 512


def test_unmount_iso_retries_resource_busy(monkeypatch):
    calls = {"n": 0}

    def fake_run(cmd, check=True, capture=True, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            return subprocess.CompletedProcess(cmd, 1, "", "hdiutil: detach failed - Resource busy")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(rufus.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(rufus, "run", fake_run)
    rufus.unmount_iso("/Volumes/WINISO")
    assert calls["n"] == 2


def test_unmount_iso_treats_missing_mount_as_done(monkeypatch):
    calls = {"n": 0}

    def fake_run(cmd, check=True, capture=True, **kw):
        calls["n"] += 1
        return subprocess.CompletedProcess(
            cmd, 1, "", "hdiutil: detach failed - No such file or directory")

    monkeypatch.setattr(rufus, "run", fake_run)
    rufus.unmount_iso("/Volumes/WINISO")
    assert calls["n"] == 1
