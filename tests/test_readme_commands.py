"""The README's command table names every command in `keelcheck --help`."""

from __future__ import annotations

import re
from pathlib import Path

from keelcheck.cli import USAGE

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _usage_commands() -> list[str]:
    lines = USAGE.split("commands:\n", 1)[1].split("\n\n", 1)[0].splitlines()
    commands = []
    for line in lines:
        head = re.split(r"\s<|\s{2,}", line.strip(), maxsplit=1)[0]
        commands.append(" ".join(head.split()))
    return commands


def _first_cells() -> list[str]:
    return [
        line.split("|")[1].strip().strip("`")
        for line in README.splitlines()
        if line.startswith("| `keelcheck ")
    ]


def test_every_usage_command_has_a_row_in_the_readme_table():
    cells = _first_cells()
    for command in _usage_commands():
        assert any(c.startswith(f"keelcheck {command}") for c in cells), command


def test_readme_does_not_claim_there_is_no_ci():
    assert (ROOT / ".github" / "workflows" / "ci.yml").exists()
    assert "No CI is configured" not in README
