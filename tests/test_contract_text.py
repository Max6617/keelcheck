from pathlib import Path

CONTRACT = Path(__file__).with_name("CONTRACT.md")


def test_contract_has_no_control_characters():
    data = CONTRACT.read_bytes()
    bad = sorted({b for b in data if b <= 0x09 or 0x0B <= b <= 0x1F})
    assert not bad, f"control bytes in CONTRACT.md: {[hex(b) for b in bad]}"


def test_contract_keeps_the_names_a_newline_ate():
    text = CONTRACT.read_bytes().decode("utf-8")
    for name in ("no-such-file.md", "review-<utc second>/", "result: malformed"):
        assert name in text
