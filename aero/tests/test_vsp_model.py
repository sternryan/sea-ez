import openvsp as vsp
import pytest

from aero.vsp_model import build_model
from seaez.params import DEFAULT
from seaez.sizing import planform


def test_model_areas_match_params():
    build_model()
    # CompGeom theoretical planform area for the wing set must match params.
    p = DEFAULT
    wing_area = float(vsp.GetParmVal(vsp.FindGeomsWithName("wing")[0], "TotalArea", "WingGeom"))
    assert wing_area == pytest.approx(p.wing_area_sqft, rel=0.01)


def test_wing_stations_in_bow_keel_frame():
    ids = build_model()
    p = DEFAULT
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    x_le_root = float(vsp.GetParmVal(ids["wing_id"], "X_Rel_Location", "XForm"))
    # root LE = chord center minus half root chord (chords centered on wing_center_x_ft)
    assert x_le_root == pytest.approx(p.wing_center_x_ft - pf.root_chord_ft / 2.0, abs=0.01)
    z = float(vsp.GetParmVal(ids["wing_id"], "Z_Rel_Location", "XForm"))
    assert z == pytest.approx(p.wing_z_ft, abs=0.01)


def test_fin_is_single_surface():
    ids = build_model()
    # Fin must be one surface, not mirrored across the centerline.
    num_surf = vsp.GetNumXSecSurfs(ids["fin_id"]) if hasattr(vsp, "GetNumXSecSurfs") else None
    sym_flag = float(vsp.GetParmVal(ids["fin_id"], "Sym_Planar_Flag", "Sym"))
    assert sym_flag == 0
    if num_surf is not None:
        assert num_surf == 1


def test_returns_all_component_ids():
    ids = build_model()
    assert set(ids.keys()) == {"wing_id", "stab_id", "fin_id", "hull_id"}
    assert all(isinstance(v, str) and v for v in ids.values())


def test_wing_tip_chord_centered_on_wing_center_x():
    # Regression: sizing.planform() centers EVERY chord (root and tip) on
    # wing_center_x_ft (see its docstring); a zero-sweep LE instead aligns
    # the LEs, sweeping the quarter-chord line forward outboard and moving
    # the VLM wing AC to ~14.5% MAC instead of ~25%. Measure the BUILT tip
    # LE surface point (not a parm) so a future regression back to
    # zero-sweep is caught even if some parm still reads "correct".
    ids = build_model()
    p = DEFAULT
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    # u=1.0 is the wingtip station; w=0.5 is the leading edge (min-x) locus
    # of the WING surface parameterization (verified live: w=0/1 are the
    # trailing edge, w=0.5 is the LE).
    tip_le = vsp.CompPnt01(ids["wing_id"], 0, 1.0, 0.5)
    assert tip_le.x() == pytest.approx(p.wing_center_x_ft - pf.tip_chord_ft / 2.0, abs=0.02)


def test_hull_bbox_matches_beam_depth():
    # Regression: a POD geom is a body of revolution (single radius) and
    # cannot represent beam != depth -- it silently builds 2x too wide with
    # its belly below the keel. Measure the BUILT geometry (not just the
    # parms) so a future regression to POD-like behavior is caught.
    ids = build_model()
    p = DEFAULT
    bmin = vsp.GetGeomBBoxMin(ids["hull_id"], 0, True)
    bmax = vsp.GetGeomBBoxMax(ids["hull_id"], 0, True)
    length = bmax.x() - bmin.x()
    beam = bmax.y() - bmin.y()
    assert length == pytest.approx(p.hull_length_ft, abs=0.05)
    assert beam == pytest.approx(p.hull_beam_ft, abs=0.05)
    # Z-extent: keel baseline (0) to spine (hull_depth_ft), nothing below Z=0.
    assert bmin.z() >= -0.05
    assert bmax.z() == pytest.approx(p.hull_depth_ft, abs=0.05)
