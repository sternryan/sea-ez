import pytest

from seaez.params import DEFAULT, DesignParams


def test_default_params_match_spec_design_point():
    p = DEFAULT
    assert isinstance(p, DesignParams)
    assert p.stall_limit_kt == 24.0                 # spec §2
    assert p.pilot_lb == 190.0                      # spec §3
    assert 470.0 <= p.gross_design_lb <= 500.0      # spec §3
    assert 135.0 <= p.wing_area_sqft <= 150.0       # spec §3
    assert p.fuel_capacity_gal == 5.0               # FAR 103.7
    assert p.fuel_lb == 30.0                        # 5 gal * 6.0 lb/gal premix
    assert p.folded_width_limit_ft == 5.0           # spec §4


def test_params_frozen():
    import dataclasses
    with pytest.raises(dataclasses.FrozenInstanceError):
        DEFAULT.pilot_lb = 200.0  # type: ignore[misc]


def test_tail_thrust_fold_params():
    p = DEFAULT
    assert p.stab_area_sqft == pytest.approx(21.0)        # 8.4 x 2.5, sized for V_h gate
    assert p.fin_area_sqft == 6.0
    assert p.tail_ac_x_ft == 17.4                          # massing_v0 tail AC station
    assert p.static_thrust_lb == 165.0                     # Moster-185-class static thrust TARGET
    assert p.thrust_line_z_ft == 4.35                      # massing_v0 prop center height
    assert p.fold_pivot_x_ft == 9.4
