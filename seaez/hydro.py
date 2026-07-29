"""Static hydrostatics from the parametric hull mesh (spec §8 CI gates).

Design-consistency checks on targets — NOT validated engineering, NOT
naval-architecture proof, and no substitute for the flotation and taxi
test campaign (spec §9). Consumes a trimesh; never imports cadquery.
"""
from __future__ import annotations

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
