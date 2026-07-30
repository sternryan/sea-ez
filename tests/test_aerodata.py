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


def test_missing_fingerprint_key_raises(tmp_path, monkeypatch):
    """GATE: a fingerprint missing a key must NOT pass as fresh (F1 fail-open
    bug — NaN-vs-float comparisons are always False, so a dropped key used
    to slip through silently)."""
    import json, seaez.aerodata as ad
    src = json.loads((Path("data/aero/airfoil_polars.json")).read_text())
    del src["fingerprint"]["wing_area_sqft"]
    bad = tmp_path / "airfoil_polars.json"
    bad.write_text(json.dumps(src))
    monkeypatch.setattr(ad, "AIRFOIL_JSON", bad)
    with pytest.raises(StaleAeroData):
        load_airfoil()


def test_clmax_3d_derivation():
    a = load_airfoil()
    assert a.clmax_3d == pytest.approx(a.clmax_2d * CLMAX_3D_FACTOR, rel=1e-6)
    assert 1.2 <= a.clmax_3d <= 2.0            # sanity band


def test_gate_landing_config_stall_within_limit():
    """GATE (Ryan ruling 2026-07-29): landing-config CLmax_3D = (2D airfoil
    clmax + flap_dclmax_2d) x CLMAX_3D_FACTOR must produce a stall speed
    <= stall_limit_kt at gross, AND params.cl_max (the design target) may
    never exceed that computed capability — the honesty gate."""
    a = load_airfoil()
    landing_clmax_3d = (a.clmax_2d + DEFAULT.flap_dclmax_2d) * CLMAX_3D_FACTOR
    vs = stall_speed_kt(_current_fingerprint()["gross_lb"],
                        DEFAULT.wing_area_sqft, landing_clmax_3d)
    print(f"computed landing stall {vs:.2f} kt @ CLmax_3D {landing_clmax_3d:.3f} (limit 24)")
    assert vs <= DEFAULT.stall_limit_kt
    assert DEFAULT.cl_max <= landing_clmax_3d


def test_gate_vspaero_static_margin():
    """GATE: VSPAERO SM >= 8% MAC — threshold restored per Ryan ruling
    2026-07-29 (boom extended +1.5 ft to move the tail out of the
    strongest wake-proximity zone; see docs/research/2026-07-29-airfoil-
    clmax-finding.md RESOLUTION)."""
    v = load_vspaero()
    assert v.static_margin_frac_mac >= 0.08


def test_gate_vspaero_directional_stability():
    """GATE: CNbeta > 0 with the hull modeled — the analytic V_v gate's
    documented blind spot (hull side area) now covered."""
    assert load_vspaero().cnb_per_rad > 0.0


def test_crosscheck_vspaero_vs_analytic_sm():
    """GATE: computed and analytic SM agree within 8 %MAC — divergence
    beyond that means a broken model or a broken analytic assumption.
    Analytic reference recomputed for the +2.5 ft boom / tail_ac_x_ft 19.9
    (Ryan ruling 2026-07-29, acceptance-check max iteration — +1.5 ft gave
    7.54%, +2.0 ft gave 7.66%, +2.5 ft gave exactly 8.0% MAC): NP 47.62% -
    CG 33.82% = 13.80% MAC."""
    v = load_vspaero()
    assert abs(v.static_margin_frac_mac - 0.138) <= 0.08
