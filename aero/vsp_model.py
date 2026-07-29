"""Build the sea-ez no-foreplane OpenVSP model from DesignParams.

Frame: OpenVSP X aft = bow datum, Z up = keel baseline (no conversion
anywhere -- datum discipline). Hull is a simple pod with the massing hull's
length/beam/depth so VSPAERO sees fuselage side area (the analytic V_v
gate's known blind spot). Design-consistency tooling -- NOT validated
engineering and NOT airworthiness proof.
"""
from __future__ import annotations

import math
from pathlib import Path

import openvsp as vsp

from seaez.params import DEFAULT
from seaez.sizing import planform


def _set(gid: str, group: str, **parms: float) -> None:
    for name, val in parms.items():
        vsp.SetParmValUpdate(gid, name, group, val)


def build_model(save_path: Path | None = None) -> dict:
    p = DEFAULT
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    vsp.ClearVSPModel()

    # sizing.planform() centers EVERY chord (root and tip) on wing_center_x_ft
    # (see its docstring; the 31.8% MAC CG gate depends on this frame). With
    # a tapered wing that means the tip LE sits aft of the root LE by half
    # the chord difference -- a zero-sweep LE would instead align the LEs
    # and sweep the quarter-chord line forward outboard, moving the VLM
    # wing AC to ~14.5% MAC instead of ~25%. Derive the LE sweep from params
    # so the built wing matches the chords-centered convention exactly.
    wing_le_sweep_deg = math.degrees(math.atan(
        ((pf.root_chord_ft - pf.tip_chord_ft) / 2.0) / (p.wing_span_ft / 2.0)))

    wing = vsp.AddGeom("WING")
    vsp.SetGeomName(wing, "wing")
    _set(wing, "XSec_1", Span=p.wing_span_ft / 2.0,
         Root_Chord=pf.root_chord_ft, Tip_Chord=pf.tip_chord_ft,
         Sweep=wing_le_sweep_deg)
    # Sweep_Location defaults to 0.0 (LE-referenced, verified live) so Sweep
    # above is applied at the leading edge, not the quarter-chord.
    # Root LE sits half a root chord forward of wing_center_x_ft; the LE
    # sweep above carries the tip LE aft to center_x - tip_chord/2 to match.
    _set(wing, "XForm",
         X_Rel_Location=p.wing_center_x_ft - pf.root_chord_ft / 2.0,
         Z_Rel_Location=p.wing_z_ft)

    stab = vsp.AddGeom("WING")
    vsp.SetGeomName(stab, "stab")
    _set(stab, "XSec_1", Span=p.stab_span_ft / 2.0,
         Root_Chord=p.stab_chord_ft, Tip_Chord=p.stab_chord_ft, Sweep=0.0)
    _set(stab, "XForm",
         X_Rel_Location=p.tail_ac_x_ft - p.stab_chord_ft / 4.0,  # AC at quarter-chord
         Z_Rel_Location=p.hull_depth_ft + 0.5)

    fin = vsp.AddGeom("WING")
    vsp.SetGeomName(fin, "fin")
    fin_span, fin_chord = 3.0, p.fin_area_sqft / 3.0  # 3 ft tall, area-preserving chord
    _set(fin, "XSec_1", Span=fin_span, Root_Chord=fin_chord,
         Tip_Chord=fin_chord, Sweep=0.0)
    _set(fin, "XForm",
         X_Rel_Location=p.tail_ac_x_ft - fin_chord / 4.0,
         Z_Rel_Location=p.hull_depth_ft + 0.5,
         X_Rel_Rotation=90.0)  # rotate planar surface vertical
    vsp.SetParmValUpdate(fin, "Sym_Planar_Flag", "Sym", 0)  # single surface, no mirror

    # POD is a body of revolution (single radius) and cannot represent a
    # beam (2.5 ft) != depth (1.35 ft) cross-section -- FineRatio only sets
    # length/radius, so a POD built to spec silently comes out 2x too wide
    # and z-centered below the keel baseline. Use FUSELAGE instead: its
    # middle cross-sections take independent width/height, and the built
    # geometry (not just the parm) is verified against the bow/keel frame
    # by test_hull_bbox_matches_beam_depth below.
    hull = vsp.AddGeom("FUSELAGE")
    vsp.SetGeomName(hull, "hull")
    vsp.SetParmValUpdate(hull, "Length", "Design", p.hull_length_ft)
    hull_xsec_surf = vsp.GetXSecSurf(hull, 0)
    # Default fuselage has 5 XSecs: pointed nose (0), three full-beam middle
    # sections (1-3), pointed tail (4). Set the middle sections to the hull's
    # true beam/depth; leave the end caps pointed (representative side area,
    # not hull fidelity).
    for i in range(1, vsp.GetNumXSec(hull_xsec_surf) - 1):
        vsp.SetXSecWidthHeight(vsp.GetXSec(hull_xsec_surf, i), p.hull_beam_ft, p.hull_depth_ft)
    _set(hull, "XForm", X_Rel_Location=0.0, Z_Rel_Location=p.hull_depth_ft / 2.0)

    vsp.Update()
    if save_path is not None:
        vsp.WriteVSPFile(str(save_path), vsp.SET_ALL)
    return {"wing_id": wing, "stab_id": stab, "fin_id": fin, "hull_id": hull}
