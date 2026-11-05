"""README's "A first run" transcript says what `keelcheck audit .` prints for a fresh, unratified charter."""

from __future__ import annotations

import re

import _support


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def test_readme_first_run_matches_the_audit_output(scratch):
    _support.write_charter(
        scratch,
        requirements=[("R1", "The example exists", "code: this example", "—", "draft")],
        gates=[],
    )
    _support.init_repo(scratch)
    proc = _support.audit(scratch)
    assert proc.returncode == 2, _support.combined(proc)

    readme = (_support.REPO / "README.md").read_text(encoding="utf-8")
    start = readme.index("$ keelcheck audit .")
    block = _collapse(readme[start:readme.index("```", start)])

    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith(("NOT AUDITABLE:", "REVIEW ("))]
    assert lines, proc.stdout
    for line in lines:
        assert _collapse(line) in block
