"""
sea-ez v0 massing model.

VISUALIZATION-GRADE GEOMETRY ONLY. This is NOT an engineering model — no
aero surfaces, no structural members, no laminate schedule. It exists to
check configuration, proportions, and stance against the spec
(docs/superpowers/specs/2026-07-28-sea-motorcycle-ultralight-design.md,
section 4 "Configuration") before any real design work starts.

Mode modeled: FLIGHT — wings spread and pinned, gear retracted, prop
running, on a neutral (waterline) stance.

Coordinate frame:
  X : bow (0) -> stern/tail (aft, +X), feet
  Y : lateral, centerline at 0, right wing = +Y, feet
  Z : up from the hull keel baseline (Z=0 at keel bottom reference), feet

Run directly to build the assembly and export STL + 3 shaded PNGs:
    .venv/bin/python design/massing_v0.py
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

import cadquery as cq
import numpy as np
import trimesh

# --------------------------------------------------------------------------
# Constants (feet unless noted). Values are massing-grade per the team-lead
# brief; see spec doc for the design rationale behind each number.
# --------------------------------------------------------------------------

# --- Hull ---
HULL_LENGTH_FT = 12.0
HULL_BEAM_FT = 2.5
HULL_STEP_FRACTION = 0.55           # step at 55% of hull length from bow
HULL_KEEL_Z = 0.0                   # baseline / neutral waterline reference
HULL_SPINE_Z = 1.35                 # top-of-spine height above keel baseline
HULL_MAX_HALF_BEAM = HULL_BEAM_FT / 2.0

# --- Rider ---
RIDER_SEAT_X = 6.3                  # amidships, just fwd of the step
RIDER_SEAT_Z = HULL_SPINE_Z + 0.15
RIDER_LEAN_DEG = 25.0               # forward "cafe racer" lean off vertical
RIDER_TORSO_LEN = 2.1
RIDER_HIP_TO_HEAD = 2.6             # hip pivot to top of helmet, along spine

# --- Wing ---
WING_AREA_SQFT = 140.0
WING_SPAN_FT = 34.0
WING_CHORD_FT = WING_AREA_SQFT / WING_SPAN_FT   # ~4.12 ft
WING_HEIGHT_ABOVE_SPINE_FT = 2.0
# wing root LE positioned so the wing's center sits above/behind the rider
WING_CENTER_X = RIDER_SEAT_X + 1.6
WING_LE_X = WING_CENTER_X - WING_CHORD_FT / 2.0
WING_TE_X = WING_CENTER_X + WING_CHORD_FT / 2.0
WING_Z = HULL_SPINE_Z + WING_HEIGHT_ABOVE_SPINE_FT
WING_THICKNESS_FRAC = 0.12          # airfoil-ish thickness for massing only
WING_TIP_CHORD_FRAC = 0.65          # simple taper, tip chord / root chord

# --- Cabane / pylon structure holding the wing up ---
CABANE_COUNT_EACH_SIDE = 1

# --- Engine pylon + pusher prop (aft of wing TE) ---
PROP_DIA_FT = 4.3
PROP_GUARD_RING_THICKNESS = 0.12
ENGINE_HEIGHT_ABOVE_SPINE_FT = 3.0
ENGINE_AFT_OF_WING_TE_FT = 1.6       # prop disc center, aft of wing TE
PROP_CENTER_X = WING_TE_X + ENGINE_AFT_OF_WING_TE_FT
PROP_CENTER_Z = HULL_SPINE_Z + ENGINE_HEIGHT_ABOVE_SPINE_FT
PYLON_WIDTH = 0.35

# --- Tail boom + empennage ---
OVERALL_LENGTH_FT = 18.5
BOOM_DIA_FT = 0.35
STAB_SPAN_FT = 7.0
STAB_CHORD_FT = 1.4
FIN_HEIGHT_FT = 2.0
FIN_CHORD_FT = 1.6

# --- Bow canards ("bar-end winglets") ---
CANARD_CHORD_FT = 0.5
CANARD_COMBINED_SPAN_FT = 2.0        # both fins together
CANARD_X = 1.1
CANARD_Z = HULL_SPINE_Z + 0.7

# --- Wingtip sponsons ---
SPONSON_LENGTH_FT = 1.6
SPONSON_WIDTH_FT = 0.55
SPONSON_DROP_BELOW_WING_FT = 1.0

# --- Retracted gear bulges ---
GEAR_BULGE_RADIUS = 0.28
GEAR_BULGE_X = RIDER_SEAT_X - 0.3
NOSEWHEEL_FAIRING_X = 2.0
NOSEWHEEL_FAIRING_RADIUS = 0.22

MM_PER_FT = 304.8  # cadquery has no implicit units; we work directly in feet


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def _yz_ellipse_station(x: float, half_beam: float, height: float, center_z: float):
    """One loft cross-section: an ellipse in the YZ plane at hull-station x."""
    return cq.Workplane("YZ").workplane(offset=x).center(0, center_z).ellipse(
        max(half_beam, 0.02), max(height, 0.02)
    )


@dataclass
class HullRef:
    spine_z: float
    keel_z: float
    step_x: float
    stern_x: float
    bow_x: float = 0.0


@dataclass
class WingRef:
    span: float
    chord: float
    le_x: float
    te_x: float
    center_x: float
    z: float
    half_span: float = field(init=False)

    def __post_init__(self) -> None:
        self.half_span = self.span / 2.0


# --------------------------------------------------------------------------
# Assemblies
# --------------------------------------------------------------------------

def build_hull() -> tuple[cq.Workplane, HullRef]:
    """Stepped planing hull: pointed bow, single step at 55% length, motorcycle-
    like raised spine amidships, tapered stern."""
    step_x = HULL_LENGTH_FT * HULL_STEP_FRACTION
    stern_x = HULL_LENGTH_FT

    stations = [
        # x, half_beam, height, center_z
        (0.0, 0.03, 0.03, HULL_SPINE_Z * 0.6),
        (0.9, 0.55, 0.55, HULL_SPINE_Z * 0.7),
        (2.6, 0.95, 0.95, HULL_SPINE_Z * 0.85),
        (4.4, HULL_MAX_HALF_BEAM, 1.05, HULL_SPINE_Z * 0.95),
        (step_x - 0.15, HULL_MAX_HALF_BEAM, 1.05, HULL_SPINE_Z * 0.95),
        # the step: a visible drop in keel/bottom line, spine stays high
        (step_x + 0.15, HULL_MAX_HALF_BEAM * 0.92, 0.85, HULL_SPINE_Z * 0.82),
        (9.6, 0.75, 0.68, HULL_SPINE_Z * 0.78),
        (stern_x, 0.12, 0.30, HULL_SPINE_Z * 0.55),
    ]

    # NOTE: both Workplane.workplane(offset=...) AND Workplane.center(...)
    # are DELTAS from the previous station in the chain, not absolute
    # coordinates from the base plane — so every offset/center below is a
    # delta from the prior station's (x, center_z).
    wp = cq.Workplane("YZ")
    prev_x = 0.0
    prev_cz = 0.0
    first_x, hb, h, cz = stations[0]
    wp = wp.workplane(offset=first_x).center(0, cz).ellipse(max(hb, 0.02), max(h, 0.02))
    prev_x, prev_cz = first_x, cz
    for x, hb, h, cz in stations[1:]:
        wp = wp.workplane(offset=x - prev_x).center(0, cz - prev_cz).ellipse(
            max(hb, 0.02), max(h, 0.02)
        )
        prev_x, prev_cz = x, cz
    hull = wp.loft(ruled=True)

    ref = HullRef(spine_z=HULL_SPINE_Z, keel_z=HULL_KEEL_Z, step_x=step_x, stern_x=stern_x)
    return hull, ref


def build_rider(hull_ref: HullRef) -> tuple[cq.Workplane, tuple[float, float]]:
    """Simple posed mannequin straddling the seat, leaned forward, helmeted
    head. Returns the solid and the (x, z) position of the head-top for the
    prop-clearance sanity check."""
    lean = math.radians(RIDER_LEAN_DEG)
    hip = (RIDER_SEAT_X, RIDER_SEAT_Z)

    # torso: a capsule-ish cylinder tilted forward from the hip
    torso_top = (
        hip[0] - RIDER_TORSO_LEN * math.sin(lean),
        hip[1] + RIDER_TORSO_LEN * math.cos(lean),
    )
    # torso: a cylinder along the lean axis from hip to shoulder
    torso_solid = _tilted_cylinder(hip, torso_top, 0.28)

    # head: sphere + a slightly larger "helmet" shell, at hip->head distance
    head_center = (
        hip[0] - RIDER_HIP_TO_HEAD * math.sin(lean),
        hip[1] + RIDER_HIP_TO_HEAD * math.cos(lean),
    )
    head = (
        cq.Workplane("XY")
        .workplane(offset=head_center[1])
        .center(head_center[0], 0)
        .sphere(0.42)
    )

    # legs: two thin cylinders straddling the hull, hip down to footpeg
    footpeg_z = hull_ref.spine_z - 0.35
    leg_y = HULL_MAX_HALF_BEAM * 0.55
    leg_r = 0.11
    leg_l = _tilted_cylinder_3d((hip[0], leg_y, hip[1]), (hip[0] + 0.3, leg_y, footpeg_z), leg_r)
    leg_rt = _tilted_cylinder_3d((hip[0], -leg_y, hip[1]), (hip[0] + 0.3, -leg_y, footpeg_z), leg_r)

    rider = torso_solid.union(head).union(leg_l).union(leg_rt)
    head_top = (head_center[0], head_center[1] + 0.42)
    return rider, head_top


def _tilted_cylinder(p0_xz: tuple[float, float], p1_xz: tuple[float, float], radius: float) -> cq.Workplane:
    """Cylinder between two points in the XZ plane (Y=0), built via extrude
    along the vector then rotate/translate into place."""
    return _tilted_cylinder_3d((p0_xz[0], 0.0, p0_xz[1]), (p1_xz[0], 0.0, p1_xz[1]), radius)


def _tilted_cylinder_3d(p0: tuple[float, float, float], p1: tuple[float, float, float], radius: float) -> cq.Workplane:
    p0v = cq.Vector(*p0)
    p1v = cq.Vector(*p1)
    axis = p1v - p0v
    length = axis.Length
    cyl = cq.Solid.makeCylinder(radius, length, p0v, axis)
    return cq.Workplane(obj=cyl)


def build_wing() -> tuple[cq.Workplane, WingRef]:
    """High wing: simple tapered planform, symmetric about centerline,
    mounted above/behind the rider. Modeled as a thin tapered slab
    (airfoil-ish thickness) — massing only, no aero section."""
    root_chord = WING_CHORD_FT
    tip_chord = WING_CHORD_FT * WING_TIP_CHORD_FRAC
    thickness = root_chord * WING_THICKNESS_FRAC
    half_span = WING_SPAN_FT / 2.0

    # Build one half-wing via loft between root and tip rectangles in an
    # XZ-profile plane swept along Y, then mirror.
    def half_wing_section(y: float, chord: float):
        le = WING_CENTER_X - chord / 2.0
        te = WING_CENTER_X + chord / 2.0
        return (
            cq.Workplane("XZ")
            .workplane(offset=y)
            .moveTo(le, WING_Z - thickness / 2.0)
            .lineTo(te, WING_Z - thickness / 2.0)
            .lineTo(te, WING_Z + thickness / 2.0)
            .lineTo(le, WING_Z + thickness / 2.0)
            .close()
        )

    root = half_wing_section(0.0, root_chord)

    # workplane(offset=...) is a DELTA from the previous station, not an
    # absolute Y — same gotcha as the hull loft above.
    mid_y = half_span * 0.15
    mid_chord = root_chord * 0.92
    wp = root
    wp = wp.workplane(offset=mid_y).moveTo(
        WING_CENTER_X - mid_chord / 2.0, WING_Z - thickness / 2.0
    ).lineTo(WING_CENTER_X + mid_chord / 2.0, WING_Z - thickness / 2.0).lineTo(
        WING_CENTER_X + mid_chord / 2.0, WING_Z + thickness / 2.0
    ).lineTo(WING_CENTER_X - mid_chord / 2.0, WING_Z + thickness / 2.0).close()
    wp = wp.workplane(offset=half_span - mid_y).moveTo(
        WING_CENTER_X - tip_chord / 2.0, WING_Z - thickness / 2.0
    ).lineTo(WING_CENTER_X + tip_chord / 2.0, WING_Z - thickness / 2.0).lineTo(
        WING_CENTER_X + tip_chord / 2.0, WING_Z + thickness / 2.0
    ).lineTo(WING_CENTER_X - tip_chord / 2.0, WING_Z + thickness / 2.0).close()

    right_half = wp.loft(ruled=True)
    left_half = right_half.mirror(mirrorPlane="XZ")
    wing = right_half.union(left_half)

    ref = WingRef(
        span=WING_SPAN_FT, chord=WING_CHORD_FT, le_x=WING_LE_X, te_x=WING_TE_X,
        center_x=WING_CENTER_X, z=WING_Z,
    )
    return wing, ref


def build_cabane(hull_ref: HullRef, wing_ref: WingRef) -> cq.Workplane:
    """Short cabane/pylon struts holding the wing above the hull spine."""
    strut_r = 0.06
    struts = None
    for y in (-0.55, 0.55):
        base = (wing_ref.center_x - 0.3, y, hull_ref.spine_z)
        top = (wing_ref.center_x - 0.3, y, wing_ref.z - 0.06)
        s = _tilted_cylinder_3d(base, top, strut_r)
        struts = s if struts is None else struts.union(s)
    for y in (-0.55, 0.55):
        base = (wing_ref.center_x + 0.5, y, hull_ref.spine_z)
        top = (wing_ref.center_x + 0.5, y, wing_ref.z - 0.06)
        s = _tilted_cylinder_3d(base, top, strut_r)
        struts = struts.union(s)
    return struts


def build_pylon_and_prop(hull_ref: HullRef) -> tuple[cq.Workplane, tuple[float, float]]:
    """Engine pylon aft of wing TE, pusher prop enclosed in a full circular
    guard ring, centered above the hull spine and clearly behind the rider."""
    pylon_base = (PROP_CENTER_X - 0.4, 0.0, hull_ref.spine_z)
    pylon_top = (PROP_CENTER_X, 0.0, PROP_CENTER_Z)
    pylon = _tilted_cylinder_3d(pylon_base, pylon_top, PYLON_WIDTH / 2.0)

    # engine block (simple box) at the top of the pylon
    engine = (
        cq.Workplane("XY")
        .workplane(offset=PROP_CENTER_Z)
        .center(PROP_CENTER_X - 0.55, 0)
        .box(0.9, 0.6, 0.6, centered=(True, True, False))
    )

    # prop disc, purely for visualization (a thin flat cylinder)
    prop_disc = (
        cq.Workplane("YZ")
        .workplane(offset=PROP_CENTER_X)
        .center(0, PROP_CENTER_Z)
        .circle(PROP_DIA_FT / 2.0)
        .extrude(0.03, both=True)
    )

    # full-perimeter guard ring: annulus (flat ring) facing aft
    ring_outer = PROP_DIA_FT / 2.0 + 0.35
    ring_inner = PROP_DIA_FT / 2.0 + 0.35 - PROP_GUARD_RING_THICKNESS
    guard_ring = (
        cq.Workplane("YZ")
        .workplane(offset=PROP_CENTER_X + 0.05)
        .center(0, PROP_CENTER_Z)
        .circle(ring_outer)
        .circle(ring_inner)
        .extrude(0.10, both=True)
    )
    # a few ring support spokes back to the pylon, purely visual
    spokes = None
    for ang_deg in (0, 90, 180, 270):
        ang = math.radians(ang_deg)
        ring_pt = (
            PROP_CENTER_X + 0.05,
            ring_outer * math.sin(ang),
            PROP_CENTER_Z + ring_outer * math.cos(ang),
        )
        spoke = _tilted_cylinder_3d((PROP_CENTER_X, 0.0, PROP_CENTER_Z), ring_pt, 0.03)
        spokes = spoke if spokes is None else spokes.union(spoke)

    assembly = pylon.union(engine).union(prop_disc).union(guard_ring).union(spokes)
    return assembly, (PROP_CENTER_X, PROP_CENTER_Z)


def build_tail(hull_ref: HullRef) -> cq.Workplane:
    """Slender tail boom from the hull stern to a small conventional tail."""
    boom_start = (hull_ref.stern_x - 0.3, 0.0, hull_ref.spine_z * 0.75)
    boom_end = (OVERALL_LENGTH_FT - 0.9, 0.0, hull_ref.spine_z * 0.95)
    boom = _tilted_cylinder_3d(boom_start, boom_end, BOOM_DIA_FT / 2.0)

    tail_x = OVERALL_LENGTH_FT - STAB_CHORD_FT / 2.0 - 0.4
    tail_z = boom_end[2]

    stab = (
        cq.Workplane("XY")
        .workplane(offset=tail_z)
        .center(tail_x, 0)
        .rect(STAB_CHORD_FT, STAB_SPAN_FT)
        .extrude(0.08, both=True)
    )
    fin = (
        cq.Workplane("XZ")
        .workplane(offset=0)
        .center(tail_x, tail_z)
        .rect(FIN_CHORD_FT, FIN_HEIGHT_FT)
        .extrude(0.07, both=True)
    )
    # nudge fin so its base sits at the boom, growing upward
    fin = fin.translate((0, 0, FIN_HEIGHT_FT / 2.0))

    return boom.union(stab).union(fin)


def build_canards(hull_ref: HullRef) -> cq.Workplane:
    """Two tiny fixed canard fins high on the bow, bar-end-winglet style."""
    half_span = CANARD_COMBINED_SPAN_FT / 2.0
    fins = None
    for side in (-1, 1):
        y0 = side * 0.15
        y1 = side * (0.15 + half_span)
        fin = (
            cq.Workplane("XY")
            .workplane(offset=CANARD_Z)
            .moveTo(CANARD_X - CANARD_CHORD_FT / 2.0, y0)
            .lineTo(CANARD_X + CANARD_CHORD_FT / 2.0, y0)
            .lineTo(CANARD_X + CANARD_CHORD_FT / 2.0, y1)
            .lineTo(CANARD_X - CANARD_CHORD_FT / 2.0, y1)
            .close()
            .extrude(0.03, both=True)
        )
        fins = fin if fins is None else fins.union(fin)
    return fins


def build_sponsons(wing_ref: WingRef) -> cq.Workplane:
    """Small teardrop floats under each wingtip."""
    z = wing_ref.z - SPONSON_DROP_BELOW_WING_FT
    sponsons = None
    for side in (-1, 1):
        y = side * wing_ref.half_span * 0.97
        sponson = (
            cq.Workplane("XY")
            .workplane(offset=z)
            .center(wing_ref.center_x, y)
            .ellipse(SPONSON_LENGTH_FT / 2.0, SPONSON_WIDTH_FT / 2.0)
            .extrude(SPONSON_WIDTH_FT, both=True)
        )
        sponsons = sponson if sponsons is None else sponsons.union(sponson)
    return sponsons


def build_gear_bulges(hull_ref: HullRef) -> cq.Workplane:
    """Trike wheels retracted flush: small bulges on the hull sides plus one
    nosewheel fairing."""
    bulges = None
    for side in (-1, 1):
        y = side * (HULL_MAX_HALF_BEAM + 0.05)
        bulge = (
            cq.Workplane("XY")
            .workplane(offset=hull_ref.spine_z * 0.35)
            .center(GEAR_BULGE_X, y)
            .sphere(GEAR_BULGE_RADIUS)
        )
        bulges = bulge if bulges is None else bulges.union(bulge)

    nose = (
        cq.Workplane("XY")
        .workplane(offset=hull_ref.spine_z * 0.25)
        .center(NOSEWHEEL_FAIRING_X, 0)
        .sphere(NOSEWHEEL_FAIRING_RADIUS)
    )
    return bulges.union(nose)


# --------------------------------------------------------------------------
# Assembly + sanity checks
# --------------------------------------------------------------------------

def build_assembly():
    hull, hull_ref = build_hull()
    rider, rider_head = build_rider(hull_ref)
    wing, wing_ref = build_wing()
    cabane = build_cabane(hull_ref, wing_ref)
    pylon_prop, prop_center = build_pylon_and_prop(hull_ref)
    tail = build_tail(hull_ref)
    canards = build_canards(hull_ref)
    sponsons = build_sponsons(wing_ref)
    gear = build_gear_bulges(hull_ref)

    parts = {
        "hull": (hull, "#c8a165"),
        "rider": (rider, "#333333"),
        "wing": (wing, "#4a7fb5"),
        "cabane": (cabane, "#888888"),
        "pylon_prop": (pylon_prop, "#a53d3d"),
        "tail": (tail, "#4a7fb5"),
        "canards": (canards, "#7fa5c9"),
        "sponsons": (sponsons, "#d9d9d9"),
        "gear": (gear, "#555555"),
    }

    info = dict(
        hull_ref=hull_ref,
        wing_ref=wing_ref,
        rider_head=rider_head,
        prop_center=prop_center,
    )
    return parts, info


def run_sanity_checks(parts, info) -> dict:
    hull_ref: HullRef = info["hull_ref"]
    wing_ref: WingRef = info["wing_ref"]
    rider_head = info["rider_head"]
    prop_center = info["prop_center"]

    # overall bounding box across all parts
    min_x = math.inf
    max_x = -math.inf
    min_y = math.inf
    max_y = -math.inf
    for solid, _color in parts.values():
        bb = solid.val().BoundingBox()
        min_x = min(min_x, bb.xmin)
        max_x = max(max_x, bb.xmax)
        min_y = min(min_y, bb.ymin)
        max_y = max(max_y, bb.ymax)

    overall_length = max_x - min_x
    span = max_y - min_y

    values = dict(
        overall_length_ft=overall_length,
        span_ft=span,
        wing_area_sqft=WING_AREA_SQFT,
        wing_chord_ft=WING_CHORD_FT,
        prop_center_x=prop_center[0],
        wing_te_x=wing_ref.te_x,
        rider_head_x=rider_head[0],
    )

    print("--- sea-ez v0 massing: sanity check values ---")
    for k, v in values.items():
        print(f"  {k}: {v:.3f}")

    assert overall_length <= 19.0, f"overall length {overall_length:.2f} ft exceeds 19 ft cap"
    assert 33.5 <= span <= 34.5, f"span {span:.2f} ft outside 34 +/- 0.5 ft"
    assert prop_center[0] > wing_ref.te_x, (
        f"prop center x={prop_center[0]:.2f} is not aft of wing TE x={wing_ref.te_x:.2f}"
    )
    assert prop_center[0] > rider_head[0], (
        f"prop center x={prop_center[0]:.2f} is not aft of rider head x={rider_head[0]:.2f}"
    )
    print("All sanity checks PASSED.")
    return values


# --------------------------------------------------------------------------
# Export: STL + shaded PNG renders (matplotlib, no OpenGL dependency)
# --------------------------------------------------------------------------

def export_stl(parts, out_path: str) -> None:
    solids = [solid.val() for solid, _color in parts.values()]
    compound = cq.Compound.makeCompound(solids)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    compound.exportStl(out_path)
    print(f"Wrote STL: {out_path}")


def _cq_solid_to_trimesh(solid, color_hex: str, tmp_path: str) -> trimesh.Trimesh:
    solid.val().exportStl(tmp_path, tolerance=0.01, angularTolerance=0.15)
    mesh = trimesh.load(tmp_path, force="mesh")
    rgb = tuple(int(color_hex[i : i + 2], 16) for i in (1, 3, 5)) + (255,)
    mesh.visual.face_colors = rgb
    return mesh


def render_views(parts, out_dir: str, tmp_dir: str) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    os.makedirs(tmp_dir, exist_ok=True)
    meshes = []
    for name, (solid, color) in parts.items():
        tmp_stl = os.path.join(tmp_dir, f"{name}.stl")
        meshes.append(_cq_solid_to_trimesh(solid, color, tmp_stl))

    def render(elev: float, azim: float, out_path: str, title: str, ortho: bool = False) -> None:
        fig = plt.figure(figsize=(10.24, 7.68), dpi=100, facecolor="white")
        ax = fig.add_subplot(111, projection="3d")
        ax.set_facecolor("white")

        light_dir = np.array([-0.4, -0.5, 0.75])
        light_dir = light_dir / np.linalg.norm(light_dir)

        all_pts = []
        for mesh in meshes:
            tris = mesh.triangles
            normals = mesh.face_normals
            base_rgb = np.array(mesh.visual.face_colors[0][:3], dtype=float) / 255.0
            intensity = np.clip(normals @ light_dir, 0.15, 1.0)
            face_colors = np.clip(
                base_rgb[None, :] * (0.35 + 0.65 * intensity[:, None]), 0, 1
            )
            coll = Poly3DCollection(tris, facecolors=face_colors, edgecolor="none", linewidths=0)
            ax.add_collection3d(coll)
            all_pts.append(mesh.vertices)

        pts = np.vstack(all_pts)
        mins = pts.min(axis=0)
        maxs = pts.max(axis=0)
        center = (mins + maxs) / 2.0
        # Per-axis padding (not a shared cube radius) so a long/thin
        # airframe actually fills the frame instead of being dwarfed by
        # whichever single axis (wingspan) happens to be largest.
        extents = np.maximum(maxs - mins, 0.5) * 1.15

        ax.set_xlim(center[0] - extents[0] / 2, center[0] + extents[0] / 2)
        ax.set_ylim(center[1] - extents[1] / 2, center[1] + extents[1] / 2)
        ax.set_zlim(center[2] - extents[2] / 2, center[2] + extents[2] / 2)
        try:
            ax.set_box_aspect(tuple(extents))
        except Exception:
            pass
        ax.view_init(elev=elev, azim=azim)
        if ortho:
            try:
                ax.set_proj_type("ortho")
            except Exception:
                pass
        ax.set_axis_off()
        ax.set_title(title, fontsize=10, color="#333333")
        fig.tight_layout(pad=0.2)
        fig.savefig(out_path, facecolor="white")
        plt.close(fig)
        print(f"Wrote render: {out_path}")

    os.makedirs(out_dir, exist_ok=True)
    side_path = os.path.join(out_dir, "massing-side.png")
    front34_path = os.path.join(out_dir, "massing-front34.png")
    top_path = os.path.join(out_dir, "massing-top.png")

    render(elev=0, azim=-90, out_path=side_path, title="sea-ez v0 massing -- side profile", ortho=True)
    render(elev=18, azim=-125, out_path=front34_path, title="sea-ez v0 massing -- front 3/4", ortho=False)
    render(elev=90, azim=-90, out_path=top_path, title="sea-ez v0 massing -- top view", ortho=True)

    return [side_path, front34_path, top_path]


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base, "out")
    tmp_dir = os.path.join(out_dir, "_parts")

    parts, info = build_assembly()
    sanity_values = run_sanity_checks(parts, info)

    stl_path = os.path.join(out_dir, "massing_v0.stl")
    export_stl(parts, stl_path)

    png_paths = render_views(parts, out_dir, tmp_dir)

    scratchpad = "/private/tmp/claude-501/-Users-ryanstern/e2cfb4b8-b688-4471-b15c-d8ae009828c0/scratchpad"
    if os.path.isdir(scratchpad):
        import shutil

        names = ["massing-side.png", "massing-front34.png", "massing-top.png"]
        for name in names:
            shutil.copy(os.path.join(out_dir, name), os.path.join(scratchpad, name))
        print(f"Copied PNGs to scratchpad: {scratchpad}")

    print("\nDone. Sanity values:", sanity_values)
