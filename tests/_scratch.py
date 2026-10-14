"""Scratch directories for the keel suite: where they live, and how a run cleans up after itself.

Same policy as rentguard's suite, for the same measured reason (see ``conftest.py``): on this host a
``tempfile`` directory is created mode 0700 and the platform sandbox, not the ACL, refuses writes
inside it, so ``mkdtemp``/``TemporaryDirectory`` fail wherever they are created. An explicit
``KEEL_SCRATCH`` wins; otherwise the platform temp dir when it is genuinely writable; otherwise a
sibling of the checkout.

Every run gets one ``run-<pid>-<random>`` directory, removed at exit, so the suite is idempotent in
one checkout.
"""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Callable, Mapping

#: tests/_scratch.py -> tests/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
SIBLING_FALLBACK = REPO_ROOT.parent / ".keel-test-tmp"
ENV_VAR = "KEEL_SCRATCH"
TEMP_SUBDIR = "keel-tests"
RUN_PREFIX = "run-"


def _platform_temp() -> Path:
    for var in ("TEMP", "TMP", "TMPDIR"):
        value = os.environ.get(var)
        if value:
            return Path(value)
    return Path(tempfile.gettempdir())


def is_writable(directory: Path) -> bool:
    """True when a file can be created, read back and removed there. A probe, not a guess."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / f".keel-write-probe-{uuid.uuid4().hex}"
        probe.write_text("ok", encoding="utf-8")
        ok = probe.read_text(encoding="utf-8") == "ok"
        probe.unlink()
        return ok
    except OSError:
        return False


def choose_root(*, env: Mapping[str, str] | None = None, temp_dir: Path | None = None,
                writable: Callable[[Path], bool] = is_writable) -> Path:
    source = os.environ if env is None else env
    override = (source.get(ENV_VAR) or "").strip()
    if override:
        return Path(override)
    platform_temp = Path(temp_dir if temp_dir is not None else _platform_temp()) / TEMP_SUBDIR
    if writable(platform_temp):
        return platform_temp
    return SIBLING_FALLBACK


class ScratchUnavailable(RuntimeError):
    """No candidate scratch directory is writable, so the suite cannot start honestly."""


_base_cache: Path | None = None
_run_dir: Path | None = None


def scratch_root() -> Path:
    global _base_cache
    if _base_cache is None:
        chosen = choose_root()
        if not is_writable(chosen):
            raise ScratchUnavailable(f"the chosen scratch root is not writable: {chosen}")
        _base_cache = chosen
    return _base_cache


def forget_choice() -> None:
    global _base_cache, _run_dir
    _base_cache = None
    _run_dir = None


def run_root() -> Path:
    global _run_dir
    if _run_dir is None:
        base = scratch_root()
        candidate = base / f"{RUN_PREFIX}{os.getpid()}-{uuid.uuid4().hex[:8]}"
        candidate.mkdir(parents=True, exist_ok=True)
        _run_dir = candidate
        atexit.register(cleanup_run)
    return _run_dir


def cleanup_run() -> None:
    if _run_dir is not None:
        shutil.rmtree(_run_dir, ignore_errors=True)


def scratch_dir(case) -> Path:
    """A fresh directory under this run's scratch root, removed when ``case`` finishes."""
    path = run_root() / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    case.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
    return path
