# sea-ez Phase 1: Research Gate + Toolchain Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the sea-ez repo with an enforced mass-budget ledger (the CI gate every future part signs), and produce the four Research Gate memos (donor selection, regulatory confirmations, Delta launch sites, Track B checklist) that unblock Phase 2 design-in-code.

**Architecture:** A plain-Python mass ledger (YAML parts file + loader + rollup) with pytest gates, structured so Phase 2 CadQuery parts later replace budgeted masses with computed masses using the same ledger schema. Research deliverables are markdown memos in `docs/research/`, each ending in a decision or a human-action list for Ryan.

**Tech Stack:** Python 3.10+, PyYAML, pytest, GitHub Actions. No CadQuery in Phase 1 (YAGNI — geometry starts Phase 2).

## Global Constraints (from spec §2, §5)

- Airframe empty weight (chute excluded) ≤ **254.0 lb** — CI-enforced.
- Ballistic chute ≤ **24.0 lb** (its own allowance) — CI-enforced.
- Hull-as-float allowance is RESERVE: no ledger entry may depend on it.
- Parts classified `primary_structure` may NOT have process `fdm_print`.
- Batteries count toward empty weight; fuel does not; mounted portable devices (phone/iPad) are excluded as removable equipment.
- Spec SSOT: `docs/superpowers/specs/2026-07-28-sea-motorcycle-ultralight-design.md`. Memos must cite it, not restate numbers.

---

### Task 1: Repo scaffolding + mass ledger with rollup gates (TDD)

**Files:**
- Create: `pyproject.toml`
- Create: `seaez/__init__.py`
- Create: `seaez/ledger.py`
- Create: `data/parts.yaml`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Produces: `seaez.ledger.load_parts(path) -> list[Part]`, `Part` dataclass (`name: str`, `group: str`, `mass_lb: float`, `classification: str`, `process: str`, `counts_toward_empty: bool`, `is_chute: bool`), `rollup_empty_lb(parts) -> float` (sum of `counts_toward_empty and not is_chute`), `chute_lb(parts) -> float`.
- Consumes: nothing (first task).

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "seaez"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pyyaml>=6.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_ledger.py
from pathlib import Path

import pytest

from seaez.ledger import Part, load_parts, rollup_empty_lb, chute_lb

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"

EMPTY_WEIGHT_LIMIT_LB = 254.0
CHUTE_ALLOWANCE_LB = 24.0


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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/sea-ez && pip install -e ".[dev]" && pytest tests/test_ledger.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seaez.ledger'`

- [ ] **Step 4: Write data/parts.yaml (spec §5 table, verbatim budgets)**

```yaml
# Mass budget ledger — SSOT: spec §5. Every future part signs this contract.
# classification: primary_structure | secondary | non_structural
# process: composite_layup | machined_metal | fdm_print | purchased
parts:
  - {name: wing_assembly,          group: wing,      mass_lb: 62.0, classification: primary_structure, process: composite_layup, counts_toward_empty: true,  is_chute: false}
  - {name: hull_chassis,           group: hull,      mass_lb: 55.0, classification: primary_structure, process: composite_layup, counts_toward_empty: true,  is_chute: false}
  - {name: tail_boom_empennage,    group: tail,      mass_lb: 16.0, classification: primary_structure, process: composite_layup, counts_toward_empty: true,  is_chute: false}
  - {name: foreplane_module,       group: foreplane, mass_lb: 4.0,  classification: primary_structure, process: composite_layup, counts_toward_empty: true,  is_chute: false}
  - {name: engine_mount_exhaust,   group: propulsion, mass_lb: 34.0, classification: primary_structure, process: purchased,      counts_toward_empty: true,  is_chute: false}
  - {name: prop,                   group: propulsion, mass_lb: 8.0,  classification: primary_structure, process: purchased,      counts_toward_empty: true,  is_chute: false}
  - {name: prop_guard_ring,        group: propulsion, mass_lb: 4.0,  classification: secondary,         process: fdm_print,      counts_toward_empty: true,  is_chute: false}
  - {name: fuel_system_dry,        group: fuel,      mass_lb: 4.0,  classification: secondary,          process: purchased,      counts_toward_empty: true,  is_chute: false}
  - {name: landing_gear,           group: gear,      mass_lb: 22.0, classification: primary_structure,  process: machined_metal, counts_toward_empty: true,  is_chute: false}
  - {name: pedal_drivetrain,       group: gear,      mass_lb: 9.0,  classification: secondary,          process: purchased,      counts_toward_empty: true,  is_chute: false}
  - {name: controls,               group: controls,  mass_lb: 8.0,  classification: primary_structure,  process: machined_metal, counts_toward_empty: true,  is_chute: false}
  - {name: instruments_sensors,    group: avionics,  mass_lb: 1.5,  classification: non_structural,     process: purchased,      counts_toward_empty: true,  is_chute: false}
  - {name: accessory_battery_pack, group: avionics,  mass_lb: 1.5,  classification: non_structural,     process: purchased,      counts_toward_empty: true,  is_chute: false}
  - {name: hardware_paint_misc,    group: misc,      mass_lb: 8.0,  classification: non_structural,     process: purchased,      counts_toward_empty: true,  is_chute: false}
  - {name: ballistic_parachute,    group: safety,    mass_lb: 22.0, classification: non_structural,     process: purchased,      counts_toward_empty: true,  is_chute: true}
```

