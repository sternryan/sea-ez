from pathlib import Path

import pytest

from seaez.ledger import load_parts
from seaez.params import DEFAULT
from seaez.roadmode import road_cg, tipover_ratio

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def test_tipover_ratio_formula():
    # half-track 1.5 ft over CG height 2.0 ft -> tips at 0.75 lateral g
    assert tipover_ratio(2.0, 3.0) == pytest.approx(0.75)


def test_road_cg_lower_wing_than_flight():
    parts = load_parts(PARTS)
    _t, _x, cg_z = road_cg(parts, DEFAULT)
    # folded wing z (2.2) < flight wing z (3.35) must pull road CG below a
    # hypothetical flight-z stack; sanity band from hand calc ~2.0-2.2 ft
    assert 1.8 <= cg_z <= 2.4


def test_gate_road_tipover_margin():
    """GATE (spec §1 success criterion 1): road config tips only above 0.4
    lateral g — generous margin at 5-8 mph pedal speeds."""
    parts = load_parts(PARTS)
    _t, _x, cg_z = road_cg(parts, DEFAULT)
    assert tipover_ratio(cg_z + DEFAULT.keel_to_ground_ft, DEFAULT.track_width_ft) >= 0.4
