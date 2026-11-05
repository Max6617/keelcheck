"""A prior review export inside the repository is not handed to the next reviewer."""

from __future__ import annotations

import _support
from keelcheck import audit as audit_mod
from keelcheck import export

REQUIREMENTS = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]


def test_prior_export_tree_is_denied(scratch):
    _support.write(scratch / "tracked.txt", "hello\n")
    _support.write_charter(scratch, requirements=REQUIREMENTS)
    sha = _support.init_repo(scratch)
    _support.write_charter(scratch, requirements=REQUIREMENTS, ratified=sha)
    _support.commit_all(scratch, "ratified")
    first = export.build_manifest(audit_mod.run_audit(scratch, write=False))
    tree = scratch / "out" / "review-x-1" / "tree"
    tree.mkdir(parents=True)
    (tree / "tracked.txt").write_text("hello\n")
    (tree / "MECHANICAL-FINDINGS.txt").write_text("prior findings\n")
    (tree / export.MANIFEST_NAME).write_text(
        '{"keelcheck": "%s", "files": []}\n' % export.MANIFEST_KIND
    )

    manifest = export.build_manifest(audit_mod.run_audit(scratch, write=False))

    assert [f["path"] for f in manifest["files"]] == [f["path"] for f in first["files"]]
    reasons = {s["path"]: s["reason"] for s in manifest["skipped"]}
    assert reasons["out/review-x-1/tree/tracked.txt"].startswith("denied")
    assert manifest["manifest_sha256"] == first["manifest_sha256"]