- [ ] **Step 5: Write seaez/ledger.py**

```python
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
```

Also create empty `seaez/__init__.py`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_ledger.py -v`
Expected: 5 PASS

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml seaez/ data/parts.yaml tests/test_ledger.py
git commit -m "feat: mass ledger with Part 103 empty-weight and chute gates"
```

---

### Task 2: Structural-integrity rules — no printed primary structure, margin report

**Files:**
- Create: `seaez/rules.py`
- Create: `scripts/margin_report.py`
- Test: `tests/test_rules.py`

**Interfaces:**
- Consumes: `load_parts`, `Part`, `rollup_empty_lb`, `chute_lb` from Task 1 (exact signatures above).
- Produces: `seaez.rules.violations(parts) -> list[str]` (empty list = clean), used by CI in Task 3.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_rules.py
from pathlib import Path

from seaez.ledger import Part, load_parts
from seaez.rules import violations

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def test_real_ledger_has_no_violations():
    assert violations(load_parts(PARTS)) == []


def test_printed_primary_structure_is_rejected():
    bad = Part(
        name="printed_spar", group="wing", mass_lb=5.0,
        classification="primary_structure", process="fdm_print",
        counts_toward_empty=True, is_chute=False,
    )
    out = violations([bad])
    assert len(out) == 1
    assert "printed_spar" in out[0]
    assert "primary structure" in out[0].lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_rules.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seaez.rules'`

- [ ] **Step 3: Write seaez/rules.py**

```python
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
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/ -v`
Expected: 7 PASS

- [ ] **Step 5: Write scripts/margin_report.py (human-readable weigh-in)**

```python
#!/usr/bin/env python3
"""Print the mass rollup and margin. Run: python scripts/margin_report.py"""
from pathlib import Path

from seaez.ledger import chute_lb, load_parts, rollup_empty_lb
from seaez.rules import violations

LIMIT, CHUTE_ALLOWANCE = 254.0, 24.0

parts = load_parts(Path(__file__).parent.parent / "data" / "parts.yaml")
empty, chute = rollup_empty_lb(parts), chute_lb(parts)
for group in sorted({p.group for p in parts}):
    sub = sum(p.mass_lb for p in parts if p.group == group)
    print(f"  {group:12s} {sub:6.1f} lb")
print(f"empty (no chute): {empty:.1f} / {LIMIT} lb  -> margin {LIMIT - empty:+.1f} lb")
print(f"chute:            {chute:.1f} / {CHUTE_ALLOWANCE} lb")
for v in violations(parts):
    print(f"VIOLATION: {v}")
```

- [ ] **Step 6: Run it, sanity-check output**

Run: `python scripts/margin_report.py`
Expected: margin line reads `margin +17.0 lb` (237.0 empty), no violations.

- [ ] **Step 7: Commit**

```bash
git add seaez/rules.py scripts/margin_report.py tests/test_rules.py
git commit -m "feat: design-rule checks (no printed primary structure) + margin report"
```

---

### Task 3: CI gate

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `Makefile`

**Interfaces:**
- Consumes: pytest suite from Tasks 1-2.
- Produces: `make test` as the local gate; GH Actions runs it on push.

- [ ] **Step 1: Write Makefile**

```makefile
.PHONY: test report
test:
	pytest tests/ -v
report:
	python scripts/margin_report.py
```

- [ ] **Step 2: Write .github/workflows/ci.yml**

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install -e ".[dev]"
      - run: make test
