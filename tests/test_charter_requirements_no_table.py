"""A Requirements heading with no table is not a charter, whether or not another heading follows."""

from __future__ import annotations

import _support

ROW = [("R1", "x", "code: x", "—", "draft")]


def _table_block(text: str) -> str:
    lines = text.split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.startswith("| # | requirement"))
    return "\n".join(lines[start:start + 3])


def test_requirements_heading_without_table_is_not_a_charter(tmp_path):
    text = _support.charter_text(requirements=ROW)
    broken = text.replace(_table_block(text), "None yet.")
    assert broken != text
    (tmp_path / "CHARTER.md").write_text(broken, encoding="utf-8")
    result = _support.charter_cli(tmp_path / "CHARTER.md", json_out=False)
    assert result.returncode == 2
    assert "no requirements table" in result.stderr


def test_control_unmodified_charter_exits_zero(tmp_path):
    (tmp_path / "CHARTER.md").write_text(_support.charter_text(requirements=ROW), encoding="utf-8")
    assert _support.charter_cli(tmp_path / "CHARTER.md", json_out=False).returncode == 0
