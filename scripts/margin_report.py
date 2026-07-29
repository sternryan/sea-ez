#!/usr/bin/env python3
"""Print the mass rollup and margin. Run: python scripts/margin_report.py"""
from pathlib import Path

from seaez.ledger import (
    chute_lb,
    load_parts,
    rollup_empty_lb,
    EMPTY_WEIGHT_LIMIT_LB,
    CHUTE_ALLOWANCE_LB,
)
from seaez.rules import violations

LIMIT, CHUTE_ALLOWANCE = EMPTY_WEIGHT_LIMIT_LB, CHUTE_ALLOWANCE_LB

parts = load_parts(Path(__file__).parent.parent / "data" / "parts.yaml")
empty, chute = rollup_empty_lb(parts), chute_lb(parts)
for group in sorted({p.group for p in parts}):
    sub = sum(p.mass_lb for p in parts if p.group == group)
    print(f"  {group:12s} {sub:6.1f} lb")
print(f"empty (no chute): {empty:.1f} / {LIMIT} lb  -> margin {LIMIT - empty:+.1f} lb")
print(f"chute:            {chute:.1f} / {CHUTE_ALLOWANCE} lb")
for v in violations(parts):
    print(f"VIOLATION: {v}")
