"""Parse a project charter (R1).

A charter is one file per project. The format is fixed: purpose, strengths, agreed
problems, requirements, permissions, scopes. A requirement lives in the requirements
table and carries how it is honoured:

    enforced-by:  a mechanism makes the violation impossible, fatal or recoverable
    checked-by:   a human judges it, or a demo makes the state visible
    neither   ->  a wish, and the parser says so.

A wish is not a parse error. It is the audit's most valuable output: the things the
human cared about that nothing enforces and nobody checks. The parser therefore parses
a wish successfully and reports it.

Two report classes come out of a parse:

``wishes``               requirements with neither field filled in -- the R1 rule, exactly.
``asserted_enforcement`` requirements whose ``enforced-by`` cell is prose that names no
                         artefact: no ``code:`` marker, no path, no commit. Nothing can be
                         run against such a cell, so it is a wish wearing a mechanism's
                         clothes. Classified from the text alone; it is a reading of the
                         cell, not a judgement about the project.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .output import emit, emit_err

__all__ = [
    "Charter",
    "CharterFormatError",
    "Gate",
    "Requirement",
    "REQUIRED_SECTIONS",
    "named_repo_paths",
    "parse_charter",
    "parse_file",
    "render",
]

#: The recorded form of a gate content hash (D8 A1). Anything else -- a bare digest, a
#: prefix in another algorithm -- is a malformed hash, and a malformed hash is divergence,
#: never a skip.
HASH_FORMAT = re.compile(r"^sha256:[0-9a-f]{64}$")

#: ``Ratified at: `<sha>``` in the charter's living state. The label may itself be inside
#: backticks, as it is in this project's own charter.
RATIFIED_LINE = re.compile(
    r"ratified\s+at\s*:?\s*`?\s*`?(?=[0-9a-f]*\d)([0-9a-f]{7,40})", re.IGNORECASE
)

#: The canonical spelling (D12): a plain line, ``Ratified at: <sha>``, trailing prose allowed.
#: Other spellings are still parsed so a miss is never silent, and reported as ``[format]``.
CANONICAL_RATIFIED = re.compile(
    r"^\s*Ratified at:\s*`?(?=[0-9a-f]*\d)([0-9a-f]{7,40})", re.IGNORECASE
)

#: Extensions that make a bare token a repo path in an ``enforced-by`` cell (D13). Deliberately
#: an allow-list and not "anything with a dot": rentguard's R5 cell holds ``$0.0264``, and a
#: currency amount is not a path.
PATH_EXTENSIONS = (
    ".py", ".md", ".json", ".jsonl", ".sh", ".toml", ".txt", ".yml", ".yaml", ".cfg", ".ini",
    ".ps1", ".bat", ".js", ".ts", ".rs", ".go",
)


class CharterFormatError(ValueError):
    """The file is not a charter: a required section or column is missing.

    Distinct from a wish. A wish is valid charter content; a missing requirements
    table is not a charter at all.
    """


# --- the fixed format -------------------------------------------------------

# Section name -> the heading texts that satisfy it. Matching is on the normalized
# heading (lowercased, punctuation stripped) and is a substring test, so
# "## What it is good at -- and what it is not for" satisfies "strengths".
REQUIRED_SECTIONS: dict[str, tuple[str, ...]] = {
    "purpose": ("what it is for", "purpose"),
    "strengths": ("what it is good at", "strengths"),
    "problems": ("problems", "the problem", "agreed problems"),
    "requirements": ("requirements",),
    "permissions": ("permissions",),
    "scopes": ("scopes",),
}

# Cells that carry no content. The em dash is how the drafted charters write "nothing",
# which is why it cannot be treated as a mechanism.
EMPTY_CELLS = frozenset({"", "-", "--", "---", "\u2013", "\u2014", "n/a", "na", "none", "?", "tbd"})

# A cell can be empty to the eye and not empty to the parser. These survive a copy out of a
# browser, a bad editor, or an agent producing emphasis, and each one turns an R1 wish into
# a row that is not a wish, is not `asserted_enforcement` and is never printed (D8).
INVISIBLE = str.maketrans("", "", "\u200b\u200c\u200d\u2060\ufeff")
BLANK_ENTITIES = ("&nbsp;", "&#160;", "&#xa0;", "&ensp;", "&emsp;", "&thinsp;")
BLANK_CHARS = "\u00a0"

# A gate/mechanism reference the parser will accept as naming something runnable.
_CODE_MARKER = re.compile(r"\bcode\b\s*[:\-\u2013\u2014+]", re.IGNORECASE)
_BACKTICKED = re.compile(r"`([^`]*)`")
_SHA = re.compile(r"^(?=[0-9a-f]*\d)[0-9a-f]{7,40}$", re.IGNORECASE)
_PATHISH = re.compile(r"[./\\]\w")
_FILELIKE = re.compile(r"\w+\.\w{1,8}$")
_SEPARATOR_ROW = re.compile(r"^:?-{2,}:?$")


def _normalize(text: str) -> str:
    """Lowercase and reduce punctuation to single spaces, for heading matching."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _cell_key(text: str) -> str:
    """The content of a table cell with markdown emphasis and invisible filler removed.

    ``**met**`` -> ``met``, and ``\\u200b``, ``&nbsp;`` or a stray BOM -> nothing: a cell
    that renders blank is not a mechanism and not a check (see ``EMPTY_CELLS``).
    """
    cleaned = text.replace("*", "").replace("`", "")
    for entity in BLANK_ENTITIES:
        cleaned = cleaned.replace(entity, " ")
    cleaned = cleaned.translate(INVISIBLE).replace(BLANK_CHARS, " ")
    return cleaned.strip()


