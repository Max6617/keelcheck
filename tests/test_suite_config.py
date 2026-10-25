"""Configuration the suite depends on, pinned where the configuration file can carry it.

a documentation reviewer measured it earlier: two `pytest-cache-files-*` directories left in keelcheck's root made
`pytest -q` exit 2 with two collection errors in the worktree, while the same revision from
`git archive` was **93 passed, 6 skipped**. The coverage gate's whole job is to run this suite, so a
stray directory that breaks collection breaks the gate.

The symptom itself needs the sandbox's unreadable ACLs — a directory a test creates here is readable,
so a behavioural reproduction would pass either way and would be a test that lies. What is pinned is
the configuration that makes such a directory harmless: it is never collected.
"""

from __future__ import annotations

from fnmatch import fnmatch

import pytest

import _support

try:  # 3.11+. The package itself declares 3.10, so this test says so instead of failing collection.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - measured on 3.10 in CI
    tomllib = None


def _pytest_options() -> dict:
    """The pytest options as configured in `pyproject.toml`, which is where this project keeps them."""
    data = tomllib.loads((_support.REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return data.get("tool", {}).get("pytest", {}).get("ini_options", {})


@pytest.mark.skipif(
    tomllib is None,
    reason="tomllib is 3.11+; the pyproject configuration cannot be read on this interpreter",
)
def test_a_stray_pytest_cache_directory_cannot_break_collection():
    options = _pytest_options()
    norecurse = options.get("norecursedirs", [])
    if isinstance(norecurse, str):
        norecurse = norecurse.split()
    testpaths = options.get("testpaths", [])
    if isinstance(testpaths, str):
        testpaths = testpaths.split()

    excluded = any(
        fnmatch("pytest-cache-files-abc123", pattern) or fnmatch("pytest-cache-files-abc123/", pattern)
        for pattern in norecurse
    )
    restricted = list(testpaths) == ["tests"]

    assert excluded or restricted, (
        "nothing in the pytest configuration keeps a stray `pytest-cache-files-*` directory in the "
        f"repository root out of collection: norecursedirs={norecurse!r}, testpaths={testpaths!r}. "
        "a documentation reviewer measured two such directories turning `pytest -q` into exit 2 with collection errors "
        "while the same revision from `git archive` was clean.")
