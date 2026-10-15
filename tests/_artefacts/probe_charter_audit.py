"""Oracle probe: apply the literal charter rules to a real charter by hand.

This is NOT the keelcheck package. It is a throwaway measurement used to state, with
numbers, what a mechanical audit of a charter can and cannot see. It exists so
the R7 demonstration can be reported before the parser exists.

Rules applied, verbatim from keel/CHARTER.md and rentguard/CHARTER.md:
  * `enforced-by:` = a mechanism; `checked-by:` = a human check.
  * Neither cell filled -> the requirement is a WISH.
  * A gate is "a script recorded in the charter with a content hash".
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ABSENT = {"", "-", "--", "\u2014", "\u2013", "n/a", "none"}


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def absent(value: str) -> bool:
    return value.strip().lower() in ABSENT


def parse_requirements(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        if re.match(r"^\|\s*R\d+\s*\|", line):
            c = cells(line)
            if len(c) < 5:
                continue
            rows.append(
                {
                    "id": c[0],
                    "req": c[1],
                    "enforced_by": c[2],
                    "checked_by": c[3],
                    "state": c[4],
                }
            )
    return rows


def audit(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    rows = parse_requirements(text)
    wishes, met_unbacked, conditional, hashes = [], [], [], []
    for r in rows:
        no_mech = absent(r["enforced_by"])
        no_check = absent(r["checked_by"])
        if no_mech and no_check:
            wishes.append(r["id"])
        if r["state"].strip().lower().startswith("**met**") and no_mech and no_check:
            # claimed met, but neither a mechanism nor a check backs it
            met_unbacked.append(r["id"])
        if not no_mech:
            mech = r["enforced_by"].lower()
            for token in ("only while", "only if", "only when", "as long as"):
                if token in mech:
                    conditional.append((r["id"], r["enforced_by"]))
        if re.search(r"\bhash\b", r["enforced_by"], re.I) or re.search(
            r"\bhash\b", r["checked_by"], re.I
        ):
            hashes.append(r["id"])
    gate_hashes = len(re.findall(r"(?im)^\s*(?:gate|hash)\s*[:=]", text))
    return {
        "path": str(path),
        "requirements": len(rows),
        "wish_ids": wishes,
        "met_without_mechanism": met_unbacked,
        "conditional_mechanisms": conditional,
        "gate_hashes_in_charter": gate_hashes,
        "state_says_wish": [r["id"] for r in rows if "wish" in r["state"].lower()],
        "empty_enforced_by": [r["id"] for r in rows if absent(r["enforced_by"])],
        "empty_checked_by": [r["id"] for r in rows if absent(r["checked_by"])],
    }


def main() -> int:
    for arg in sys.argv[1:]:
        a = audit(Path(arg))
        print(f"== {a['path']}")
        print(f"   requirements: {a['requirements']}")
        print(f"   wishes by the rule (no mechanism, no check): {a['wish_ids']}")
        print(f"   state column itself says 'wish': {a['state_says_wish']}")
        print(f"   claimed met with neither mechanism nor check: {a['met_without_mechanism']}")
        print(f"   enforced-by that is conditional prose: {a['conditional_mechanisms']}")
        print(f"   empty enforced-by: {a['empty_enforced_by']}")
        print(f"   empty checked-by: {a['empty_checked_by']}")
        print(f"   gate content hashes in the charter: {a['gate_hashes_in_charter']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
