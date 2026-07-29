from pathlib import Path

import pytest

from seaez.ledger import load_parts, rollup_empty_lb, chute_lb, cg
from seaez.params import DEFAULT
from seaez.sizing import stall_speed_kt, wing_area_for_stall, planform, horizontal_tail_volume, vertical_tail_volume

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


def test_planform_geometry():
    # S=140, b=34, taper 0.65, unswept with chords centered at x=7.9
    pf = planform(140.0, 34.0, 0.65, 7.9)
    assert pf.root_chord_ft == pytest.approx(4.991, abs=0.01)   # 2S / (b(1+t))
    assert pf.tip_chord_ft == pytest.approx(3.244, abs=0.01)
    assert pf.mac_ft == pytest.approx(4.179, abs=0.01)          # (2/3)Cr(1+t+t^2)/(1+t)
    assert pf.mac_le_x_ft == pytest.approx(7.9 - 4.179 / 2.0, abs=0.01)


def test_planform_untapered_mac_equals_chord():
    pf = planform(140.0, 34.0, 1.0, 7.9)
    assert pf.mac_ft == pytest.approx(140.0 / 34.0, abs=1e-9)


def tail_arm_ft() -> float:
    """Tail AC to actual gross CG (bow datum)."""
    parts = load_parts(PARTS)
    _t, cg_x, _z = cg(parts, extra_masses=[
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ])
    return DEFAULT.tail_ac_x_ft - cg_x


def test_tail_volume_formulas_known_point():
    # S_h=21, l=10.26, S=140, MAC=4.1794 -> V_h ~ 0.368
    assert horizontal_tail_volume(21.0, 10.2597, 140.0, 4.1794) == pytest.approx(0.3682, abs=0.001)
    # S_v=6, l=10.26, S=140, b=34 -> V_v ~ 0.0129
    assert vertical_tail_volume(6.0, 10.2597, 140.0, 34.0) == pytest.approx(0.01293, abs=0.0003)


def test_gate_horizontal_tail_volume():
    """GATE: V_h >= 0.35 (low end of light-aircraft practice; ultralights run
    low, but the high-pylon thrust couple argues against going lower)."""
    vh = horizontal_tail_volume(
        DEFAULT.stab_area_sqft, tail_arm_ft(), DEFAULT.wing_area_sqft,
        planform(DEFAULT.wing_area_sqft, DEFAULT.wing_span_ft,
                 DEFAULT.wing_taper_ratio, DEFAULT.wing_center_x_ft).mac_ft,
    )
    assert vh >= 0.35, f"V_h = {vh:.3f}"


def test_gate_vertical_tail_volume():
    """GATE: V_v >= 0.012 (ultralight-typical low end)."""
    vv = vertical_tail_volume(
        DEFAULT.fin_area_sqft, tail_arm_ft(), DEFAULT.wing_area_sqft, DEFAULT.wing_span_ft,
    )
    assert vv >= 0.012, f"V_v = {vv:.4f}"


def test_reynolds_at_stall_mac():
    # Vs 23.69 kt, MAC 4.1794 ft, nu 1.5722e-4 -> Re ~= 1.063e6
    from seaez.sizing import reynolds
    assert reynolds(23.69, 4.1794) == pytest.approx(1.063e6, rel=0.01)
