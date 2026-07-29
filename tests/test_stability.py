from pathlib import Path

import pytest

from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import horizontal_tail_volume, planform, stall_speed_kt
from seaez.stability import (
    ROTATION_SPEED_FACTOR, neutral_point_frac, static_margin_frac,
    tail_authority_moment_lbft, thrust_couple_ratio, thrust_pitch_moment_lbft,
)

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def gross_cg():
    parts = load_parts(PARTS)
    return cg(parts, extra_masses=[
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ])


def pf():
    return planform(DEFAULT.wing_area_sqft, DEFAULT.wing_span_ft,
                    DEFAULT.wing_taper_ratio, DEFAULT.wing_center_x_ft)


def vh_actual() -> float:
    _t, cg_x, _z = gross_cg()
    return horizontal_tail_volume(
        DEFAULT.stab_area_sqft, DEFAULT.tail_ac_x_ft - cg_x,
        DEFAULT.wing_area_sqft, pf().mac_ft,
    )


def test_neutral_point_known_value():
    # NP = 0.25 + 0.9*0.85*(1-0.35)*V_h ; V_h=0.3682 -> 0.25+0.1831 = 0.4331
    assert neutral_point_frac(0.3682) == pytest.approx(0.4331, abs=0.002)


def test_static_margin_is_np_minus_cg():
    assert static_margin_frac(0.30, 0.3682) == pytest.approx(0.4331 - 0.30, abs=0.002)


def test_gate_static_margin_no_foreplane():
    """GATE: analytic static margin >= 8% MAC, no foreplane (v1 first-flight
    config, spec §4). Assumption constants documented in seaez/stability.py;
    OpenVSP replaces this estimate in Phase 2.3 (spec §8)."""
    _t, cg_x, _z = gross_cg()
    cg_frac = (cg_x - pf().mac_le_x_ft) / pf().mac_ft
    sm = static_margin_frac(cg_frac, vh_actual())
    assert sm >= 0.08, f"static margin {sm:.1%} MAC"


def test_thrust_moment_formula():
    # 165 lb thrust, 2.24 ft above CG -> 369.6 lb-ft nose-down
    assert thrust_pitch_moment_lbft(165.0, 4.35, 2.11) == pytest.approx(369.6, abs=0.5)


def test_gate_tail_counters_thrust_couple_at_rotation():
    """GATE: tail pitch authority >= 1.2x the full-static-thrust nose-down
    couple at rotation speed (1.2 Vs). This is THE configuration risk of the
    high-pylon pusher (spec §4: foreplane exists for exactly this reason, but
    v1 flies without it — so the tail alone must clear the gate)."""
    total, cg_x, cg_z = gross_cg()
    vs = stall_speed_kt(total, DEFAULT.wing_area_sqft, DEFAULT.cl_max)
    ratio = thrust_couple_ratio(
        thrust_lb=DEFAULT.static_thrust_lb,
        thrust_line_z_ft=DEFAULT.thrust_line_z_ft,
        cg_z_ft=cg_z,
        speed_kt=ROTATION_SPEED_FACTOR * vs,
        stab_area_sqft=DEFAULT.stab_area_sqft,
        tail_arm_ft=DEFAULT.tail_ac_x_ft - cg_x,
    )
    assert ratio >= 1.2, f"tail authority / thrust couple = {ratio:.2f}"