def _is_empty_cell(text: str) -> bool:
    return _cell_key(text).lower() in EMPTY_CELLS


def named_repo_paths(cell: str) -> list[str]:
    """The repo paths an ``enforced-by`` cell names, by the same text heuristics as above.

    D13 needs this list so the audit can check that a named mechanism actually resolves in
    the audited repository: an ``enforced-by`` naming ``tools/coverage.py`` passes any text
    heuristic and enforces nothing when that path belongs to another repository.
    """
    found: list[str] = []
    candidates = [*_BACKTICKED.findall(cell), *re.findall(r"\S+", cell)]
    for token in candidates:
        candidate = token.strip().strip(",;:()[]`*\"'")
        if not candidate or _SHA.match(candidate):
            continue
        if candidate.lower().startswith(("http://", "https://", "www.")):
            continue
        looks_like_path = "/" in candidate or candidate.lower().endswith(PATH_EXTENSIONS)
        if looks_like_path and candidate not in found:
            found.append(candidate)
    return found


def _names_an_artefact(cell: str) -> bool:
    """True when an ``enforced-by`` cell names something that can be run or checked.

    Accepted: a ``code:`` marker, a backticked path/filename, a commit sha (backticked
    or bare), a path-like token with an extension. Everything else -- "only while
    ``watch`` runs", "3 rentals, $0.0264" -- is prose. See the module docstring for why
    prose in this cell is reported rather than rejected.
    """
    if _CODE_MARKER.search(cell):
        return True
    for span in _BACKTICKED.findall(cell):
        token = span.strip()
        if _SHA.match(token) or _PATHISH.search(token):
            return True
    for token in re.findall(r"\S+", cell):
        bare = token.strip(",;:()[]`")
        if _SHA.match(bare):
            return True
        if "/" in bare or "\\" in bare:
            if _FILELIKE.search(bare):
                return True
    return False


# --- the model --------------------------------------------------------------


@dataclass(frozen=True)
class Gate:
    """One row of the gates table: a script, and the content hash that locks it (R2)."""

    name: str
    path: str
    hash: str
    line: int

    @property
    def malformed_hash(self) -> bool:
        """A1: the recorded hash is ``sha256:<64 hex>`` or it is a divergence."""
        return not HASH_FORMAT.match(self.hash.strip())

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "hash": self.hash,
            "line": self.line,
            "malformed_hash": self.malformed_hash,
        }


@dataclass(frozen=True)
class Requirement:
    """One row of the requirements table, kept with the line it came from."""

    id: str
    text: str
    enforced_by: str
    checked_by: str
    state: str
    line: int

    @property
    def is_wish(self) -> bool:
        """R1: neither ``enforced-by`` nor ``checked-by`` -> a wish."""
        return _is_empty_cell(self.enforced_by) and _is_empty_cell(self.checked_by)

    @property
    def enforcement(self) -> str:
        """"none" (no enforced-by), "asserted" (prose), or "mechanical" (names an artefact)."""
        if _is_empty_cell(self.enforced_by):
            return "none"
        return "mechanical" if _names_an_artefact(self.enforced_by) else "asserted"

    @property
    def declared_wish(self) -> bool:
        """True when the state column itself says "wish"."""
        return "wish" in _cell_key(self.state).lower()

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "enforced_by": self.enforced_by,
            "checked_by": self.checked_by,
            "state": self.state,
            "line": self.line,
            "is_wish": self.is_wish,
            "enforcement": self.enforcement,
            "declared_wish": self.declared_wish,
        }


