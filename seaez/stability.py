"""Analytic longitudinal stability and control-authority estimates (spec §8).

Design-consistency checks on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice). The constants below are classic
first-pass assumptions for a strut-braced high-wing with an aft tail; they
are TARGETS, replaced by OpenVSP analysis in Phase 2.3. All stability gates
are for the NO-FOREPLANE configuration (v1 first flights, spec §4).

V_v is the least trustworthy analytic gate here: the model ignores the
destabilizing forward hull side area (large on a flying boat) and reuses
the stab AC station as the fin arm — highest priority for OpenVSP
replacement in 2.3.
"""
from __future__ import annotations

from seaez.sizing import FPS_PER_KT, RHO_SL_SLUG_FT3

# Assumption constants (first-pass classic values; OpenVSP supersedes in 2.3):
TAIL_EFFICIENCY = 0.90        # eta_h: dynamic-pressure ratio at the tail
TAIL_LIFT_SLOPE_RATIO = 0.85  # a_t / a_w: tail vs wing lift-curve slope
DOWNWASH_DERIV = 0.35         # d(epsilon)/d(alpha) behind the wing
WING_AC_FRAC = 0.25           # wing aerodynamic center, fraction of MAC


def neutral_point_frac(vh: float) -> float:
    """Stick-fixed neutral point as a fraction of MAC:
    NP = x_ac + eta_h * (a_t/a_w) * (1 - de/da) * V_h."""
    return WING_AC_FRAC + TAIL_EFFICIENCY * TAIL_LIFT_SLOPE_RATIO * (1.0 - DOWNWASH_DERIV) * vh


def static_margin_frac(cg_frac_mac: float, vh: float) -> float:
    """SM = NP - CG, both as fractions of MAC. Positive = stable."""
    return neutral_point_frac(vh) - cg_frac_mac


CL_TAIL_MAX = 0.9             # elevator-equipped tail max CL, conservative target
ROTATION_SPEED_FACTOR = 1.2   # rotation at 1.2 Vs


def thrust_pitch_moment_lbft(thrust_lb: float, thrust_line_z_ft: float, cg_z_ft: float) -> float:
    """Nose-down pitch couple from a thrust line above the CG (both z in the
    keel-baseline datum). Static thrust is the conservative worst case —
    prop thrust decays with airspeed."""
    return thrust_lb * (thrust_line_z_ft - cg_z_ft)


def tail_authority_moment_lbft(speed_kt: float, stab_area_sqft: float, tail_arm_ft: float) -> float:
    """Max tail pitch moment: q * S_h * CL_tail_max * eta_h * l_h."""
    v_fps = speed_kt * FPS_PER_KT
    q = 0.5 * RHO_SL_SLUG_FT3 * v_fps**2
    return q * stab_area_sqft * CL_TAIL_MAX * TAIL_EFFICIENCY * tail_arm_ft


def thrust_couple_ratio(thrust_lb: float, thrust_line_z_ft: float, cg_z_ft: float,
                        speed_kt: float, stab_area_sqft: float, tail_arm_ft: float) -> float:
    """Tail authority over thrust couple; >= 1 means the tail wins."""
    couple = thrust_pitch_moment_lbft(thrust_lb, thrust_line_z_ft, cg_z_ft)
    authority = tail_authority_moment_lbft(speed_kt, stab_area_sqft, tail_arm_ft)
    return authority / couple
