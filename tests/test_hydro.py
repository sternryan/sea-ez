from pathlib import Path

import pytest
import trimesh

from seaez.hydro import (
    WATER_LB_FT3,
    displaced_volume_ft3,
    foam_reserve_ok,
    freeboard_at_step_ft,
    solve_waterline,
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