@dataclass
class Charter:
    """A parsed charter: what was found, and what the fixed format required."""

    path: Path | None
    title: str
    frozen_original: str
    sections: dict[str, int] = field(default_factory=dict)  # section -> heading line
    requirements: list[Requirement] = field(default_factory=list)
    gates: list[Gate] = field(default_factory=list)
    ratified_at: str | None = None
    ratified_line: str | None = None
    ratified_canonical: bool = False
    unknown_sections: list[str] = field(default_factory=list)

    @property
    def missing_sections(self) -> list[str]:
        return [name for name in REQUIRED_SECTIONS if name not in self.sections]

    @property
    def frozen_original_bytes(self) -> int:
        """The block's byte length, recorded beside its hash (D11 F9).

        A redefinition of what the anchor covers is then visible as a length change, rather
        than as two hashes that are each defensible under a different definition.
        """
        return len(self.frozen_original.encode("utf-8"))

    @property
    def frozen_original_sha256(self) -> str:
        return "sha256:" + hashlib.sha256(self.frozen_original.encode("utf-8")).hexdigest()

    @property
    def wishes(self) -> list[Requirement]:
        """R1's output: requirements with neither mechanism nor check."""
        return [r for r in self.requirements if r.is_wish]

    @property
    def human_checks(self) -> list[Requirement]:
        """Requirements backed only by a ``checked-by`` sentence.

        Not wishes by the R1 rule, and not mechanical either: a human judged it. They must
        be printed (D8), because a report that reads "0 wishes, 0 asserted" while a
        sentence is the only thing between the project and an irreversible act is the
        render lying about the charter.
        """
        return [
            r
            for r in self.requirements
            if _is_empty_cell(r.enforced_by) and not _is_empty_cell(r.checked_by)
        ]

    @property
    def asserted_enforcement(self) -> list[Requirement]:
        """Requirements whose ``enforced-by`` is prose that names no artefact."""
        return [r for r in self.requirements if r.enforcement == "asserted"]

    @property
    def declared_wish_not_wish(self) -> list[Requirement]:
        """The state column says wish, the R1 rule does not. One of the two is wrong."""
        return [r for r in self.requirements if r.declared_wish and not r.is_wish]

    @property
    def wish_not_declared(self) -> list[Requirement]:
        """The R1 rule says wish, the state column does not."""
        return [r for r in self.requirements if r.is_wish and not r.declared_wish]

    def as_dict(self) -> dict:
        return {
            "path": str(self.path) if self.path else None,
            "title": self.title,
            "frozen_original": self.frozen_original,
            "frozen_original_bytes": self.frozen_original_bytes,
            "frozen_original_sha256": self.frozen_original_sha256,
            "sections": self.sections,
            "missing_sections": self.missing_sections,
            "requirements": [r.as_dict() for r in self.requirements],
            "gates": [g.as_dict() for g in self.gates],
            "ratified_at": self.ratified_at,
            "ratified_canonical": self.ratified_canonical,
            "ratified_line": self.ratified_line,
            "wishes": [r.id for r in self.wishes],
            "human_checks": [r.id for r in self.human_checks],
            "asserted_enforcement": [r.id for r in self.asserted_enforcement],
            "declared_wish_not_wish": [r.id for r in self.declared_wish_not_wish],
            "wish_not_declared": [r.id for r in self.wish_not_declared],
        }


# --- the parser -------------------------------------------------------------


def _split_row(line: str) -> list[str]:
    """Split a markdown table row on unescaped pipes, dropping the outer edges."""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells = re.split(r"(?<!\\)\|", body)
    return [c.replace("\\|", "|").strip() for c in cells]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(_SEPARATOR_ROW.match(c.strip()) for c in cells if c.strip() != "")


