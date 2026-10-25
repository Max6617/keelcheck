"""R1's boundaries, driven from outside the package: `python -m keelcheck.charter`.

**Red against landed code, not a pin.** R1 landed before these existed; a pin records an
answer as *correct*, these record a hole. Every failure below was already in the working tree at
an earlier revision.

Three holes, all of the kind the tool exists to catch — a requirement that is not honoured, not
checked, and not reported:

1. a row that would be a wish is dropped when its id cell is empty or its id column is labelled
   something the parser does not know: exit 0, ``requirements: 0``, ``wishes: []`` — invisible;
2. a ``checked-by`` cell holding a zero-width character or ``&nbsp;`` renders as nothing but is read
   as content, so the row leaves the wishes list and the report never prints it;
3. a requirement backed only by a sentence appears in ``--json`` but not in the two-minute report a
   human reads (the same hole as `test_charter_silent_wish`'s red, asserted here on the CLI surface —
   this one is green since the author's D8 render fix, kept as the CLI-level control).

**No test here may pass because the command crashed.** A non-zero exit is only an acceptable answer
when it is a clean named refusal ("keelcheck: ..."), never a traceback: otherwise a broken parser would
turn every hole below into a pass. This is the guard `test_the_audit_command_exists_and_help_succeeds`
plays for the audit.

**Status.** All three holes were open in an earlier revision, re-measured there, and were closed in
the author's uncommitted working tree the same evening: a row with no id is now reported (id synthesised
from the line, e.g. `#20`), and `\u200b`, `\u2060`, `\ufeff`, `&nbsp;` are now wishes. The tests stay
as regressions, and the crash guard is why they did **not** go green while the parser was raising
`NameError` mid-refactor — they would have passed on the traceback's exit code otherwise.
"""

from __future__ import annotations

import json

import _support

HEADER = "| # | requirement | enforced-by | checked-by | state |"
UNKNOWN_ID_HEADER = "| Rule | requirement | enforced-by | checked-by | state |"


def _charter(rows: list[str], header: str = HEADER) -> str:
    return (
        "# Charter - probe\n\n## The frozen original\n\n> probe\n\n"
        "## What it is for\nx\n\n## What it is good at\nx\n\n"
        "## Problems the human and the agent agreed on\nx\n\n"
        "## Requirements\n\n" + header + "\n|---|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n## Permissions\nnone\n\n## Scopes\nproject\n"
    )


def _parsed(proc, label: str) -> dict:
    """The JSON document, or a failure that says why the command did not produce one."""
    out = _support.combined(proc)
    assert "Traceback" not in out, f"{label}: the parser crashed instead of reporting:\n{out}"
    assert proc.returncode == 0, (
        f"{label}: a valid charter must parse (exit {proc.returncode})\n{out}")
    return json.loads(proc.stdout)


def _write(scratch, name: str, text: str):
    return _support.write(scratch / name, text)


# --- 1. a row is never silently dropped ---------------------------------------


def test_a_requirement_row_is_never_silently_dropped(scratch):
    """A fixed-format parser may refuse a charter it cannot read; it may not read it as empty.

    ``wishes: []`` with a clean refusal is an honest "I could not read this". ``wishes: []`` with
    exit 0 on a file that contains an unenforced, unchecked requirement is the tool lying about
    itself. A crash is neither, and must not be accepted as a pass.
    """
    cases = [
        ("empty id cell", HEADER, ["|  | the pod must stop itself | \u2014 | \u2014 | draft |"]),
        ("unrecognised id header", UNKNOWN_ID_HEADER,
         ["| R1 | the pod must stop itself | \u2014 | \u2014 | draft |"]),
    ]
    for i, (label, header, rows) in enumerate(cases):
        path = _write(scratch, f"dropped-{i}.md", _charter(rows, header))
        proc = _support.charter_cli(path)
        out = _support.combined(proc)
        assert "Traceback" not in out, f"{label}: the parser crashed instead of reporting:\n{out}"
        if proc.returncode != 0:
            # a refusal is acceptable, a crash is not: it must be named, not a stack trace
            assert "keelcheck:" in out, f"{label}: refused without naming the reason:\n{out}"
            continue
        doc = json.loads(proc.stdout)
        parsed, present = len(doc["requirements"]), len(rows)
        assert parsed == present, (
            f"{label}: exit 0 with {parsed} of {present} rows parsed, so the unenforced, unchecked "
            f"requirement in the dropped row is invisible (wishes={doc['wishes']})\n{proc.stdout}"
        )


