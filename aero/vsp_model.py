"""Build the sea-ez no-foreplane OpenVSP model from DesignParams.

Frame: OpenVSP X aft = bow datum, Z up = keel baseline (no conversion
anywhere -- datum discipline). Hull is a simple pod with the massing hull's
length/beam/depth so VSPAERO sees fuselage side area (the analytic V_v
gate's known blind spot). Design-consistency tooling -- NOT validated
engineering and NOT airworthiness proof.
"""
from __future__ import annotations

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

    wing = vsp.AddGeom("WING")
    vsp.SetGeomName(wing, "wing")
    _set(wing, "XSec_1", Span=p.wing_span_ft / 2.0,
         Root_Chord=pf.root_chord_ft, Tip_Chord=pf.tip_chord_ft, Sweep=0.0)
    # Zero sweep is at the LE by default; chords centered on wing_center_x_ft
    # means the root LE sits half a root chord forward of it.
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

    hull = vsp.AddGeom("POD")
    vsp.SetGeomName(hull, "hull")
    _set(hull, "Design", Length=p.hull_length_ft, FineRatio=p.hull_length_ft / p.hull_beam_ft)
    _set(hull, "XForm", X_Rel_Location=0.0, Z_Rel_Location=p.hull_depth_ft / 2.0)

    vsp.Update()
    if save_path is not None:
        vsp.WriteVSPFile(str(save_path), vsp.SET_ALL)
    return {"wing_id": wing, "stab_id": stab, "fin_id": fin, "hull_id": hull}
