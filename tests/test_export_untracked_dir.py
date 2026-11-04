"""A new untracked directory is exported by its files, not as one unreadable `newpkg/` entry."""

from __future__ import annotations

import _support
from keelcheck import audit as audit_mod
from keelcheck import export

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def test_files_inside_untracked_dir_are_exported(scratch):
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write_charter(scratch, requirements=REQUIREMENTS)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, ratified=sha)
    _support.commit_all(scratch, "ratified")
    _support.write(scratch / "newpkg" / "mod.py", "X = 1\n")

    manifest = export.build_manifest(audit_mod.run_audit(scratch, write=False))

    assert "newpkg/mod.py" in [f["path"] for f in manifest["files"]]
    assert "newpkg/" not in [s["path"] for s in manifest["skipped"]]
