"""Wing sizing math (spec §2-§3).

Design-consistency checks on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice). CLmax is an assumed target until
an airfoil is chosen and verified (donor memo §2: no candidate's airfoil is
manufacturer-confirmed).
"""
from __future__ import annotations

import math

RHO_SL_SLUG_FT3 = 0.0023769   # sea-level standard air density
FPS_PER_KT = 1.68781


def stall_speed_kt(gross_lb: float, wing_area_sqft: float, cl_max: float) -> float:
    """1-g power-off stall: Vs = sqrt(2W / (rho * S * CLmax)), lb/ft/slug units."""
    v_fps = math.sqrt(2.0 * gross_lb / (RHO_SL_SLUG_FT3 * wing_area_sqft * cl_max))
    return v_fps / FPS_PER_KT


def wing_area_for_stall(gross_lb: float, stall_kt: float, cl_max: float) -> float:
    v_fps = stall_kt * FPS_PER_KT
    return 2.0 * gross_lb / (RHO_SL_SLUG_FT3 * cl_max * v_fps**2)