# --- 2. a cell that renders blank is not a check -------------------------------


def test_a_cell_that_renders_blank_is_not_a_check(scratch):
    """Not the empty *string* — the cell that is empty to the eye and not empty to the parser.

    The literal empty string is handled (control below). These are the spellings that survive a copy
    out of a browser, a bad editor, or an agent producing emphasis, and each turns an R1 wish into a
    silent row: not a wish, not `asserted_enforcement` (that class reads `enforced-by` only), and
    `render()` never prints `checked-by`.
    """
    for i, (label, cell) in enumerate([
        ("zero-width space", "\u200b"),
        ("word joiner", "\u2060"),
        ("BOM / ZWNBSP", "\ufeff"),
        ("&nbsp; entity", "&nbsp;"),
    ]):
        path = _write(scratch, f"blank-{i}.md",
                      _charter([f"| R1 | the pod must stop itself | \u2014 | {cell} | met |"]))
        doc = _parsed(_support.charter_cli(path), label)
        r = doc["requirements"][0]
        assert r["is_wish"], (
            f"checked-by={label} ({cell!r}) renders as nothing but was read as content: "
            f"is_wish={r['is_wish']}, wishes={doc['wishes']}, asserted={doc['asserted_enforcement']}"
        )


def test_the_literal_empty_checked_by_is_a_control(scratch):
    """A control, so the test above cannot pass by calling every `checked-by` a wish."""
    path = _write(scratch, "empty.md",
                  _charter(["| R1 | the pod must stop itself | \u2014 |  | met |"]))
    doc = _parsed(_support.charter_cli(path), "literal empty cell")
    assert doc["requirements"][0]["is_wish"] is True
    assert doc["wishes"] == ["R1"]


# --- 3. the report must not hide the sentence --------------------------------


def test_the_two_minute_report_does_not_hide_a_requirement_backed_only_by_a_sentence(scratch):
    """The machine-readable path carries the column; the report the human reads must too (D8).

    A `checked-by` sentence is valid charter content, not an error: the CLI must exit 0 *and* print
    it. keelcheck's own R9 is exactly this shape, and a report that says "0 wishes, 0 asserted" is
    reporting health it did not measure.
    """
    marker = "the user's word before any push"
    path = _write(scratch, "sentence.md",
                  _charter([f"| R9 | nothing is published | \u2014 | {marker} | checked, not enforced |"]))
    json_proc = _support.charter_cli(path)
    report = _support.charter_cli(path, json_out=False)

    assert marker in json_proc.stdout, "precondition: the JSON output carries the cell"
    out = _support.combined(report)
    assert "Traceback" not in out, f"the report crashed:\n{out}"
    assert report.returncode == 0, f"a checked-by sentence is valid content:\n{out}"
    assert marker in report.stdout, (
        "the report hides a requirement whose only backing is a human check; it printed:\n"
        f"{report.stdout}"
    )


# --- D12: the parser CLI's exit codes ----------------------------------------


def test_keel_charter_exit_codes_are_the_ones_d12_rules(scratch):
    """D12: "A file that is not a charter — or is unreadable — is exit 2 ... A charter that parses and
    has findings (a missing section, ...) is exit 1."

    Measured earlier: all three exit 0. `keelcheck charter` prints `MISSING SECTIONS:` and then does
    not act on it, so the command reads a file it cannot claim to have read as a charter.
    """
    req = [("R1", "the parser exists", "code: the charter parser", "—", "**met**")]
    _support.write(scratch / "complete.md", _support.charter_text(requirements=req))
    _support.write(scratch / "missing.md",
                   _support.charter_text(requirements=req, omit_sections=("Permissions",)))
    _support.write(scratch / "empty.md", "# just a heading\n\nsome prose\n")

    assert _support.charter_cli(scratch / "complete.md").returncode == 0, "control: a full charter is 0"
    assert _support.charter_cli(scratch / "missing.md").returncode == 1, (
        "a charter that parses with a missing required section must be exit 1 (D12)")
    assert _support.charter_cli(scratch / "empty.md").returncode == 2, (
        "a file with none of the six required sections is not a charter: exit 2 (D12)")
