import pytest

from seaez.foldmode import folded_envelope
from seaez.params import DEFAULT


def test_gate_folded_width_under_limit():
    """GATE (spec §4): folded width < 5 ft."""
    env = folded_envelope(DEFAULT)
    assert env.width_ft < DEFAULT.folded_width_limit_ft, f"folded width {env.width_ft:.2f} ft"


def test_folded_length_reconciliation_report():
    """SPEC RECONCILIATION (report, not a pass/fail design gate): spec §4
    estimated folded length ~18-19 ft, but that figure fit the Firefly's
    22 ft span. Our 34 ft span folding aft from the rear-spar pivot reaches
    ~25.7 ft. This test pins the COMPUTED value so any geometry change shows
    up, and the mismatch with spec §4 is Ryan's call (accept longer road
    envelope / shorten span / two-piece fold) — do not silently retune
    fold_pivot_x_ft to force 19 ft."""
    env = folded_envelope(DEFAULT)
    assert env.length_ft == pytest.approx(25.7, abs=0.3)
    assert env.length_ft > 19.0  # documents that the spec §4 estimate is NOT met
