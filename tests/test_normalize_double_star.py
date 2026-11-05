"""A **/ in a .gitattributes pattern also matches at depth zero, as in git."""

from __future__ import annotations

import hashlib

import _support
from keelcheck import normalize


def test_leading_double_star_matches_root_file(scratch):
    _support.init_repo(scratch, commit=False)
    _support.git(scratch, "config", "core.autocrlf", "true")
    _support.write(scratch / ".gitattributes", "**/*.txt -text\n")
    (scratch / "a.txt").write_bytes(b"a\r\nb\r\n")

    assert normalize.attributes_for(scratch, "a.txt").text == "false"

    proc = _support.keelcheck("gate", "hash", "a.txt", "--repo", str(scratch))
    assert proc.returncode == 0
    assert proc.stdout.strip() == "sha256:" + hashlib.sha256(b"a\r\nb\r\n").hexdigest()


def test_middle_double_star_matches_zero_and_more_directories(scratch):
    _support.init_repo(scratch, commit=False)
    _support.write(scratch / ".gitattributes", "a/**/b.txt -text\n")

    assert normalize.attributes_for(scratch, "a/b.txt").text == "false"
    assert normalize.attributes_for(scratch, "a/x/b.txt").text == "false"
