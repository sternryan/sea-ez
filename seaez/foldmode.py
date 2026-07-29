"""Folded (road-mode) envelope estimate (spec §4 Kolb-style aft-fold).

Design-consistency checks on targets — NOT validated engineering (spec
safety notice). Rigid planar fold model: panels pivot aft about the
rear-spar attach, leading edges outboard, resting alongside the tail boom.
Real fold kinematics (swing path, cradle geometry, interference) are a
Phase 2.3 task on the purchased donor fold drawings.
"""
from __future__ import annotations

from dataclasses import dataclass

from seaez.params import DesignParams
from seaez.sizing import planform


@dataclass(frozen=True)
class FoldedEnvelope:
    width_ft: float
    length_ft: float
    tip_x_ft: float


def folded_envelope(p: DesignParams) -> FoldedEnvelope:
    """Folded width: hull beam + per-side stowed panel depth (root-chord
    thickness + clearance). Folded length: panels swing aft from the pivot,
    so the tip reaches pivot_x + (half-span - root offset); envelope length
    is that or the airframe length, whichever governs."""
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    panel_reach = p.wing_span_ft / 2.0 - p.fold_root_y_ft
    tip_x = p.fold_pivot_x_ft + panel_reach

    # 0.12 thickness fraction matches massing_v0 / the Phase 2.1 wing model.
    stowed_depth = 0.12 * pf.root_chord_ft + p.fold_clearance_ft
    width = p.hull_beam_ft + 2.0 * stowed_depth

    return FoldedEnvelope(
        width_ft=width,
        length_ft=max(tip_x, p.overall_length_ft),
        tip_x_ft=tip_x,
    )
