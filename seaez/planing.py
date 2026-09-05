"""First-order pre-planing "hump" resistance estimate (Savitsky 1964 method).

Design-consistency / order-of-magnitude tooling on a TARGET gross weight —
NOT validated engineering, NOT a towing-tank result, and NOT airworthiness
proof (spec safety notice). Written for the 2026-09-05 gating-numbers
request because no hull hump-drag model existed in the repo before this.

KNOWN LIMITATION, stated up front: Savitsky's planing equations assume a
prismatic hard-chine V-bottom hull at constant deadrise. sea-ez's hull
(`design/geometry.py`) is an elliptical-section flying-boat hull, not a
V-bottom — there is no chine and no single deadrise angle to measure off
the geometry. This module treats deadrise and hump trim angle as literature
-typical ASSUMED CONSTANTS (documented below), not values derived from the
mesh. Treat the output as an order-of-magnitude bound, not a hull-specific
prediction — a real hump-drag number needs a towing-tank test or a proper
CFD/VPP run against the actual hull shape.

Assumptions (flagged, not fit to this hull):
- Effective deadrise beta_deg = 12.0 -- mid of the 8-15 deg range typical of
  light round-bilge/warped-bottom hulls (Savitsky & Ross 1952 Series 62
  covers 0-30 deg hard-chine; round-bilge hulls plane less cleanly than a
  hard chine at any given deadrise, so this is optimistic, not conservative).
- Hump trim angle tau_deg = 4.0 -- Savitsky (1964) and later planing-hull
  literature (e.g. Blount & Fox 1976) consistently place the resistance hump
  trim in the 3-5 deg band for unassisted (no trim-tab) small craft; full
  Savitsky method solves trim from a moment balance against LCG-to-step
  distance, which the repo does not model (no spar/step moment-arm data),
  so a fixed literature value is used instead of a solved equilibrium trim.
- Fresh water: rho = 1.9394 slug/ft^3, kinematic viscosity nu = 1.2791e-5
  ft^2/s @ 59 F (ITTC standard reference temperature).
- Excludes aerodynamic drag of the airframe/wing during the water run and
  any appendage (rudder, sponson) drag -- both first-order omissions on top
  of the hull-shape mismatch above.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

WATER_RHO_SLUG_FT3 = 1.9394       # 62.4 lb/ft^3 / 32.174 ft/s^2, fresh water
WATER_NU_FT2_S = 1.2791e-5        # ITTC-57 reference, fresh water @ 59 F
G_FT_S2 = 32.174
FT_PER_KT = 1.68781

DEFAULT_DEADRISE_DEG = 12.0
DEFAULT_HUMP_TRIM_DEG = 4.0
ROUGHNESS_ALLOWANCE_CF = 0.0004   # Savitsky's standard planing-hull add-on


@dataclass(frozen=True)
class PlaningPoint:
    speed_kt: float
    lambda_wl_b: float           # mean wetted-length / beam
    resistance_lb: float


def _clb_required(weight_lb: float, speed_fps: float, beam_ft: float) -> float:
    return weight_lb / (0.5 * WATER_RHO_SLUG_FT3 * speed_fps**2 * beam_ft**2)


def _clb_of_lambda(lam: float, tau_deg: float, beta_deg: float, cv: float) -> float:
    cl0 = tau_deg**1.1 * (0.012 * lam**0.5 + 0.0055 * lam**2.5 / cv**2)
    return cl0 - 0.0065 * beta_deg * cl0**0.60


def _solve_lambda(weight_lb: float, speed_fps: float, beam_ft: float,
                   tau_deg: float, beta_deg: float) -> float:
    """Bisect the mean wetted-length/beam ratio (Savitsky lift-coefficient
    equation) that supports weight_lb at speed_fps. Returns lambda in
    (0, 20] -- if the target CLb exceeds what lambda=20 can produce, the
    hull is still fully displacement-borne at this speed (pre-hump)."""
    cv = speed_fps / math.sqrt(G_FT_S2 * beam_ft)
    target = _clb_required(weight_lb, speed_fps, beam_ft)
    lo, hi = 1e-3, 20.0
    if _clb_of_lambda(hi, tau_deg, beta_deg, cv) < target:
        return hi  # still displacement-borne; caller should treat as "off scale"
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if _clb_of_lambda(mid, tau_deg, beta_deg, cv) > target:
            hi = mid   # CLb(lambda) is increasing -- root is below an overshoot
        else:
            lo = mid
    return (lo + hi) / 2.0


def savitsky_resistance_lb(weight_lb: float, beam_ft: float, speed_kt: float,
                           tau_deg: float = DEFAULT_HUMP_TRIM_DEG,
                           beta_deg: float = DEFAULT_DEADRISE_DEG) -> PlaningPoint:
    """Total (pressure + friction) planing resistance at one speed, Savitsky
    (1964) formulation. See module docstring for the assumptions this rests
    on -- this is a first-order estimate, not a hull-specific prediction."""
    v_fps = speed_kt * FT_PER_KT
    lam = _solve_lambda(weight_lb, v_fps, beam_ft, tau_deg, beta_deg)
    lm_ft = lam * beam_ft
    re = v_fps * lm_ft / WATER_NU_FT2_S
    cf = 0.075 / (math.log10(max(re, 10.0)) - 2.0) ** 2 + ROUGHNESS_ALLOWANCE_CF
    beta_rad = math.radians(beta_deg)
    tau_rad = math.radians(tau_deg)
    friction_lb = (0.5 * WATER_RHO_SLUG_FT3 * v_fps**2 * lam * beam_ft**2 * cf) / math.cos(beta_rad)
    total_lb = weight_lb * math.tan(tau_rad) + friction_lb / math.cos(tau_rad)
    return PlaningPoint(speed_kt=speed_kt, lambda_wl_b=lam, resistance_lb=total_lb)


def hump_sweep(weight_lb: float, beam_ft: float, speed_range_kt: tuple[float, float] = (2.0, 40.0),
               step_kt: float = 0.25, tau_deg: float = DEFAULT_HUMP_TRIM_DEG,
               beta_deg: float = DEFAULT_DEADRISE_DEG) -> list[PlaningPoint]:
    """Resistance curve from low speed through the pre-planing hump. The
    peak of this curve (max(resistance_lb)) is the hump-drag thrust
    requirement -- report it, don't just read off the endpoint."""
    n = int(round((speed_range_kt[1] - speed_range_kt[0]) / step_kt)) + 1
    return [
        savitsky_resistance_lb(weight_lb, beam_ft, speed_range_kt[0] + i * step_kt,
                                tau_deg=tau_deg, beta_deg=beta_deg)
        for i in range(n)
    ]


