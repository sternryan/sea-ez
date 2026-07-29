"""Sweep candidate airfoils through XFOIL at the stall-MAC Reynolds number
and write data/aero/airfoil_polars.json (committed; gates consume it).

Candidates per Ryan's 2026-07-29 ruling: mod-NACA-4412 family + USA-35B
class. Design-consistency tooling — NOT validated engineering.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from aero.fingerprint import params_fingerprint
from aero.xfoil_runner import clmax, run_polar
from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import planform, reynolds, stall_speed_kt

ROOT = Path(__file__).parent.parent
CANDIDATES = {
    "naca4412": "NACA 4412",
    "naca4415": "NACA 4415",
    "usa35b": ROOT / "data" / "airfoils" / "usa35b.dat",
}


def main() -> None:
    p = DEFAULT
    fp = params_fingerprint()
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    vs = stall_speed_kt(fp["gross_lb"], p.wing_area_sqft, p.cl_max)
    re_mac = reynolds(vs, pf.mac_ft)

    out = {"fingerprint": fp, "reynolds_mac": round(re_mac), "ncrit": 9,
           "candidates": {}, "selected": None,
           "selection_rule": "highest clmax_2d; cd_at_cl_1p0 tiebreak"}
    for key, spec in CANDIDATES.items():
        with tempfile.TemporaryDirectory() as td:
            pts = run_polar(spec, re_mac, 0.0, 19.0, 1.0, Path(td))
        cl, a = clmax(pts)
        at_cl = min(pts, key=lambda q: abs(q.cl - 1.0))
        cm_at = min(pts, key=lambda q: abs(q.alpha_deg - a)).cm
        out["candidates"][key] = {
            "clmax_2d": round(cl, 4), "alpha_clmax_deg": a,
            "cm_at_clmax": round(cm_at, 4), "cd_at_cl_1p0": round(at_cl.cd, 5),
            "polar": [[q.alpha_deg, q.cl, q.cd, q.cm] for q in pts],
        }
        print(f"{key}: clmax_2d {cl:.3f} @ {a:.0f} deg")

    ranked = sorted(out["candidates"].items(),
                    key=lambda kv: (-kv[1]["clmax_2d"], kv[1]["cd_at_cl_1p0"]))
    out["selected"] = ranked[0][0]
    dest = ROOT / "data" / "aero" / "airfoil_polars.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print(f"selected: {out['selected']} -> {dest}")


if __name__ == "__main__":
    main()
