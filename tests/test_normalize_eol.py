"""An eol attribute with text unspecified makes the path text, as in git."""

from __future__ import annotations

import hashlib

import _support
from keelcheck import normalize


def test_eol_alone_normalizes_crlf_to_lf(scratch):
    _support.init_repo(scratch, commit=False)
    _support.git(scratch, "config", "core.autocrlf", "false")
    _support.write(scratch / ".gitattributes", "*.md eol=lf\n")
    (scratch / "a.md").write_bytes(b"x\r\ny\r\n")

    assert normalize.content_hash(scratch, "a.md")[0] == "sha256:" + hashlib.sha256(b"x\ny\n").hexdigest()
