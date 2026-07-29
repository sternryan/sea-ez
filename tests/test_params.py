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
    import pytest
    with pytest.raises(dataclasses.FrozenInstanceError):
        DEFAULT.pilot_lb = 200.0  # type: ignore[misc]
