"""Gate-lane loader for committed aero results (data/aero/*.json).

The aero lane (tools/venv313: OpenVSP + XFOIL) writes these files via
`make aero`; this module is how gates consume them WITHOUT importing any
aero tooling. Every load re-derives the params fingerprint in pure python
and refuses stale data — the 2.2 stale-station bug class, systematized.
Design-consistency checks on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import planform

ROOT = Path(__file__).parent.parent
AIRFOIL_JSON = ROOT / "data" / "aero" / "airfoil_polars.json"
VSPAERO_JSON = ROOT / "data" / "aero" / "vspaero_stability.json"
CLMAX_3D_FACTOR = 0.90  # classic unswept AR~8 2D->3D decrement (documented, fixed)


class StaleAeroData(RuntimeError):
    pass


def _current_fingerprint() -> dict:
    p = DEFAULT
    parts = load_parts(ROOT / "data" / "parts.yaml")
    gross, cg_x, cg_z = cg(parts, extra_masses=[
        (p.pilot_lb, p.seat_x_ft, p.seat_z_flight_ft),
        (p.fuel_lb, p.fuel_x_ft, p.fuel_z_ft),
    ])
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    return {
        "wing_area_sqft": p.wing_area_sqft, "wing_span_ft": p.wing_span_ft,
        "wing_taper_ratio": p.wing_taper_ratio, "gross_lb": round(gross, 2),
        "mac_ft": round(pf.mac_ft, 4), "stall_limit_kt": p.stall_limit_kt,
        "stab_area_sqft": p.stab_area_sqft, "fin_area_sqft": p.fin_area_sqft,
        "tail_ac_x_ft": p.tail_ac_x_ft,
        "cg_x_ft": round(cg_x, 4), "cg_z_ft": round(cg_z, 4),
    }


def _check(fp: dict, path: Path) -> None:
    cur = _current_fingerprint()
    diffs = {k: (fp.get(k), cur[k]) for k in cur
             if k not in fp or abs(float(fp[k]) - cur[k]) > 1e-3}
    if diffs:
        raise StaleAeroData(f"{path.name} stale vs current params {diffs} — run make aero")


@dataclass(frozen=True)
class AirfoilResult:
    selected: str
    clmax_2d: float
    clmax_3d: float
    reynolds_mac: float


@dataclass(frozen=True)
class VspaeroResult:
    static_margin_frac_mac: float
    cnb_per_rad: float
    neutral_point_frac_mac: float


def load_airfoil() -> AirfoilResult:
    d = json.loads(AIRFOIL_JSON.read_text())
    _check(d["fingerprint"], AIRFOIL_JSON)
    best = d["candidates"][d["selected"]]
    return AirfoilResult(
        selected=d["selected"], clmax_2d=best["clmax_2d"],
        clmax_3d=best["clmax_2d"] * CLMAX_3D_FACTOR,
        reynolds_mac=d["reynolds_mac"],
    )


def load_vspaero() -> VspaeroResult:
    d = json.loads(VSPAERO_JSON.read_text())
    _check(d["fingerprint"], VSPAERO_JSON)
    return VspaeroResult(
        static_margin_frac_mac=d["static_margin_frac_mac"],
        cnb_per_rad=d["derivatives"]["CNb_per_rad"],
        neutral_point_frac_mac=d["derivatives"]["neutral_point_frac_mac"],
    )
