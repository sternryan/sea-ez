from pathlib import Path

import pytest

from seaez.ledger import (
    Part,
    load_parts,
    rollup_empty_lb,
    chute_lb,
    EMPTY_WEIGHT_LIMIT_LB,
    CHUTE_ALLOWANCE_LB,
)

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def test_parts_file_loads_and_is_nonempty():
    parts = load_parts(PARTS)
    assert len(parts) >= 10
    assert all(isinstance(p, Part) for p in parts)
    assert all(p.mass_lb > 0 for p in parts)


def test_empty_weight_within_part_103_limit():
    """THE gate: airframe (chute excluded) must be <= 254 lb. Spec §2, §5."""
    parts = load_parts(PARTS)
    assert rollup_empty_lb(parts) <= EMPTY_WEIGHT_LIMIT_LB


def test_chute_within_its_own_allowance():
    parts = load_parts(PARTS)
    assert 0 < chute_lb(parts) <= CHUTE_ALLOWANCE_LB


def test_chute_excluded_from_empty_rollup():
    parts = load_parts(PARTS)
    total_all = sum(p.mass_lb for p in parts if p.counts_toward_empty)
    assert rollup_empty_lb(parts) == pytest.approx(total_all - chute_lb(parts))


def test_removable_items_flagged_not_counted():
    """Accessory battery pack COUNTS (batteries are empty weight);
    phone/iPad must not appear as a counting part at all."""
    parts = load_parts(PARTS)
    names = {p.name: p for p in parts}
    assert names["accessory_battery_pack"].counts_toward_empty is True
    assert not any("phone" in p.name or "ipad" in p.name for p in parts)
