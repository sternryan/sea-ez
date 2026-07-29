"""One-screen design margin report across every Phase 2.1 gate.

Values are design targets under consistency checks — NOT validated
engineering (spec safety notice)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from seaez.foldmode import folded_envelope
from seaez.hydro import (
    freeboard_at_step_ft, metacentric_height_ft, solve_waterline,
    sponson_touch_deg, WATER_LB_FT3,
)
from seaez.ledger import cg, chute_lb, load_parts, rollup_empty_lb, EMPTY_WEIGHT_LIMIT_LB
from seaez.params import DEFAULT
from seaez.aerodata import load_airfoil, load_vspaero
from seaez.roadmode import road_cg, tipover_ratio
from seaez.sizing import horizontal_tail_volume, planform, stall_speed_kt, vertical_tail_volume
from seaez.stability import ROTATION_SPEED_FACTOR, static_margin_frac, thrust_couple_ratio

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def main() -> None:
    p = DEFAULT
    parts = load_parts(PARTS)
    empty = rollup_empty_lb(parts)
    extras = [
        (p.pilot_lb, p.seat_x_ft, p.seat_z_flight_ft),
        (p.fuel_lb, p.fuel_x_ft, p.fuel_z_ft),
    ]
    gross, cg_x, cg_z = cg(parts, extra_masses=extras)
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    mac_frac = (cg_x - pf.mac_le_x_ft) / pf.mac_ft
    vs = stall_speed_kt(gross, p.wing_area_sqft, p.cl_max)
    _rt, _rx, road_z = road_cg(parts, p)

    tail_arm = p.tail_ac_x_ft - cg_x
    vh = horizontal_tail_volume(p.stab_area_sqft, tail_arm, p.wing_area_sqft, pf.mac_ft)
    vv = vertical_tail_volume(p.fin_area_sqft, tail_arm, p.wing_area_sqft, p.wing_span_ft)
    sm = static_margin_frac(mac_frac, vh)
    tc = thrust_couple_ratio(
        thrust_lb=p.static_thrust_lb, thrust_line_z_ft=p.thrust_line_z_ft, cg_z_ft=cg_z,
        speed_kt=ROTATION_SPEED_FACTOR * vs, stab_area_sqft=p.stab_area_sqft, tail_arm_ft=tail_arm,
    )
    env = folded_envelope(p)

    from design.geometry import hull_mesh
    hull = hull_mesh(p)
    wl = solve_waterline(hull, gross)
    draft = wl - hull.bounds[0][2]

    rows = [
        ("empty weight (lb)", f"{empty:.1f}", f"<= {EMPTY_WEIGHT_LIMIT_LB:.0f}"),
        ("chute (lb)", f"{chute_lb(parts):.1f}", "<= 24"),
        ("gross w/ pilot+fuel (lb)", f"{gross:.1f}", "470-500"),
        ("stall @ gross, CLmax %.2f (kt)" % p.cl_max, f"{vs:.2f}", f"<= {p.stall_limit_kt:.0f}"),
        ("gross CG (%MAC)", f"{mac_frac:.1%}", "25-35%"),
        ("hull volume (ft^3)", f"{hull.volume:.1f}", ">= foam reserve 2x1.5xW"),
        ("static draft (ft)", f"{draft:.2f}", "< 75% depth"),
        ("freeboard @ step (ft)", f"{freeboard_at_step_ft(p, hull, wl):.2f}", ">= 0.33"),
        ("hull-alone GM (ft)", f"{metacentric_height_ft(hull, wl, cg_z):.2f}", "report only"),
        ("sponson touch heel (deg)", f"{sponson_touch_deg(p, wl - hull.bounds[0][2]):.1f}", "<= 10"),
        ("road tipover threshold (g)", f"{tipover_ratio(road_z + DEFAULT.keel_to_ground_ft, p.track_width_ft):.2f}", ">= 0.4"),
        ("horiz tail volume V_h", f"{vh:.3f}", ">= 0.35"),
        ("vert tail volume V_v", f"{vv:.4f}", ">= 0.012"),
        ("static margin (%MAC, analytic)", f"{sm:.1%}", ">= 8%"),
        ("tail/thrust-couple ratio @1.2Vs", f"{tc:.2f}", ">= 1.2"),
        ("folded width (ft)", f"{env.width_ft:.2f}", "< 5"),
        ("folded length (ft)", f"{env.length_ft:.1f}", "report: spec said 18-19"),
    ]

    af = load_airfoil()
    va = load_vspaero()
    vs_computed = stall_speed_kt(gross, p.wing_area_sqft, af.clmax_3d)
    rows += [
        ("airfoil (XFOIL, Re %.0fk)" % (af.reynolds_mac / 1e3),
         af.selected, "clmax_2d %.2f" % af.clmax_2d),
        ("CLmax_3D (0.90 x 2D)", f"{af.clmax_3d:.3f}", ">= 1.755 for 24 kt"),
        ("stall @ COMPUTED CLmax (kt)", f"{vs_computed:.2f}",
         f"<= {p.stall_limit_kt:.0f} — Ryan gate pending"),
        ("static margin (%MAC, VSPAERO)", f"{va.static_margin_frac_mac:.1%}",
         ">= 8% — Ryan gate pending (>0 gated)"),
        ("CNbeta (/rad, VSPAERO w/ hull)", f"{va.cnb_per_rad:+.4f}", "> 0"),
        ("SM cross-check |vsp - analytic|",
         f"{abs(va.static_margin_frac_mac - sm):.1%}", "<= 8%"),
    ]
    w = max(len(r[0]) for r in rows)
    print(f"sea-ez design report — targets, not validated engineering\n{'-' * 60}")
    for name, val, limit in rows:
        print(f"  {name:<{w}}  {val:>10}   [{limit}]")


if __name__ == "__main__":
    main()
