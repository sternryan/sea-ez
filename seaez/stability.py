"""Analytic longitudinal stability and control-authority estimates (spec §8).

Design-consistency checks on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice). The constants below are classic
first-pass assumptions for a strut-braced high-wing with an aft tail; they
are TARGETS, replaced by OpenVSP analysis in Phase 2.3. All stability gates
are for the NO-FOREPLANE configuration (v1 first flights, spec §4).
"""
from __future__ import annotations

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
