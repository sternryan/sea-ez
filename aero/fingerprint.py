"""Params fingerprint embedded in every committed aero JSON.

The 2.2 stale-station bug class, systematized: results carry the exact
inputs they were computed from; seaez/aerodata.py refuses mismatches.
"""
from __future__ import annotations

from pathlib import Path

from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import planform

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def params_fingerprint() -> dict:
    p = DEFAULT
    parts = load_parts(PARTS)
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
        "wing_center_x_ft": p.wing_center_x_ft, "wing_z_ft": p.wing_z_ft,
        "stab_span_ft": p.stab_span_ft, "stab_chord_ft": p.stab_chord_ft,
        "hull_length_ft": p.hull_length_ft, "hull_beam_ft": p.hull_beam_ft,
        "hull_depth_ft": p.hull_depth_ft,
        # aero/vsp_model.py places stab & fin XForm Z at hull_depth_ft + 0.5;
        # fingerprinted here under its own name so a T-tail / stab-Z change
        # trips staleness even though no other param moves (F2, F3).
        "tail_z_ft": p.hull_depth_ft + 0.5,
    }
