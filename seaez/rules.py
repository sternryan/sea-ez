"""Design-rule checks beyond mass. Spec §6: printed polymer forbidden in primary structure."""
from __future__ import annotations

from seaez.ledger import Part


def violations(parts: list[Part]) -> list[str]:
    out: list[str] = []
    for p in parts:
        if p.classification == "primary_structure" and p.process == "fdm_print":
            out.append(
                f"{p.name}: fdm_print is forbidden for primary structure (spec §6)"
            )
    return out
