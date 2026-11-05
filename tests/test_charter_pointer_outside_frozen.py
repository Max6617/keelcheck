"""A `Ratified at:` or `Review:` line quoted inside the frozen original is not the pointer."""
import json

import _support


def test_pointer_inside_frozen_original_is_ignored(tmp_path):
    path = _support.write(
        tmp_path / "CHARTER.md",
        _support.charter_text(
            frozen="we said Ratified at: 1234567abc and Review: required back then",
            ratified="89abcdef0123",
        ),
    )
    proc = _support.charter_cli(path)
    data = json.loads(proc.stdout)
    assert data["ratified_at"] == "89abcdef0123"
    assert data["review_required"] is False
