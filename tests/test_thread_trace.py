"""`sys.settrace` reaches only the calling thread, so the tracer needs `threading.settrace` too.

The property, stated as a line rather than as a mechanism: **a package line executed on a worker thread
is recorded**. Before this test's fix, `tools/coverage.py` and `tools/_child_trace.py` called
`sys.settrace` and nothing else, so every line that only ever runs on a thread was in the denominator and
could never be hit -- wrong in the direction nobody checks. Keel runs package code on threads:
`review.py` starts two daemon threads around `_drain`.

The driver is a real child process, because that is where the child tracer lives and because the hit file
is written at exit. Nothing here is a mock: `_child_trace.activate()` is the gate's own bootstrap, and
the thread target is a real package function that this child does not call anywhere else.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import _support

REPO = _support.REPO

#: The package function the thread runs, and a line inside its body. Chosen because a bare child never
#: calls it outside the thread, so the only way its line can be recorded is through the thread tracer.
TARGET_MODULE = "keelcheck/review.py"
TARGET_FUNCTION = "split_command"

DRIVER = """
import sys, threading
sys.path.insert(0, r"{repo}")
sys.path.insert(0, r"{tools}")
import _child_trace
_child_trace.activate()
import keelcheck.review as review


def work():
    review.split_command("python -m keelcheck audit .")


thread = threading.Thread(target=work, name="keelcheck-test-worker")
thread.start()
thread.join()
"""


def _target_line() -> int:
    """The first executable line inside `split_command`'s body, from the source itself."""
    from trace import _find_executable_linenos

    path = REPO / TARGET_MODULE
    text = path.read_text(encoding="utf-8").splitlines()
    start = next(n for n, line in enumerate(text, 1) if line.startswith(f"def {TARGET_FUNCTION}("))
    executable = sorted(n for n in _find_executable_linenos(str(path)) if isinstance(n, int))
    return next(n for n in executable if n > start)


def test_a_line_executed_on_a_worker_thread_is_recorded(scratch):
    hits = scratch / "hits"
    hits.mkdir()
    driver = _support.write(scratch / "driver.py", DRIVER.format(
        repo=str(REPO), tools=str(REPO / "tools")))
    env = {
        **os.environ,
        "KEELCHECK_COVERAGE_CHILD": "1",
        "KEELCHECK_COVERAGE_DIR": str(hits),
        "KEELCHECK_COVERAGE_PACKAGE": str(REPO / "keelcheck"),
        "PYTHONIOENCODING": "utf-8",
    }
    done = subprocess.run([sys.executable, str(driver)], capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=120)
    assert done.returncode == 0, f"the driver did not run:\n{done.stdout}\n{done.stderr}"

    recorded: set[tuple[str, int]] = set()
    for hit_file in hits.glob("*.txt"):
        for entry in hit_file.read_text(encoding="utf-8").splitlines():
            name, _, line = entry.partition("\t")
            if name and line.isdigit():
                recorded.add((Path(name).as_posix(), int(line)))

    target = _target_line()
    module_lines = sorted(line for name, line in recorded if name.endswith(TARGET_MODULE))
    assert any(name.endswith(TARGET_MODULE) and line == target for name, line in recorded), (
        f"the line {target} of {TARGET_MODULE} ran on a worker thread and was not recorded; "
        f"the tracer has no `threading.settrace`. Lines recorded for that module: {module_lines}")