def _section_of(line: str) -> tuple[int, str] | None:
    m = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
    if not m:
        return None
    return len(m.group(1)), m.group(2)


def _match_section(heading: str) -> str | None:
    norm = _normalize(heading)
    for name, aliases in REQUIRED_SECTIONS.items():
        for alias in aliases:
            if _normalize(alias) in norm:
                return name
    return None


def _parse_requirements_table(lines: list[str], start: int, path: Path | None) -> tuple[list[Requirement], int]:
    """Parse the table beginning at ``lines[start]``. Returns (requirements, next index).

    The header row fixes the column order, so a charter may reorder columns. ``#``,
    ``enforced-by`` and ``checked-by`` must all be present -- without them a requirement
    cannot be tested for wishhood, and the file is not a charter.
    """
    header = [c.lower() for c in _split_row(lines[start])]
    index: dict[str, int] = {}
    for i, name in enumerate(header):
        key = _normalize(name)
        if key in ("", "#", "id", "no", "num"):
            index["id"] = i
        elif key in ("requirement", "requirements", "text", "what"):
            index["text"] = i
        elif key.replace(" ", "") in ("enforcedby", "enforced", "enforcement"):
            index["enforced_by"] = i
        elif key.replace(" ", "") in ("checkedby", "checked", "check"):
            index["checked_by"] = i
        elif key in ("state", "status"):
            index["state"] = i

    if "id" not in index:
        # An unfamiliar label in the first column ("Rule", "") is still the id column. A row
        # must never vanish because the parser did not recognise a heading: the requirement
        # in it may be exactly the wish this tool exists to surface.
        for i in range(len(header)):
            if i not in index.values():
                index["id"] = i
                break

    missing = [k for k in ("enforced_by", "checked_by") if k not in index]
    if missing:
        where = f"{path} (line {start + 1})" if path else f"line {start + 1}"
        raise CharterFormatError(
            f"requirements table at {where} has no {'/'.join(missing)} column; "
            "the format is fixed and a requirement without those columns cannot be tested for wishhood"
        )

    def cell(cells: list[str], key: str) -> str:
        i = index.get(key)
        if i is None or i >= len(cells):
            return ""
        return cells[i]

    requirements: list[Requirement] = []
    i = start + 1
    if i < len(lines) and lines[i].strip().startswith("|") and _is_separator(_split_row(lines[i])):
        i += 1
    while i < len(lines):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        cells = _split_row(line)
        if _is_separator(cells):
            i += 1
            continue
        rid = _cell_key(cell(cells, "id")) or f"#{i + 1}"
        requirements.append(
            Requirement(
                id=rid,
                text=cell(cells, "text"),
                enforced_by=cell(cells, "enforced_by").strip(),
                checked_by=cell(cells, "checked_by").strip(),
                state=cell(cells, "state").strip(),
                line=i + 1,
            )
        )
        i += 1
    return requirements, i


def _parse_gates_table(lines: list[str], start: int) -> list[Gate]:
    """Parse the table at ``lines[start]`` as ``| gate | path | hash |``.

    Deliberately lenient where the requirements table is strict: a gates table with no
    ``hash`` column, or a row with an empty hash, produces gates whose hash is malformed,
    and the audit reports that as divergence (A1) instead of refusing to read the charter.
    A malformed hash must be visible, not a skip and not a parse error.
    """
    header = [c.lower() for c in _split_row(lines[start])]
    index: dict[str, int] = {}
    for i, name in enumerate(header):
        key = _normalize(name)
        if key in ("gate", "name", "id", "#"):
            index["name"] = i
        elif key in ("path", "script", "file", "gate file"):
            index["path"] = i
        elif key in ("hash", "sha256", "content hash", "contenthash", "digest"):
            index["hash"] = i

    def cell(cells: list[str], key: str) -> str:
        i = index.get(key)
        if i is None or i >= len(cells):
            return ""
        return cells[i]

    gates: list[Gate] = []
    i = start + 1
    if i < len(lines) and lines[i].strip().startswith("|") and _is_separator(_split_row(lines[i])):
        i += 1
    while i < len(lines):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        cells = _split_row(line)
        if _is_separator(cells):
            i += 1
            continue
        name = _cell_key(cell(cells, "name"))
        path = _cell_key(cell(cells, "path"))
        if name or path:
            gates.append(
                Gate(
                    name=name,
                    path=path,
                    hash=_cell_key(cell(cells, "hash")),
                    line=i + 1,
                )
            )
        i += 1
    return gates


