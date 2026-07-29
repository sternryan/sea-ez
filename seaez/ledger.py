"""Mass budget ledger. SSOT for empty-weight compliance (spec §2, §5)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_CLASSIFICATIONS = {"primary_structure", "secondary", "non_structural"}
VALID_PROCESSES = {"composite_layup", "machined_metal", "fdm_print", "purchased"}


@dataclass(frozen=True)
class Part:
    name: str
    group: str
    mass_lb: float
    classification: str
    process: str
    counts_toward_empty: bool
    is_chute: bool

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
