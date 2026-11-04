"""`keelcheck --help` lists every command, including `version`."""

from __future__ import annotations

import re

from keelcheck import cli
from keelcheck.cli import USAGE, main


def test_help_names_the_version_command(capsys):
    assert main(["--help"]) == 0
    assert "version" in capsys.readouterr().out


def test_unknown_command_exits_2_and_prints_usage(capsys):
    assert main(["no-such-command"]) == 2
    err = capsys.readouterr().err
    assert "unknown command: no-such-command" in err
    assert "version" in err


def _usage_commands() -> list[str]:
    lines = USAGE.split("commands:\n", 1)[1].split("\n\n", 1)[0].splitlines()
    commands = []
    for line in lines:
        head = re.split(r"\s<|\s{2,}", line.strip(), maxsplit=1)[0]
        commands.append(" ".join(head.split()))
    return commands


def test_every_usage_command_is_in_the_module_docstring():
    doc = " ".join((cli.__doc__ or "").split())
    for command in _usage_commands():
        assert f"keelcheck {command}" in doc, command
