"""Road-mode (folded, pedaling) stability checks (spec §4 mode matrix).

Design-consistency checks on targets — NOT validated engineering (spec
safety notice). Static rigid-body tipover only; no dynamic/gust cases.
"""
from __future__ import annotations

import dataclasses

from seaez.ledger import Part, cg
from seaez.params import DesignParams


def road_cg(parts: list[Part], p: DesignParams) -> tuple[float, float, float]:
    """CG in road config: wing folded to its stowed height, rider upright,
    full fuel. Returns (total_lb, cg_x_ft, cg_z_ft)."""
    adjusted = [
        dataclasses.replace(part, z_ft=p.folded_wing_z_ft)
        if part.name == "wing_assembly" else part
        for part in parts
    ]
    extras = [
        (p.pilot_lb, p.seat_x_ft, p.seat_z_road_ft),
        (p.fuel_lb, p.fuel_x_ft, p.fuel_z_ft),
    ]
    return cg(adjusted, extra_masses=extras)


def tipover_ratio(cg_z_ft: float, track_width_ft: float) -> float:
    """Lateral acceleration (in g) at which the trike lifts an inside wheel:
    half-track over CG height. Static rigid-body estimate."""
    return (track_width_ft / 2.0) / cg_z_ft
