"""Computes the two pre-hardware gating numbers from the 2026-09-05 research
brief (docs/research/2026-09-05-sea-ez-propulsion-part103-envelope.md, §4):

  1. Stall speed at gross weight + build-weight creep (5/10/15%).
  2. Pre-planing hump-drag thrust required vs. the named engine class's
     thrust curve (Moster/Polini 28-35 hp).

Uses the repo's own toolchain (seaez.sizing, seaez.ledger, seaez.aerodata,
the new seaez.planing) -- no new physics engine, one new first-order module.
Design-consistency numbers on TARGETS, not validated engineering (spec
safety notice, same as every other module in this repo).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from seaez.aerodata import CLMAX_3D_FACTOR, load_airfoil
from seaez.ledger import cg, chute_lb, load_parts, rollup_empty_lb
from seaez.params import DEFAULT
from seaez.planing import hump_point, thrust_at_speed_lb
from seaez.sizing import planform, stall_speed_kt, wing_area_for_stall

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"

# Engine class the spec names (research brief §3 Option 1 / §5): 28-35 hp
# paramotor-class 2-stroke pusher units. Grounded to published static-thrust
# figures for the two named brands (2026-09-05 web lookups):
#   Vittorazi Moster 185 (~28 hp): 75 kgf (165 lbf) static w/ 125 cm prop,
#     up to 90+ kgf (198+ lbf) w/ 140 cm prop.  vittorazi.com/en/motori/moster-185/
#   Polini Thor 202/250/303 (~30-40 hp class): 90-120 kgf (198-265 lbf)
#     static w/ 130-160 cm props.  polinithor.com product pages
# params.py's static_thrust_lb=165.0 already documents the Moster-185/125cm
# figure -- used here as the LOW end of the named class; 250 lbf is used as
# the HIGH end (Polini Thor mid-range, rounded down from the 265 lbf
# Thor-303-class ceiling to stay inside "28-35 hp", since the 303 pushes
# closer to 40 hp).
ENGINE_CLASS_LOW_STATIC_LB = DEFAULT.static_thrust_lb   # 165 lbf, Moster 185 / 125cm
ENGINE_CLASS_HIGH_STATIC_LB = 250.0                     # Polini Thor 202/250 class, 130cm
PROP_DIAMETER_LOW_FT = 125.0 / 100.0 * 3.28084          # 125 cm
PROP_DIAMETER_HIGH_FT = 130.0 / 100.0 * 3.28084         # 130 cm


def gross_at_creep(creep_frac: float) -> float:
    """Apply build-weight creep to the STRUCTURE only (empty weight minus
    chute -- the composite/machined parts that actually run heavy off CAD),
    not to the chute (purchased, fixed spec) or pilot/fuel (not a build
    item). README/CLAUDE.md flag 5-10% heavy vs CAD as the real-world risk;
    this brief asks for 5/10/15% to see where the ceiling breaks."""
    parts = load_parts(PARTS)
    empty = rollup_empty_lb(parts)
    chute = chute_lb(parts)
    return empty * (1.0 + creep_frac) + chute + DEFAULT.pilot_lb + DEFAULT.fuel_lb


def landing_clmax_3d() -> float:
    af = load_airfoil()
    return (af.clmax_2d + DEFAULT.flap_dclmax_2d) * CLMAX_3D_FACTOR


def stall_creep_table() -> list[tuple[float, float, float]]:
    """[(creep_frac, gross_lb, stall_kt), ...] at the repo's own computed
    landing CLmax (aerodata-grounded, not the hand-set params.cl_max)."""
    clmax = landing_clmax_3d()
    out = []
    for creep in (0.0, 0.05, 0.10, 0.15):
        gross = gross_at_creep(creep)
        vs = stall_speed_kt(gross, DEFAULT.wing_area_sqft, clmax)
        out.append((creep, gross, vs))
    return out


def creep_that_busts_ceiling(ceiling_kt: float = 24.0) -> float:
    """Bisect the structure creep fraction at which computed stall first
    exceeds ceiling_kt, holding wing area and CLmax fixed."""
    clmax = landing_clmax_3d()
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        vs = stall_speed_kt(gross_at_creep(mid), DEFAULT.wing_area_sqft, clmax)
        if vs > ceiling_kt:
            hi = mid
        else:
            lo = mid
    return lo


def wing_area_needed_at_creep(creep_frac: float, ceiling_kt: float = 24.0) -> float:
    clmax = landing_clmax_3d()
    return wing_area_for_stall(gross_at_creep(creep_frac), ceiling_kt, clmax)


def clmax_needed_at_creep(creep_frac: float, ceiling_kt: float = 24.0) -> float:
    """CLmax that would hold the CURRENT wing area to the ceiling at this
    creep level: Vs = sqrt(2W/(rho*S*CLmax)) => CLmax = 2W/(rho*S*(V*fps)^2)."""
    from seaez.sizing import FPS_PER_KT, RHO_SL_SLUG_FT3
    gross = gross_at_creep(creep_frac)
    v_fps = ceiling_kt * FPS_PER_KT
    return 2.0 * gross / (RHO_SL_SLUG_FT3 * DEFAULT.wing_area_sqft * v_fps**2)


def hump_drag_report() -> dict:
    gross = gross_at_creep(0.0)  # nominal design gross, no creep (spec design point)
    hump = hump_point(weight_lb=gross, beam_ft=DEFAULT.hull_beam_ft)
    t_low = thrust_at_speed_lb(ENGINE_CLASS_LOW_STATIC_LB, PROP_DIAMETER_LOW_FT, hump.speed_kt)
    t_high = thrust_at_speed_lb(ENGINE_CLASS_HIGH_STATIC_LB, PROP_DIAMETER_HIGH_FT, hump.speed_kt)
    return {
        "gross_lb": gross,
        "hump_speed_kt": hump.speed_kt,
        "hump_resistance_lb": hump.resistance_lb,
        "thrust_avail_low_lb": t_low,
        "thrust_avail_high_lb": t_high,
        "margin_low": t_low - hump.resistance_lb,
        "margin_high": t_high - hump.resistance_lb,
    }


def main() -> None:
    print("=== Gating number 1: stall speed vs. build-weight creep ===")
    print(f"CLmax used (repo's own XFOIL-grounded landing value): {landing_clmax_3d():.3f}")
    for creep, gross, vs in stall_creep_table():
        flag = "  <-- BUSTS 24 kt" if vs > 24.0 else ""
        print(f"  creep {creep:>5.0%}   gross {gross:6.1f} lb   Vs {vs:5.2f} kt{flag}")
    bust = creep_that_busts_ceiling()
    print(f"\n  Ceiling (24.0 kt) is first exceeded at structure creep = {bust:.1%}")
    s_needed = wing_area_needed_at_creep(0.15)
    c_needed = clmax_needed_at_creep(0.15)
    print(f"  To hold 24 kt at +15% creep: wing area >= {s_needed:.1f} sq ft "
          f"(currently {DEFAULT.wing_area_sqft:.0f}, +{s_needed - DEFAULT.wing_area_sqft:.1f} sq ft)"
          f"  OR  CLmax >= {c_needed:.3f} (currently {landing_clmax_3d():.3f}, "
          f"+{c_needed - landing_clmax_3d():.3f})")

    print("\n=== Gating number 2: pre-planing hump-drag thrust required ===")
    r = hump_drag_report()
    print(f"  Design gross (no creep): {r['gross_lb']:.1f} lb, hull beam {DEFAULT.hull_beam_ft:.2f} ft")
    print(f"  Hump speed: {r['hump_speed_kt']:.1f} kt   Thrust required at hump: {r['hump_resistance_lb']:.1f} lbf")
    print(f"  Thrust available (Moster 185 / 125cm class, actuator-disk lapse): "
          f"{r['thrust_avail_low_lb']:.1f} lbf   margin {r['margin_low']:+.1f} lbf")
    print(f"  Thrust available (Polini Thor / 130cm class, actuator-disk lapse): "
          f"{r['thrust_avail_high_lb']:.1f} lbf   margin {r['margin_high']:+.1f} lbf")


if __name__ == "__main__":
    main()
