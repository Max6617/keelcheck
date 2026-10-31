"""`keelcheck --help` lists every command, including `version`."""

from __future__ import annotations

from keelcheck.cli import main


def test_help_names_the_version_command(capsys):
    assert main(["--help"]) == 0
    assert "version" in capsys.readouterr().out