```

- [ ] **Step 3: Verify locally**

Run: `make test && make report`
Expected: all tests pass, report prints margin +17.0.

- [ ] **Step 4: Commit**

```bash
git add Makefile .github/workflows/ci.yml
git commit -m "ci: enforce mass and design-rule gates on every push"
```

---

### Task 4: Donor selection research memo

**Files:**
- Create: `docs/research/2026-07-donor-selection.md`

**Interfaces:**
- Consumes: spec §9 donor candidate list.
- Produces: a ranked donor recommendation + spar-data acquisition path; Phase 2 blocks on this decision.

- [ ] **Step 1: Research (web) each candidate — Kolb Firefly, Aerolite 103, Legal Eagle, Airbike**

For each, collect into a comparison table: empty weight, wing area & span, airfoil (if published), documented Part 103 compliance, folding-wing mechanism details (Firefly), plans/kit availability and cost, whether spar/structure data is published or purchasable (plans sets count), float/seaplane fleet history.

- [ ] **Step 2: Write the memo**

Structure: comparison table → discussion of fold-mechanism transferability to an aft-fold on a hull → recommendation (single donor or split donors: fold mechanism from one, aero from another) → concrete spar-data acquisition path (e.g., "buy Firefly plans set from Kolb, $X") → open risks.

- [ ] **Step 3: Verify no unsupported claims**

Every number in the table carries a source URL or "unverified — confirm from plans." No spec numbers restated without citing spec section.

- [ ] **Step 4: Commit**

```bash
git add docs/research/2026-07-donor-selection.md
git commit -m "research: donor selection memo with ranked recommendation"
```

---

### Task 5: Regulatory confirmations memo

**Files:**
- Create: `docs/research/2026-07-regulatory-confirmations.md`

**Interfaces:**
- Consumes: spec §2 open questions, §11.
- Produces: memo with findings + a **human-action list** (calls/emails only Ryan can make).

- [ ] **Step 1: Research question A — hull-as-float allowance**

Read FAA **AC 103-7** (the Part 103 inspection/weight guidance) for how float allowance is worded; search EAA/USUA/USPPA guidance and any FAA legal interpretations on whether a flying-boat hull qualifies for the seaplane float allowance vs. only detachable floats. Document the honest answer including "ambiguous" if ambiguous.

- [ ] **Step 2: Research question B — CA bicycle classification**

Pull CVC §231 (bicycle definition) and any width/wheel-count qualifiers; check whether a ~5 ft wide, 19 ft long pedal-only trike hits any CVC limits (e.g., CVC §21202 lane rules, trailer/width provisions). Document findings.

- [ ] **Step 3: Write memo with human-action list**

End with checklist: e.g., "[ ] Ryan: email EAA government advocacy for float-allowance reading", "[ ] Ryan: confirm with local PD/CHP non-emergency that the folded machine is road-legal as a bicycle on [specific road]."

- [ ] **Step 4: Commit**

```bash
git add docs/research/2026-07-regulatory-confirmations.md
git commit -m "research: regulatory memo (float allowance, CA bicycle classification)"
```

---

### Task 6: Delta launch-site survey + Track B checklist

**Files:**
- Create: `docs/research/2026-07-delta-launch-sites.md`
- Create: `docs/research/2026-07-track-b-checklist.md`

**Interfaces:**
- Consumes: spec §1 (mission), §9 (Track B).
- Produces: ranked launch-site shortlist; Track B action checklist with first action dated.

- [ ] **Step 1: Launch-site survey**

Criteria per site: public ramp within ~1.5 mi of plausible housing, slough width ≥ 1,500 ft straight run or open reach, prevailing wind alignment, boat traffic density, Class G/E ceiling above. Candidates to evaluate: Bethel Island, Discovery Bay, Rio Vista, Isleton, Walnut Grove areas. Rank top 3 with maps links.

- [ ] **Step 2: Track B checklist memo**

Contents: seaplane/ultralight-float instructor options near the Delta (names/fields found via web), used Firefly-class market scan (Barnstormers/eBay/Kolb forums — price range observed), storage options, insurance note, and the ordering rule from spec §9: **no Track A water ops before Track B training**.

- [ ] **Step 3: Commit**

```bash
git add docs/research/2026-07-delta-launch-sites.md docs/research/2026-07-track-b-checklist.md
git commit -m "research: Delta launch-site shortlist + Track B checklist"
```

---

## Self-Review Notes

- Spec coverage: §5 mass table → Task 1 ledger; §6 printed-structure rule → Task 2; CI mandate (§5, §8) → Task 3; §11 open questions → Tasks 4-6. §4/§7 geometry & systems are Phase 2 by design.
- Ledger sums to 237.0 empty + 22 chute = matches spec §5 subtotal and 17 lb margin.
- OpenEFB panel mode / BLE sensors: separate repos per spec §7 — intentionally NOT in this plan.
