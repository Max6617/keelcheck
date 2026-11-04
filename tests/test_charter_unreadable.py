"""`keelcheck charter` exits 2 on a path it cannot read, with no traceback (D12)."""

from __future__ import annotations

from _support import keelcheck


def _assert_unreadable(proc):
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert "keelcheck: cannot read" in proc.stderr


def test_directory_exits_2(scratch):
    _assert_unreadable(keelcheck("charter", str(scratch)))


def test_undecodable_file_exits_2(scratch):
    bad = scratch / "bad.md"
    bad.write_bytes(b"\xff\xfe# x\n")
    _assert_unreadable(keelcheck("charter", str(bad)))