def hump_point(weight_lb: float, beam_ft: float, **kwargs) -> PlaningPoint:
    """The single peak-resistance point on the sweep -- the hump."""
    pts = hump_sweep(weight_lb, beam_ft, **kwargs)
    return max(pts, key=lambda p: p.resistance_lb)


# --- Propeller thrust lapse (actuator-disk momentum theory, constant-power
# assumption: same shaft power delivered to the disk at the hump speed as at
# static). Standard textbook method (e.g. Gudmundsson, "General Aviation
# Aircraft Design", ch. 15) for converting a static thrust rating to thrust
# at forward speed for a fixed-pitch prop -- NOT a vendor-measured curve. ---

AIR_RHO_SLUG_FT3 = 0.0023769


def thrust_at_speed_lb(static_thrust_lb: float, prop_diameter_ft: float,
                       speed_kt: float, rho: float = AIR_RHO_SLUG_FT3) -> float:
    """Thrust available at forward speed, holding shaft power (into the
    slipstream) constant at its static value -- actuator disk theory."""
    area_ft2 = math.pi * (prop_diameter_ft / 2.0) ** 2
    v_i0 = math.sqrt(static_thrust_lb / (2.0 * rho * area_ft2))
    power = static_thrust_lb * v_i0  # P = T * v_i at V=0
    v_fps = speed_kt * FT_PER_KT
    v_i = v_i0
    for _ in range(200):
        thrust = power / (v_fps + v_i)
        v_i_new = thrust / (2.0 * rho * area_ft2 * (v_fps + v_i))
        v_i = 0.5 * v_i + 0.5 * v_i_new
    return power / (v_fps + v_i)