def _frozen_block(lines: list[str], start: int, level: int) -> str:
    """The frozen-original **section**: its heading line to the next heading of the same or a
    higher level, heading included, joined with LF.

    D11 (F9): the block is the section, not the first blockquote in it. The section carries
    the accepted recommendation, and the recommendation is where the scope lives -- so
    anchoring only the first quote anchors *less* than the record says the anchor covers,
    which is the vacuity class on the tool's own anchor. The block's byte length is recorded
    beside its hash so that a redefinition shows up as a length change rather than as a
    second defensible hash.
    """
    end = len(lines)
    for n in range(start + 1, len(lines)):
        found = _section_of(lines[n])
        if found and found[0] <= level:
            end = n
            break
    return "\n".join(lines[start:end])


def parse_charter(text: str, path: Path | None = None) -> Charter:
    """Parse charter ``text``. Raises :class:`CharterFormatError` when it is not one."""
    lines = text.splitlines()

    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    charter = Charter(path=path, title=title, frozen_original="")
    frozen_seen = False

    section_for_line: dict[int, str | None] = {}
    for n, line in enumerate(lines):
        found = _section_of(line)
        if found:
            section_for_line[n] = _match_section(found[1])

    for n, line in enumerate(lines):
        found = _section_of(line)
        if not found:
            continue
        level, heading = found
        name = section_for_line[n]
        if level >= 2 and name:
            charter.sections.setdefault(name, n + 1)
        elif level >= 2 and _normalize(heading) not in (
            "the wishes",
            "wishes",
            "the frozen original",
            "frozen original",
            "gates",
            "ratification",
        ):
            charter.unknown_sections.append(heading)

    # Requirements table: the first table after the requirements heading.
    if "requirements" in charter.sections:
        start = charter.sections["requirements"]
        for n in range(start, len(lines)):
            if _section_of(lines[n]) and n > start:
                break
            if lines[n].strip().startswith("|"):
                charter.requirements, _ = _parse_requirements_table(lines, n, path)
                break
        else:
            where = f"{path}" if path else "input"
            raise CharterFormatError(f"no requirements table found after the requirements heading in {where}")

    # Frozen original: the whole section under its heading, heading included (D11 F9).
    for n, line in enumerate(lines):
        found = _section_of(line)
        if found and _normalize(found[1]) in ("the frozen original", "frozen original"):
            charter.frozen_original = _frozen_block(lines, n, found[0])
            frozen_seen = True
            break
    if not frozen_seen:
        for n, line in enumerate(lines):
            found = _section_of(line)
            if found and "original" in _normalize(found[1]):
                charter.frozen_original = _frozen_block(lines, n, found[0])
                break

    # The ratification commit: named in the living state, never in the frozen original (A2).
    # Any spelling is parsed, so a miss is never silent; only the canonical plain line is
    # silent (D12), and the audit reports the others as `[format]`.
    for line in lines:
        found = RATIFIED_LINE.search(line)
        if found:
            charter.ratified_at = found.group(1).lower()
            charter.ratified_line = line.strip()
            charter.ratified_canonical = bool(CANONICAL_RATIFIED.match(line))
            break

    # Gates table: the first table under a "Gates" heading, if there is one.
    for n, line in enumerate(lines):
        found = _section_of(line)
        if not found or _normalize(found[1]) not in ("gates", "the gates"):
            continue
        for m in range(n + 1, len(lines)):
            if _section_of(lines[m]):
                break
            if lines[m].strip().startswith("|"):
                charter.gates = _parse_gates_table(lines, m)
                break
        break

    return charter


def parse_file(path: str | Path) -> Charter:
    """Read and parse a charter file."""
    p = Path(path)
    return parse_charter(p.read_text(encoding="utf-8"), path=p)


