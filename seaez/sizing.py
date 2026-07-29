"""Wing sizing math (spec §2-§3).

Design-consistency checks on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice). CLmax is an assumed target until
an airfoil is chosen and verified (donor memo §2: no candidate's airfoil is
manufacturer-confirmed).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

RHO_SL_SLUG_FT3 = 0.0023769   # sea-level standard air density
FPS_PER_KT = 1.68781


def stall_speed_kt(gross_lb: float, wing_area_sqft: float, cl_max: float) -> float:
    """1-g power-off stall: Vs = sqrt(2W / (rho * S * CLmax)), lb/ft/slug units."""
    v_fps = math.sqrt(2.0 * gross_lb / (RHO_SL_SLUG_FT3 * wing_area_sqft * cl_max))
    return v_fps / FPS_PER_KT


def wing_area_for_stall(gross_lb: float, stall_kt: float, cl_max: float) -> float:
    v_fps = stall_kt * FPS_PER_KT
    return 2.0 * gross_lb / (RHO_SL_SLUG_FT3 * cl_max * v_fps**2)


@dataclass(frozen=True)
class Planform:
    root_chord_ft: float
    tip_chord_ft: float
    mac_ft: float
    mac_le_x_ft: float


def planform(area_sqft: float, span_ft: float, taper_ratio: float, center_x_ft: float) -> Planform:
    """Straight-tapered unswept wing with every chord centered on center_x_ft
    (matches design/massing_v0.py). MAC leading edge sits half a MAC forward
    of the chord centerline."""
    root = 2.0 * area_sqft / (span_ft * (1.0 + taper_ratio))
    tip = root * taper_ratio
    mac = (2.0 / 3.0) * root * (1.0 + taper_ratio + taper_ratio**2) / (1.0 + taper_ratio)
    return Planform(
        root_chord_ft=root,
        tip_chord_ft=tip,
        mac_ft=mac,
        mac_le_x_ft=center_x_ft - mac / 2.0,
    )


def horizontal_tail_volume(stab_area_sqft: float, tail_arm_ft: float,
                           wing_area_sqft: float, mac_ft: float) -> float:
    """V_h = S_h * l_h / (S * MAC). Arm is tail AC to gross CG, bow datum."""
    return stab_area_sqft * tail_arm_ft / (wing_area_sqft * mac_ft)


def vertical_tail_volume(fin_area_sqft: float, tail_arm_ft: float,
                         wing_area_sqft: float, span_ft: float) -> float:
    """V_v = S_v * l_v / (S * b). Arm is tail AC to gross CG, bow datum."""
    return fin_area_sqft * tail_arm_ft / (wing_area_sqft * span_ft)
