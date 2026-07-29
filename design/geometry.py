"""Parametric hull geometry (engineering-input grade, spec §8).

Station shape is normalized from design/massing_v0.py's hand-tuned loft so
hydrostatics run against the same hull the massing renders show. Values are
design targets — NOT validated engineering (spec safety notice).
"""
from __future__ import annotations

import os
import tempfile

import cadquery as cq
import trimesh

from seaez.params import DesignParams

# (x_frac of length, half_beam_frac of beam/2, height_frac of depth, center_z_frac of depth)
# Normalized from massing_v0.build_hull()'s stations; the two step rows are
# injected at step_fraction +/- 0.0125 at build time.
_STATIONS = [
    (0.000, 0.024, 0.022, 0.60),
    (0.075, 0.440, 0.407, 0.70),
    (0.217, 0.760, 0.704, 0.85),
    (0.367, 1.000, 0.778, 0.95),
    ("step_fwd", 1.000, 0.778, 0.95),
    ("step_aft", 0.920, 0.630, 0.82),
    (0.800, 0.600, 0.504, 0.78),
    (1.000, 0.096, 0.222, 0.55),
]


def hull_stations(p: DesignParams) -> list[tuple[float, float, float, float]]:
    """Absolute (x, half_beam, height, center_z) in feet."""
    out = []
    for x_frac, hb_frac, h_frac, cz_frac in _STATIONS:
        if x_frac == "step_fwd":
            x_frac = p.hull_step_fraction - 0.0125
        elif x_frac == "step_aft":
            x_frac = p.hull_step_fraction + 0.0125
        out.append((
            x_frac * p.hull_length_ft,
            max(hb_frac * p.hull_beam_ft / 2.0, 0.02),
            max(h_frac * p.hull_depth_ft, 0.02),
            cz_frac * p.hull_depth_ft,
        ))
    return out


def build_hull_solid(p: DesignParams) -> cq.Workplane:
    stations = hull_stations(p)
    # NOTE: workplane(offset=...) and center(...) are DELTAS from the previous
    # station, not absolute coordinates — same gotcha as massing_v0.build_hull.
    wp = cq.Workplane("YZ")
    first_x, hb, h, cz = stations[0]
    wp = wp.workplane(offset=first_x).center(0, cz).ellipse(hb, h)
    prev_x, prev_cz = first_x, cz
    for x, hb, h, cz in stations[1:]:
        wp = wp.workplane(offset=x - prev_x).center(0, cz - prev_cz).ellipse(hb, h)
        prev_x, prev_cz = x, cz
    return wp.loft(ruled=True)


def hull_mesh(p: DesignParams) -> trimesh.Trimesh:
    solid = build_hull_solid(p)
    with tempfile.TemporaryDirectory() as tmp:
        stl = os.path.join(tmp, "hull.stl")
        solid.val().exportStl(stl, tolerance=0.005, angularTolerance=0.1)
        mesh = trimesh.load(stl, force="mesh")
    if not mesh.is_watertight:
        trimesh.repair.fill_holes(mesh)
    return mesh