def render(charter: Charter) -> str:
    """The two-minute report: every column, findings first.

    D8: the report prints all four columns of the requirements table. A row whose only
    mechanism is ``checked-by`` is a **human check**, never silence -- the silent row is the
    loophole the R1 rule leaves, and hiding it is how a report reads "0 wishes" while a
    sentence is the only guard on an irreversible act.
    """
    out: list[str] = []
    where = str(charter.path) if charter.path else "<input>"
    out.append(f"charter: {where}")
    out.append(f"title:   {charter.title or '(untitled)'}")
    out.append(f"sections: {len(charter.sections)}/{len(REQUIRED_SECTIONS)} required")
    if charter.missing_sections:
        out.append(f"  MISSING SECTIONS: {', '.join(charter.missing_sections)}")
    out.append(f"requirements: {len(charter.requirements)}")
    out.append(f"gates: {len(charter.gates)} declared")
    out.append(f"ratified at: {charter.ratified_at or '(not named)'}")
    out.append(
        f"frozen original: {charter.frozen_original_bytes} bytes, {charter.frozen_original_sha256}"
    )
    out.append("")

    out.append(f"REQUIREMENTS ({len(charter.requirements)}) -- all four columns")
    if not charter.requirements:
        out.append("  (none)")
    for r in charter.requirements:
        out.append(f"  {r.id}  state: {_cell_key(r.state) or '-'}")
        out.append(f"      requirement:  {r.text}")
        out.append(f"      enforced-by:  {r.enforced_by or '-'}")
        out.append(f"      checked-by:   {r.checked_by or '-'}")
    out.append("")

    out.append(f"WISHES (neither enforced-by nor checked-by): {len(charter.wishes)}")
    for r in charter.wishes:
        out.append(f"  {r.id} (line {r.line}) state={_cell_key(r.state) or '-'}")
        out.append(f"      {r.text}")
    out.append("")

    out.append(f"HUMAN CHECKS (checked-by only, no mechanism): {len(charter.human_checks)}")
    for r in charter.human_checks:
        out.append(f"  {r.id} (line {r.line}) checked-by: {r.checked_by}")
        out.append(f"      {r.text}")
    out.append("")

    out.append(f"ASSERTED ENFORCEMENT (enforced-by names no artefact): {len(charter.asserted_enforcement)}")
    for r in charter.asserted_enforcement:
        out.append(f"  {r.id} (line {r.line}) enforced-by: {r.enforced_by}")
    out.append(
        "  heuristic: 'names an artefact' means a `code:` marker, a backticked path or filename, "
        "a commit sha, or a path-like token with an extension, read from the enforced-by cell "
        "only. 0 here means no cell matched that reading, not that every mechanism exists (D13)."
    )
    out.append("")

    if charter.gates:
        out.append(f"GATES ({len(charter.gates)})")
        for g in charter.gates:
            mark = "  MALFORMED HASH" if g.malformed_hash else ""
            out.append(f"  {g.name or '(unnamed)'} -> {g.path or '(no path)'}  {g.hash or '(no hash)'}{mark}")
        out.append("")

    if charter.declared_wish_not_wish:
        out.append("DECLARED WISH, NOT A WISH BY THE R1 RULE:")
        for r in charter.declared_wish_not_wish:
            out.append(f"  {r.id} (line {r.line}) enforced-by: {r.enforced_by}")
        out.append("")
    if charter.wish_not_declared:
        out.append("WISH BY THE R1 RULE, NOT DECLARED AS ONE:")
        for r in charter.wish_not_declared:
            out.append(f"  {r.id} (line {r.line}) state={_cell_key(r.state) or '-'}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    """``python -m keel.charter <path> [--json]``.

    Exit 0 whether or not wishes were found: a wish is the output, not an error.
    Exit 2 when the file is not a charter at all -- unreadable or unparseable, the one meaning
    exit 2 carries across every command (D12). Exit 1 is for a charter that parses and has
    findings.
    """
    import argparse

    parser = argparse.ArgumentParser(prog="keel charter", description="parse a charter (R1)")
    parser.add_argument("path", help="path to CHARTER.md")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--fail-on-wish",
        action="store_true",
        help="exit 2 when a wish or an asserted mechanism is found (opt-in; not the default)",
    )
    args = parser.parse_args(argv)

    try:
        charter = parse_file(args.path)
    except FileNotFoundError:
        emit_err(f"keel: no such file: {args.path}")
        return 2
    except CharterFormatError as exc:
        emit_err(f"keel: not a charter: {exc}")
        return 2

    if args.json:
        emit(json.dumps(charter.as_dict(), indent=2, ensure_ascii=False))
    else:
        emit(render(charter))

    if args.fail_on_wish and (charter.wishes or charter.asserted_enforcement):
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
