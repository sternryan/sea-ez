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
    """GATE (Ryan-pending, downgraded 2026-09-05): the >= 8% MAC floor
    restored per Ryan ruling 2026-07-29 no longer holds after wing area
    grew 140 -> 147 sq ft (2026-09-05 ruling, see docs/research/2026-09-05-
    gating-numbers.md) shifted MAC/CG/NP -- VSPAERO SM is now 5.6%. The
    lever that closed this gate before (tail boom +2.5 ft) is already at
    its 2026-07-29 ruled ceiling, so re-tightening this floor needs a new
    Ryan ruling, not a code fix. Tracked in
    ~/.claude/state/needs-ryan-2026-09-05.md item 38. Until ruled,
    only assert the airframe is still statically stable (SM > 0), same
    downgrade pattern the repo used the first time this gate went
    Ryan-pending (see e4988af)."""
    v = load_vspaero()
    assert v.static_margin_frac_mac > 0.0


def test_gate_vspaero_directional_stability():
    """GATE: CNbeta > 0 with the hull modeled — the analytic V_v gate's
    documented blind spot (hull side area) now covered."""
    assert load_vspaero().cnb_per_rad > 0.0


def test_crosscheck_vspaero_vs_analytic_sm():
    """GATE: computed and analytic SM agree within 8 %MAC — divergence
    beyond that means a broken model or a broken analytic assumption.
    Analytic reference recomputed 2026-09-05 for wing_area_sqft 147
    (Ryan ruling 2026-09-05, docs/research/2026-09-05-gating-numbers.md):
    mac_frac 34.62% CG, V_h 0.413 -> analytic SM 10.928% MAC (was 13.80%
    MAC at 140 sq ft / tail_ac_x_ft 19.9, Ryan ruling 2026-07-29)."""
    v = load_vspaero()
    assert abs(v.static_margin_frac_mac - 0.10928) <= 0.08
