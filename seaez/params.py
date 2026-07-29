"""Design-point parameter SSOT (spec §2-§4; donor memo docs/research/2026-07-donor-selection.md).

These values are DESIGN TARGETS feeding design-consistency checks. They are
NOT validated engineering and NOT airworthiness proof (spec safety notice).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignParams:
    # --- Regulatory / design point ---
    gross_design_lb: float = 490.0        # spec §3: gross ~470-500 lb
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
    cl_max: float = 1.8                   # spec §3: high-lift ultralight airfoil TARGET —
                                          # unverified until airfoil chosen (donor memo §2 gaps)

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

    @property
    def fuel_lb(self) -> float:
        return self.fuel_capacity_gal * self.fuel_density_lb_per_gal


DEFAULT = DesignParams()
