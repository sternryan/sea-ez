import math
from pathlib import Path

import pytest
import trimesh

from seaez.hydro import (
    WATER_LB_FT3,
    displaced_volume_ft3,
    foam_reserve_ok,
    freeboard_at_step_ft,
    metacentric_height_ft,
    solve_waterline,
    sponson_touch_deg,
    waterplane_ixx_ft4,
)
from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


@pytest.fixture(scope="module")
def hull():
    from design.geometry import hull_mesh
    return hull_mesh(DEFAULT)


def gross_lb():
    parts = load_parts(PARTS)
    total, _x, _z = cg(parts, extra_masses=[
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ])
    return total


def test_displaced_volume_of_unit_cube():
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))  # centered at origin
    assert displaced_volume_ft3(box, 0.0) == pytest.approx(0.5, abs=0.01)
    assert displaced_volume_ft3(box, 0.5) == pytest.approx(1.0, abs=0.01)


def test_gate_hull_floats_at_gross(hull):
    """GATE (spec §1 success criterion 2): waterline solve converges with the
    hull less than fully submerged at actual gross weight."""
    wl = solve_waterline(hull, gross_lb())
    draft = wl - hull.bounds[0][2]
    depth = hull.bounds[1][2] - hull.bounds[0][2]
    assert 0.0 < draft < 0.75 * depth, f"draft {draft:.2f} ft of {depth:.2f} ft depth"


def test_gate_freeboard_at_step(hull):
    """GATE: >= 4 in of freeboard at the step at static gross."""
    wl = solve_waterline(hull, gross_lb())
    assert freeboard_at_step_ft(DEFAULT, hull, wl) >= 0.33


def test_gate_foam_reserve(hull):
    """GATE (spec §6): hull envelope holds >= 1.5x-gross foam buoyancy volume,
    with 2x headroom because sealed bays won't fill the whole envelope."""
    assert foam_reserve_ok(hull, gross_lb())


def test_waterplane_ixx_of_box():
    # 4 ft long x 2 ft wide box, waterline mid-height: I_xx = L*B^3/12 = 4*8/12
    box = trimesh.creation.box(extents=(4.0, 2.0, 1.0))
    assert waterplane_ixx_ft4(box, 0.0) == pytest.approx(4.0 * 8.0 / 12.0, rel=0.05)


def test_gm_sign_matches_box_physics():
    # Wide flat box with low KG floats stably: GM > 0
    box = trimesh.creation.box(extents=(4.0, 2.0, 1.0))
    assert metacentric_height_ft(box, 0.0, kg_ft=-0.25) > 0.0


def test_gate_sponsons_touch_before_10_degrees(hull):
    """GATE (spec §4): wingtip sponsons engage the water at a small heel angle
    so the narrow hull never depends on its own (likely negative) GM."""
    wl = solve_waterline(hull, gross_lb())
    angle = sponson_touch_deg(DEFAULT, wl)
    assert 0.0 < angle <= 10.0, f"sponson touches at {angle:.1f} deg"


def test_hull_alone_gm_is_reported_not_gated(hull):
    """Documentation test: record hull-alone GM at gross with the flight CG.
    Expected near zero or negative — that is WHY the sponsons exist. This
    test only asserts the computation runs and returns a finite number."""
    parts = load_parts(PARTS)
    _t, _x, kg = cg(parts, extra_masses=[
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ])
    wl = solve_waterline(hull, gross_lb())
    gm = metacentric_height_ft(hull, wl, kg_ft=kg)
    assert math.isfinite(gm)
