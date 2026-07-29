"""Static hydrostatics from the parametric hull mesh (spec §8 CI gates).

Design-consistency checks on targets — NOT validated engineering, NOT
naval-architecture proof, and no substitute for the flotation and taxi
test campaign (spec §9). Consumes a trimesh; never imports cadquery.
"""
from __future__ import annotations

import math

import trimesh

WATER_LB_FT3 = 62.4


def _submerged(mesh: trimesh.Trimesh, waterline_z: float) -> trimesh.Trimesh | None:
    """The part of the mesh below waterline_z, capped watertight."""
    cut = trimesh.intersections.slice_mesh_plane(
        mesh, plane_normal=(0.0, 0.0, -1.0), plane_origin=(0.0, 0.0, waterline_z),
        cap=True,
    )
    if cut is None or cut.is_empty:
        return None
    return cut


def displaced_volume_ft3(mesh: trimesh.Trimesh, waterline_z: float) -> float:
    sub = _submerged(mesh, waterline_z)
    return 0.0 if sub is None else float(sub.volume)


def solve_waterline(mesh: trimesh.Trimesh, gross_lb: float, tol_lb: float = 0.1) -> float:
    """Bisect the waterline z where displacement supports gross_lb."""
    target_ft3 = gross_lb / WATER_LB_FT3
    lo, hi = float(mesh.bounds[0][2]), float(mesh.bounds[1][2])
    if float(mesh.volume) * WATER_LB_FT3 < gross_lb:
        raise ValueError("hull envelope cannot displace gross weight — it sinks")
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if displaced_volume_ft3(mesh, mid) < target_ft3:
            lo = mid
        else:
            hi = mid
        if (hi - lo) * WATER_LB_FT3 < tol_lb:
            break
    return (lo + hi) / 2.0


def freeboard_at_step_ft(p, mesh: trimesh.Trimesh, waterline_z: float) -> float:
    """Deck height minus waterline at the step station (min freeboard region)."""
    step_x = p.hull_step_fraction * p.hull_length_ft
    section = mesh.section(plane_origin=(step_x, 0.0, 0.0), plane_normal=(1.0, 0.0, 0.0))
    if section is None:
        raise ValueError("no hull section at the step station")
    deck_z = float(section.vertices[:, 2].max())
    return deck_z - waterline_z


def foam_reserve_ok(mesh: trimesh.Trimesh, gross_lb: float, factor: float = 1.5,
                    packing_headroom: float = 2.0) -> bool:
    """Spec §6: foam buoyancy > factor x gross. Sealed bays won't fill the
    envelope, so require the envelope to hold packing_headroom x that volume."""
    required_ft3 = factor * gross_lb / WATER_LB_FT3
    return float(mesh.volume) >= packing_headroom * required_ft3


def waterplane_ixx_ft4(mesh: trimesh.Trimesh, waterline_z: float) -> float:
    """Second moment of the waterplane area about the fore-aft centerline
    (y=0), via Green's theorem over the waterplane outline polygons."""
    section = mesh.section(plane_origin=(0.0, 0.0, waterline_z), plane_normal=(0.0, 0.0, 1.0))
    if section is None:
        return 0.0
    planar, _tf = section.to_2D()
    ixx = 0.0
    for poly in planar.polygons_full:
        # to_planar maps mesh (x, y) -> polygon (x, y); centerline symmetry
        # puts the centroid on y~0, so moments are about the centerline.
        xs, ys = poly.exterior.coords.xy
        for i in range(len(xs) - 1):
            cross = xs[i] * ys[i + 1] - xs[i + 1] * ys[i]
            ixx += cross * (ys[i] ** 2 + ys[i] * ys[i + 1] + ys[i + 1] ** 2)
    return abs(ixx) / 12.0


def metacentric_height_ft(mesh: trimesh.Trimesh, waterline_z: float, kg_ft: float) -> float:
    """GM = KB + BM - KG, all heights in the mesh's own z datum.
    Negative GM means the bare hull is initially unstable — expected for a
    narrow motorcycle hull; roll stability comes from the sponsons (spec §4).
    Datum note: kg_ft is expected in the mesh's own z datum, which may differ
    from the ledger's keel-baseline datum by the mesh's bounds[0][2] offset;
    at estimate grade this discrepancy (< 0.25 ft) is inside the noise."""
    sub = _submerged(mesh, waterline_z)
    if sub is None or sub.volume <= 0:
        raise ValueError("no displaced volume at this waterline")
    kb = float(sub.center_mass[2])
    bm = waterplane_ixx_ft4(mesh, waterline_z) / float(sub.volume)
    return kb + bm - kg_ft


def sponson_touch_deg(p, waterline_above_keel_ft: float) -> float:
    """Heel angle at which the wingtip sponson bottom reaches the water.
    Small-angle rigid roll about the waterline centerline.
    Datum note: waterline_above_keel_ft is the waterline height above the
    keel baseline (the same datum as p.wing_z_ft) — NOT the mesh's own z
    datum, which is offset from the keel baseline by the mesh's bounds[0][2]."""
    y = p.sponson_half_span_frac * p.wing_span_ft / 2.0
    sponson_bottom_z = p.wing_z_ft - p.sponson_bottom_below_wing_ft
    height_above_wl = sponson_bottom_z - waterline_above_keel_ft
    if height_above_wl <= 0:
        return 0.0
    return math.degrees(math.atan2(height_above_wl, y))
