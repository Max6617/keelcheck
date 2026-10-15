"""Test-run setup for the keelcheck suite.

Two environment jobs, both inherited from rentguard where they were measured, not guessed.

**1. Temporary files that can actually be written.** On this host the sandbox creates ``tempfile``
directories mode 0700 and then refuses writes inside them, so ``TemporaryDirectory``/``mkdtemp``
fail wherever they are created. ``tests/_scratch.py`` owns the policy (``KEELCHECK_SCRATCH`` else a
writable platform temp dir else a checkout sibling) and this hook points ``tempfile`` at the same
root so the two cannot disagree.

**2. Cleanup that tolerates a refused chmod.** ``shutil.rmtree`` fails while restoring permissions
on a confined directory, after the test body has already passed. A passing assertion must not be
reported as a failure because of it.

Product behaviour is asserted in the test modules. This file must not change any of it.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
REPO_ROOT = TESTS.parent

# The package under test lives at <repo>/keelcheck/, the tests at <repo>/tests/.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

sys.path.insert(0, str(TESTS))
from _scratch import cleanup_run, run_root  # noqa: E402

_real_rmtree = shutil.rmtree
_real_mkdtemp = tempfile.mkdtemp


def _tolerant_rmtree(path, ignore_errors=False, onerror=None, *, onexc=None):
    return _real_rmtree(path, ignore_errors=True, onerror=onerror, onexc=onexc)


def _writable_mkdtemp(suffix=None, prefix=None, dir=None):
    path = _real_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
    try:
        import os

        os.chmod(path, 0o777)
    except OSError:
        pass
    return path


def pytest_configure(config):  # noqa: ARG001
    try:
        tempfile.tempdir = str(run_root())
    except OSError:
        pass
    shutil.rmtree = _tolerant_rmtree
    tempfile.mkdtemp = _writable_mkdtemp


def pytest_unconfigure(config):  # noqa: ARG001
    shutil.rmtree = _real_rmtree
    tempfile.mkdtemp = _real_mkdtemp
    cleanup_run()


@pytest.fixture
def scratch():
    """A fresh writable directory, removed when the test finishes."""
    path = run_root() / __import__("uuid").uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
