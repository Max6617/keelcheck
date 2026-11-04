"""$GIT_DIR/info/attributes takes precedence over a working-tree .gitattributes, as in git."""

from __future__ import annotations

import _support
from keelcheck import normalize


def _setup(scratch):
    _support.write(scratch / ".gitattributes", "* text\n")
    (scratch / "a.md").write_bytes(b"one\r\ntwo\r\n")
    _support.init_repo(scratch)
    info = scratch / ".git" / "info"
    info.mkdir(exist_ok=True)
    (info / "attributes").write_text("a.md -text\n")


def test_info_attributes_overrides_gitattributes(scratch):
    _setup(scratch)

    assert normalize.attributes_for(scratch, "a.md").text == "false"


def test_content_hash_does_not_raise_for_crlf_file(scratch):
    _setup(scratch)

    normalize.content_hash(scratch, "a.md")
