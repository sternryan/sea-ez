import pytest

from seaez.planing import hump_point, hump_sweep, savitsky_resistance_lb, thrust_at_speed_lb


def test_resistance_positive_and_finite():
    pt = savitsky_resistance_lb(weight_lb=479.0, beam_ft=2.5, speed_kt=8.0)
    assert pt.resistance_lb > 0
    assert pt.lambda_wl_b > 0


def test_hump_is_an_interior_peak_not_an_endpoint():
    """The whole point of a 'hump' is that resistance rises then falls --
    if the sweep's max sits on either endpoint, the speed range is too
    narrow to have captured the actual hump."""
    sweep = hump_sweep(weight_lb=479.0, beam_ft=2.5, step_kt=0.5)
    hump = hump_point(weight_lb=479.0, beam_ft=2.5, step_kt=0.5)
    idx = sweep.index(hump)
    assert 0 < idx < len(sweep) - 1, f"hump at sweep edge (idx {idx}/{len(sweep)-1}) -- widen speed_range_kt"


def test_resistance_falls_off_well_past_hump():
    """Past the hump, rising speed should reduce lambda enough that total
    resistance drops well below the peak -- the defining planing behavior."""
    hump = hump_point(weight_lb=479.0, beam_ft=2.5)
    fast = savitsky_resistance_lb(weight_lb=479.0, beam_ft=2.5, speed_kt=40.0)
    assert fast.resistance_lb < 0.85 * hump.resistance_lb


def test_thrust_lapse_decreases_with_speed():
    static = thrust_at_speed_lb(static_thrust_lb=165.0, prop_diameter_ft=4.10, speed_kt=0.01)
    at_hump = thrust_at_speed_lb(static_thrust_lb=165.0, prop_diameter_ft=4.10, speed_kt=8.0)
    assert 0 < at_hump < static
    assert static == pytest.approx(165.0, rel=0.02)


def test_thrust_lapse_monotonic():
    speeds = [2.0, 6.0, 10.0, 14.0]
    thrusts = [thrust_at_speed_lb(165.0, 4.10, v) for v in speeds]
    assert thrusts == sorted(thrusts, reverse=True)
