# tests/test_cg.py
from pathlib import Path

import pytest

from seaez.ledger import Part, cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import planform

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def _part(name, mass, x, z):
    return Part(
        name=name, group="test", mass_lb=mass, classification="secondary",
        process="purchased", counts_toward_empty=True, is_chute=False,
        x_ft=x, z_ft=z,
    )


def test_cg_two_point_masses():
    parts = [_part("a", 10.0, 0.0, 0.0), _part("b", 10.0, 10.0, 2.0)]
    total, cgx, cgz = cg(parts)
    assert total == pytest.approx(20.0)
    assert cgx == pytest.approx(5.0)
    assert cgz == pytest.approx(1.0)


def test_cg_with_extra_masses():
    parts = [_part("a", 10.0, 0.0, 0.0)]
    total, cgx, cgz = cg(parts, extra_masses=[(30.0, 4.0, 2.0)])
    assert total == pytest.approx(40.0)
    assert cgx == pytest.approx(3.0)
    assert cgz == pytest.approx(1.5)


def test_all_ledger_parts_have_plausible_stations():
    parts = load_parts(PARTS)
    for p in parts:
        assert 0.0 <= p.x_ft <= 18.5, f"{p.name}: x_ft outside airframe length"
        assert 0.0 <= p.z_ft <= 5.0, f"{p.name}: z_ft outside airframe height"


def gross_cg():
    parts = load_parts(PARTS)
    extras = [
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ]
    return cg(parts, extra_masses=extras)


def test_gate_gross_cg_within_mac_band():
    """GATE: gross CG (pilot + full fuel) inside 25-35% MAC.

    Band is the conventional first-pass envelope for a high-wing pusher;
    Phase 2.2's OpenVSP static-margin gate replaces it with a computed
    neutral point (spec §8).
    """
    pf = planform(
        DEFAULT.wing_area_sqft, DEFAULT.wing_span_ft,
        DEFAULT.wing_taper_ratio, DEFAULT.wing_center_x_ft,
    )
    _total, cg_x, _cg_z = gross_cg()
    frac = (cg_x - pf.mac_le_x_ft) / pf.mac_ft
    assert 0.25 <= frac <= 0.35, f"gross CG at {frac:.1%} MAC, outside 25-35%"


def test_gate_gross_weight_sane():
    """GATE: actual gross stays inside the spec §3 design band."""
    total, _cg_x, _cg_z = gross_cg()
    assert 470.0 <= total <= 500.0
