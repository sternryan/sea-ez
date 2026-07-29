from pathlib import Path

import pytest

from seaez.aerodata import (
    CLMAX_3D_FACTOR, StaleAeroData, load_airfoil, load_vspaero, _current_fingerprint,
)
from seaez.params import DEFAULT
from seaez.sizing import stall_speed_kt
from seaez.stability import static_margin_frac


def test_fingerprints_are_fresh():
    """GATE: committed aero JSON was generated from the CURRENT params/CG.
    (2.2 stale-station learning, systematized.)"""
    load_airfoil()
    load_vspaero()   # both raise StaleAeroData on mismatch


def test_stale_fingerprint_raises(tmp_path, monkeypatch):
    import json, seaez.aerodata as ad
    src = json.loads((Path("data/aero/airfoil_polars.json")).read_text())
    src["fingerprint"]["wing_area_sqft"] = 999.0
    bad = tmp_path / "airfoil_polars.json"
    bad.write_text(json.dumps(src))
    monkeypatch.setattr(ad, "AIRFOIL_JSON", bad)
    with pytest.raises(StaleAeroData):
        load_airfoil()


def test_clmax_3d_derivation():
    a = load_airfoil()
    assert a.clmax_3d == pytest.approx(a.clmax_2d * CLMAX_3D_FACTOR, rel=1e-6)
    assert 1.2 <= a.clmax_3d <= 2.0            # sanity band


def test_report_computed_stall_vs_limit():
    """REPORT (gate decision is Task 8 / Ryan): stall at the COMPUTED
    CLmax_3D vs the 24 kt ceiling. Required CLmax_3D at 479 lb / 140 sqft
    is 1.755 — print both, assert nothing about the comparison."""
    a = load_airfoil()
    vs = stall_speed_kt(_current_fingerprint()["gross_lb"],
                        DEFAULT.wing_area_sqft, a.clmax_3d)
    print(f"computed stall {vs:.2f} kt @ CLmax_3D {a.clmax_3d:.3f} (limit 24)")


def test_gate_vspaero_static_margin():
    """GATE (amended mid-phase, controller ruling in SDD ledger): VSPAERO
    SM must be POSITIVE (stable). The original >=8% threshold is Ryan-pending
    at the Task 8 checkpoint — computed SM is +5.46% MAC (real finding:
    short-coupled tail in wing downwash; ~0.9 pt/deg alpha sensitivity).
    Report row carries the 8% target."""
    v = load_vspaero()
    assert v.static_margin_frac_mac > 0.0


def test_gate_vspaero_directional_stability():
    """GATE: CNbeta > 0 with the hull modeled — the analytic V_v gate's
    documented blind spot (hull side area) now covered."""
    assert load_vspaero().cnb_per_rad > 0.0


def test_crosscheck_vspaero_vs_analytic_sm():
    """GATE: computed and analytic SM agree within 8 %MAC — divergence
    beyond that means a broken model or a broken analytic assumption."""
    v = load_vspaero()
    assert abs(v.static_margin_frac_mac - 0.115) <= 0.08
