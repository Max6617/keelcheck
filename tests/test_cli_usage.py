"""`keelcheck --help` lists every command, including `version`."""

from __future__ import annotations

from keelcheck.cli import main


def test_help_names_the_version_command(capsys):
    assert main(["--help"]) == 0
    assert "version" in capsys.readouterr().out


def test_unknown_command_exits_2_and_prints_usage(capsys):
    assert main(["no-such-command"]) == 2
    err = capsys.readouterr().err
    assert "unknown command: no-such-command" in err
    assert "version" in err
