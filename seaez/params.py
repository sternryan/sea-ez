"""Design-point parameter SSOT (spec §2-§4; donor memo docs/research/2026-07-donor-selection.md).

These values are DESIGN TARGETS feeding design-consistency checks. They are
NOT validated engineering and NOT airworthiness proof (spec safety notice).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignParams:
    # --- Regulatory / design point ---
    gross_design_lb: float = 488.0        # stall-limited: max gross for 24 kt at CLmax 1.79 /
                                          # 140 sqft is 488.8 (was 490; spec §3 band 470-500
                                          # intact; actual rollup 479 -- 9 lb growth margin;
                                          # Ryan veto point 2026-07-29
    pilot_lb: float = 190.0               # spec §3: design pilot + gear
    fuel_capacity_gal: float = 5.0        # FAR 103.7 / spec §2
    fuel_density_lb_per_gal: float = 6.0  # 2-stroke premix, ~gasoline density
    stall_limit_kt: float = 24.0          # spec §2: power-off stall ceiling

    # --- Wing (spec §3-4; Firefly planform scaled UP from 117 sq ft, donor memo §4) ---
    wing_area_sqft: float = 140.0
    wing_span_ft: float = 34.0            # matches design/massing_v0.py
    wing_taper_ratio: float = 0.65        # tip/root, matches massing_v0
    wing_center_x_ft: float = 7.9         # unswept, chords centered here (massing_v0)
    wing_z_ft: float = 3.35               # spine 1.35 + 2.0 above spine (massing_v0)
    cl_max: float = 1.79                  # landing-config CLmax_3D target = (usa35b 1.694 +
                                          # flap 0.3) x 0.90 = 1.7946, rounded DOWN conservative;
                                          # consistency-gated against computed aerodata
    flap_dclmax_2d: float = 0.3           # full-span flaperons, plain-flap low end;
                                          # Ryan ruling 2026-07-29; landing config counts
                                          # toward FAR 103 stall

    # --- Rider / loadout stations (bow datum X, keel-baseline Z, massing_v0 frame) ---
    seat_x_ft: float = 6.3
    seat_z_flight_ft: float = 1.9         # leaned "cafe" posture CG height
    seat_z_road_ft: float = 2.2           # upright pedaling posture CG height
    fuel_x_ft: float = 7.2                # tank behind seatback at CG (spec §7)
    fuel_z_ft: float = 1.2

    # --- Hull (massing-grade; engineering hull is a later plan) ---
    hull_length_ft: float = 12.0
    hull_beam_ft: float = 2.5
    hull_depth_ft: float = 1.35           # spine height over keel baseline
    hull_step_fraction: float = 0.55

    # --- Sponsons (spec §4: on outer wing panels) ---
    sponson_half_span_frac: float = 0.97  # spanwise position / half-span
    sponson_bottom_below_wing_ft: float = 1.275  # drop 1.0 + half of 0.55 width

    # --- Road mode (spec §4) ---
    track_width_ft: float = 3.0           # trike main-wheel track, inside folded envelope
    folded_width_limit_ft: float = 5.0    # spec §4 hard target (gated in Phase 2.2)
    folded_wing_z_ft: float = 2.2         # wings folded alongside boom: CG height estimate
    keel_to_ground_ft: float = 0.5        # wheels-down keel-to-pavement clearance estimate; tipover uses CG height above GROUND

    # --- Empennage (SIZED by the Phase 2.2 tail-volume gates; massing_v0's
    # 7.0x1.4 stab computed V_h~0.17 — too small, superseded by these) ---
    stab_span_ft: float = 8.4
    stab_chord_ft: float = 2.5
    fin_area_sqft: float = 6.0
    tail_ac_x_ft: float = 19.9            # stab quarter-chord AC station (bow datum); +2.5 ft boom extension per Ryan ruling 2026-07-29 (SM lever, wake-proximity fix — +1.5 ft gave 7.54% MAC, +2.0 ft gave 7.66% MAC, both short of the 8% floor; extended to the ruling's stated max of 2.5 ft total)
    overall_length_ft: float = 21.9       # airframe length incl. tail: +2.5 ft boom (max per ruling 2026-07-29) so the 2.5 ft-chord stab's quarter-chord AC sits at tail_ac_x_ft. Mass delta stays parked for 2.3b laminate (tail mass 16 lb unchanged).

    # --- Propulsion geometry (spec §3-4; thrust is a TARGET until measured) ---
    static_thrust_lb: float = 165.0       # Moster 185 class ~75 kgf static; conservative max for couple
    thrust_line_z_ft: float = 4.35        # prop center above keel baseline, massing_v0

    # --- Fold geometry (spec §4 Kolb-style aft-fold; pivot at rear spar root) ---
    fold_pivot_x_ft: float = 9.4          # rear-spar attach station estimate (bow datum)
    fold_root_y_ft: float = 0.7           # panel root offset from centerline
    fold_clearance_ft: float = 0.5        # per-side stowage clearance in folded width — MUST also cover the tucked wingtip sponson; 2.3 fold kinematics verifies (width gate margin is only 0.30 ft total)

    @property
    def fuel_lb(self) -> float:
        return self.fuel_capacity_gal * self.fuel_density_lb_per_gal

    @property
    def stab_area_sqft(self) -> float:
        return self.stab_span_ft * self.stab_chord_ft


DEFAULT = DesignParams()
