# tests/test_cg.py
from pathlib import Path

import pytest

from seaez.ledger import Part, cg, load_parts

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def _part(name, mass, x, z):
    return Part(
        name=name, group="test", mass_lb=mass, classification="secondary",
        process="purchased", counts_toward_empty=True, is_chute=False,
        x_ft=x, z_ft=z,
    )


def test_cg_two_point_masses():
    parts = [_part("a", 10.0, 0.0, 0.0), _part("b", 10.0, 10.0, 2.0)]
    total, cgx, cgz = cg(parts)
    assert total == pytest.approx(20.0)
    assert cgx == pytest.approx(5.0)
    assert cgz == pytest.approx(1.0)


def test_cg_with_extra_masses():
    parts = [_part("a", 10.0, 0.0, 0.0)]
    total, cgx, cgz = cg(parts, extra_masses=[(30.0, 4.0, 2.0)])
    assert total == pytest.approx(40.0)
    assert cgx == pytest.approx(3.0)
    assert cgz == pytest.approx(1.5)


def test_all_ledger_parts_have_plausible_stations():
    parts = load_parts(PARTS)
    for p in parts:
        assert 0.0 <= p.x_ft <= 18.5, f"{p.name}: x_ft outside airframe length"
        assert 0.0 <= p.z_ft <= 5.0, f"{p.name}: z_ft outside airframe height"
