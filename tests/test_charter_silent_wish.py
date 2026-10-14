"""The charter parser's own answers, and the one place a requirement can still pass silently.

**Pins, not reds.** Mason landed R1 at `489f47d` with no test in front of it — `tests/` is not his
file (D3, "Pins, not reds"). These lock the parser's current answers so a later change cannot move
them silently. A pin is green on landing and says so; calling a backfilled test "red-first" would be
the laundering this project exists to catch.

The last test is a genuine red: a requirement whose only backing is a `checked-by` sentence is not a
wish, and the report never prints the `checked-by` column — so a charter can be driven to "0 wishes,
0 asserted" while the only thing between it and an irreversible act is a sentence.
"""

from __future__ import annotations

import pytest

import _support
from keel.charter import parse_file, render

ABSENT_FORMS = ["", " ", "—", "-", "--", "–", "n/a", "NONE", "none"]


# --- pins: the parser's answers as of 489f47d ---------------------------------


def test_pin_rentguard_has_exactly_the_three_wishes_the_r1_rule_finds():
    doc = parse_file(_support.RENTGUARD_CHARTER)
    assert [r.id for r in doc.wishes] == ["R2", "R4", "R8"]


def test_pin_rentguard_enforced_by_cells_that_name_no_artefact():
    """R5 is a past event ("3 rentals, $0.0264"); R9 is a condition ("only while `watch` runs").
    Neither is runnable, so neither is a mechanism."""
    doc = parse_file(_support.RENTGUARD_CHARTER)
    assert [r.id for r in doc.asserted_enforcement] == ["R5", "R9"]


def test_pin_rentguard_r9_is_declared_a_wish_but_is_not_one_by_the_rule():
    doc = parse_file(_support.RENTGUARD_CHARTER)
    assert [r.id for r in doc.declared_wish_not_wish] == ["R9"]


def test_pin_rentguard_is_still_missing_the_problems_section():
    """rentguard stays 5/6: D4 forbids editing the R7 input to fix what the tool finds."""
    doc = parse_file(_support.RENTGUARD_CHARTER)
    assert doc.missing_sections == ["problems"]


def test_pin_keel_own_charter_is_complete_and_reports_no_wishes():
    doc = parse_file(_support.KEEL_CHARTER)
    assert doc.missing_sections == []
    assert [r.id for r in doc.wishes] == []


@pytest.mark.parametrize("blank", ABSENT_FORMS)
def test_every_blank_spelling_is_a_wish(scratch, blank):
    """A cell that says "nothing" in any spelling is not a mechanism and not a check."""
    charter = _support.write_charter(
        scratch, requirements=[("R1", "the pod must stop itself", blank, blank, "draft")]
    )
    doc = parse_file(charter)
    assert doc.requirements[0].is_wish is True, f"{blank!r} was read as content"
    assert [r.id for r in doc.wishes] == ["R1"]


def test_a_named_mechanism_or_check_takes_a_requirement_out_of_the_wishes(scratch):
    charter = _support.write_charter(
        scratch,
        requirements=[
            ("R1", "the parser exists", "code: the charter parser", "—", "**met**"),
            ("R2", "the report is readable", "—", "the human reads it", "**met**"),
        ],
    )
    doc = parse_file(charter)
    assert [r.id for r in doc.wishes] == []
    assert [r.id for r in doc.asserted_enforcement] == []


@pytest.mark.skipif(not _support.RENTGUARD_CHARTER_LIVE.exists(),
                    reason="rentguard/ is not checked out beside keel/ (expected in a clone)")
def test_the_snapshot_still_matches_the_live_demonstration_input():
    """D4: rentguard/ is read-only while it is R7's input. If it ever changes, the pins above would
    silently keep measuring an old target; this fails so the snapshot is re-taken deliberately."""
    assert (_support.RENTGUARD_CHARTER_LIVE.read_bytes()
            == _support.RENTGUARD_CHARTER.read_bytes()), (
        "rentguard/CHARTER.md has moved since the snapshot; the R7 pins measure the snapshot"
    )


# --- red: the silent requirement that is not a wish ---------------------------


def test_the_report_shows_which_requirements_are_backed_only_by_a_human_check(scratch):
    """The loophole left by the R1 rule.

    Sequence: `enforced-by` is empty and `checked-by` holds a sentence. Effect: the requirement is
    not a wish (by the rule), not `asserted_enforcement` (that class only reads `enforced-by`), and
    `render()` never prints `checked-by` — so the two-minute report is silent about it.

    keel's own charter takes exactly this path: R9's *"nothing is published without the user's
    explicit word"* was moved from the wishes to `checked-by` when the user struck the wish, and the
    parser now reports **0 wishes, 0 asserted** for a project whose publication is guarded by a
    sentence. A report that cannot show that is reporting health it did not measure.
    """
    charter = _support.write_charter(
        scratch,
        requirements=[("R9", "nothing is published without the user's word", "—",
                       "the user's explicit word before any push", "checked, not enforced")],
    )
    doc = parse_file(charter)
    assert [r.id for r in doc.wishes] == [], "precondition: the sentence keeps it out of the wishes"

    report = render(doc)

    assert "the user's explicit word before any push" in report, (
        "the report hides requirements backed only by a human check; "
        f"it printed:\n{report}"
    )
