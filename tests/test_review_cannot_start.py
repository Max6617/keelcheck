"""A review that cannot start exits 2 (R4), never an uncaught exception's exit 1."""

from __future__ import annotations

import pytest

import _support
from keelcheck import export, normalize, review
from test_review_cli import _repo


def test_an_unbalanced_reviewer_command_exits_2_before_any_export(scratch):
    _repo(scratch)
    proc = _support.keelcheck("review", str(scratch), "--reviewer", 'python -c "print(1)')
    assert proc.returncode == 2
    assert "Traceback" not in _support.combined(proc)
    keel = scratch / ".keel"
    assert [p for p in keel.iterdir() if p.is_dir()] == []


def test_a_normalization_error_exits_2(scratch, monkeypatch):
    _repo(scratch)

    def boom(audit):
        raise normalize.NormalizationError("x")

    monkeypatch.setattr(export, "build_manifest", boom)
    assert review.main([str(scratch), "--reviewer", "python -c pass"]) == 2
