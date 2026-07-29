from pathlib import Path

import pytest

from seaez.ledger import load_parts, rollup_empty_lb, chute_lb
from seaez.params import DEFAULT
from seaez.sizing import stall_speed_kt, wing_area_for_stall

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def gross_actual_lb() -> float:
    """Actual gross from the ledger: airframe + chute + pilot + full fuel."""
    parts = load_parts(PARTS)
    return rollup_empty_lb(parts) + chute_lb(parts) + DEFAULT.pilot_lb + DEFAULT.fuel_lb


def test_stall_math_known_point():
    # 490 lb / 140 sqft / CLmax 1.8 at sea level -> ~23.97 kt
    assert stall_speed_kt(490.0, 140.0, 1.8) == pytest.approx(23.97, abs=0.05)


def test_area_and_speed_are_inverses():
    area = wing_area_for_stall(490.0, 24.0, 1.8)
    assert stall_speed_kt(490.0, area, 1.8) == pytest.approx(24.0, abs=1e-6)


def test_gate_stall_at_actual_gross_within_limit():
    """GATE (spec §2): power-off stall <= 24 kt at actual ledger gross."""
    vs = stall_speed_kt(gross_actual_lb(), DEFAULT.wing_area_sqft, DEFAULT.cl_max)
    assert vs <= DEFAULT.stall_limit_kt


def test_gate_stall_at_design_gross_within_limit():
    """GATE: still legal at the top of the design gross band."""
    vs = stall_speed_kt(DEFAULT.gross_design_lb, DEFAULT.wing_area_sqft, DEFAULT.cl_max)
    assert vs <= DEFAULT.stall_limit_kt
