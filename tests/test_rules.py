from pathlib import Path

from seaez.ledger import Part, load_parts
from seaez.rules import violations

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def test_real_ledger_has_no_violations():
    assert violations(load_parts(PARTS)) == []


def test_printed_primary_structure_is_rejected():
    bad = Part(
        name="printed_spar", group="wing", mass_lb=5.0,
        classification="primary_structure", process="fdm_print",
        counts_toward_empty=True, is_chute=False,
    )
    out = violations([bad])
    assert len(out) == 1
    assert "printed_spar" in out[0]
    assert "primary structure" in out[0].lower()
