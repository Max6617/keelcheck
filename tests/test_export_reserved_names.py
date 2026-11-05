"""A repository file named like a file the export writes is skipped with a reason, not overwritten."""

from __future__ import annotations

import _support
from keelcheck import audit as audit_mod
from keelcheck import export


def test_repo_file_named_like_an_export_file_is_skipped(scratch):
    _support.write(scratch / "tools" / "gate.py", "print('ok')\n")
    gates = [("g", "tools/gate.py", _support.hash_file(scratch / "tools" / "gate.py"))]
    requirements = [("R1", "the gate runs", "gate: g", "—", "**met**")]
    _support.write_charter(scratch, requirements=requirements, gates=gates)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=requirements, gates=gates, ratified=sha)
    _support.commit_all(scratch, "ratified")
    _support.write(scratch / "FROZEN-ORIGINAL.md", "not keelcheck's frozen block\n")
    _support.commit_all(scratch, "add a file with a reserved name")

    manifest = export.build_manifest(audit_mod.run_audit(scratch, write=False))

    assert "FROZEN-ORIGINAL.md" not in [f["path"] for f in manifest["files"]]
    reasons = {s["path"]: s["reason"] for s in manifest["skipped"]}
    assert reasons["FROZEN-ORIGINAL.md"].startswith("reserved")
