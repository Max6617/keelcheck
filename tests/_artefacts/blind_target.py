"""A pytest target that reaches no keel code at all.

Used by `tests/test_coverage_gate.py` to force the gate's blind case: the measurement finds zero
hits, so a zero number is a measurement failure and the gate must refuse rather than report 0%.

Named without a `test_` prefix so the normal suite never collects it; the gate is given the path
explicitly.
"""


def test_nothing_reaches_keel():
    assert True
