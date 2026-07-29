"""Mass budget ledger. SSOT for empty-weight compliance (spec §2, §5)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_CLASSIFICATIONS = {"primary_structure", "secondary", "non_structural"}
VALID_PROCESSES = {"composite_layup", "machined_metal", "fdm_print", "purchased"}

# Part 103 empty-weight ceiling and legal ballistic-chute allowance (FAR 103.7 / spec §2).
EMPTY_WEIGHT_LIMIT_LB = 254.0
CHUTE_ALLOWANCE_LB = 24.0


@dataclass(frozen=True)
class Part:
    name: str
    group: str
    mass_lb: float
    classification: str
    process: str
    counts_toward_empty: bool
    is_chute: bool
    # Station of the part CG: bow datum X, keel-baseline Z, flight config.
    # Frame matches design/massing_v0.py. Estimate-grade until CAD refines them.
    x_ft: float
    z_ft: float

    def __post_init__(self) -> None:
        if self.classification not in VALID_CLASSIFICATIONS:
            raise ValueError(f"{self.name}: bad classification {self.classification!r}")
        if self.process not in VALID_PROCESSES:
            raise ValueError(f"{self.name}: bad process {self.process!r}")


def load_parts(path: Path) -> list[Part]:
    raw = yaml.safe_load(Path(path).read_text())
    return [Part(**entry) for entry in raw["parts"]]


def rollup_empty_lb(parts: list[Part]) -> float:
    return sum(p.mass_lb for p in parts if p.counts_toward_empty and not p.is_chute)


def chute_lb(parts: list[Part]) -> float:
    return sum(p.mass_lb for p in parts if p.is_chute)


def cg(
    parts: list[Part],
    extra_masses: list[tuple[float, float, float]] = (),
) -> tuple[float, float, float]:
    """Mass-weighted CG over ALL listed parts (chute included) plus extras.

    extra_masses entries are (mass_lb, x_ft, z_ft) — pilot, fuel, cargo.
    Returns (total_lb, cg_x_ft, cg_z_ft).
    """
    masses = [(p.mass_lb, p.x_ft, p.z_ft) for p in parts] + list(extra_masses)
    total = sum(m for m, _x, _z in masses)
    if total <= 0:
        raise ValueError("cg() needs positive total mass")
    cg_x = sum(m * x for m, x, _z in masses) / total
    cg_z = sum(m * z for m, _x, z in masses) / total
    return total, cg_x, cg_z
