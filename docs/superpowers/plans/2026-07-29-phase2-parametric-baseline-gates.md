# Phase 2.1 — Parametric Baseline + Physics Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the spec's design point into a tested, parameter-driven codebase: one parameter SSOT, stall/planform sizing math, a CG rollup gated against the wing MAC band, a parametric hull whose mesh feeds hydrostatics gates (draft, freeboard, foam reserve, sponson-touch heel), and a road-mode tipover gate — all runnable as `make gates`.

**Architecture:** Pure-math modules (`seaez/sizing.py`, `seaez/hydro.py`, `seaez/roadmode.py`) consume a frozen `DesignParams` SSOT (`seaez/params.py`) and the extended mass ledger (parts gain `x_ft`/`z_ft` stations). CAD lives only in `design/geometry.py`, which produces a watertight trimesh the hydro module analyzes — physics code never imports cadquery. Every gate is a pytest test; `massing_v0.py` stays untouched as the visualization reference.

**Tech Stack:** Python ≥3.10, pytest, PyYAML; cadquery + trimesh + numpy (already in `.venv`) for geometry only.

**Scope note (spec §9 Track A milestone 2):** This is the first slice of "Design in code." Deliberately OUT of this plan: OpenVSP static-margin/stall/thrust-couple gates, fold kinematics + folded-envelope check, spar/laminate parametrics (blocked on Legal Eagle XL plans purchase + Kolb contact — Ryan's checklist, first action 2026-08-15), manufacturing outputs (G-code/DXF/STL packages). Those are Phase 2.2+.

## Global Constraints

- Empty weight ≤ **254 lb** chute excluded; chute ≤ **24 lb** own allowance (spec §2, FAR 103.7; already enforced by `seaez/ledger.py`).
- Power-off stall ≤ **24 kt** — sets wing area with gross weight (spec §2).
- Design pilot + gear **190 lb**; gross ≈ **470–500 lb**; wing **135–150 sq ft**; span/planform scales UP from Kolb Firefly's 117 sq ft (spec §3, donor memo §4).
- Fuel **5 US gal** max; premix ≈ 6.0 lb/gal.
- Printed polymer forbidden in primary structure (spec §6; enforced by `seaez/rules.py` — do not weaken).
- Folded width < **5 ft** (spec §4) — recorded in params now, gated in Phase 2.2.
- Flotation: foam buoyancy > **1.5× gross** (spec §6).
- All commands run via `.venv/bin/python` / `.venv/bin/pytest` from the repo root `/Users/ryanstern/sea-ez`. No new runtime deps beyond the existing venv (shapely is verified in Task 6).
- **Safety framing (spec safety notice):** every module docstring that computes a physics number must state these are design-consistency checks on targets, NOT validated engineering or airworthiness proof. Copy the phrasing used below verbatim.
- Commit style: `feat:` / `test:` / `docs:` prefixes, matching existing history.

## File Structure

- Create `seaez/params.py` — frozen `DesignParams` dataclass, SSOT for every design-point number, each with a spec/memo citation comment.
- Create `seaez/sizing.py` — stall-speed and wing-planform (MAC) math. Pure functions, no I/O.
- Modify `seaez/ledger.py` — `Part` gains required `x_ft`, `z_ft`; new `cg()` rollup.
- Modify `data/parts.yaml` — every part gains estimated `x_ft`/`z_ft` stations (flight config, bow datum / keel-baseline datum matching `design/massing_v0.py`).
- Create `design/geometry.py` — parametric hull loft (stations scaled from `DesignParams`), STL→trimesh export. Only file that imports cadquery.
- Create `seaez/hydro.py` — waterline solve, freeboard, foam-reserve check, GM estimate, sponson-touch heel angle. Consumes a `trimesh.Trimesh`, never cadquery.
- Create `seaez/roadmode.py` — road-config CG (folded wing, upright rider) and tipover ratio.
- Create `scripts/design_report.py` — prints every gate value + margin in one table.
- Modify `Makefile` — add `gates` target.
- Tests: `tests/test_params.py`, `tests/test_sizing.py`, `tests/test_cg.py`, `tests/test_geometry.py`, `tests/test_hydro.py`, `tests/test_roadmode.py`.

---

### Task 1: DesignParams SSOT

**Files:**
- Create: `seaez/params.py`
- Test: `tests/test_params.py`

**Interfaces:**
- Produces: `seaez.params.DesignParams` (frozen dataclass), module-level `DEFAULT: DesignParams`, property `DesignParams.fuel_lb -> float`. Every later task imports `DEFAULT`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_params.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_params.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seaez.params'`

- [ ] **Step 3: Write the implementation**

```python
# seaez/params.py
"""Design-point parameter SSOT (spec §2-§4; donor memo docs/research/2026-07-donor-selection.md).

These values are DESIGN TARGETS feeding design-consistency checks. They are
NOT validated engineering and NOT airworthiness proof (spec safety notice).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignParams:
    # --- Regulatory / design point ---
    gross_design_lb: float = 490.0        # spec §3: gross ~470-500 lb
    pilot_lb: float = 190.0               # spec §3: design pilot + gear
    fuel_capacity_gal: float = 5.0        # FAR 103.7 / spec §2
    fuel_density_lb_per_gal: float = 6.0  # 2-stroke premix, ~gasoline density
    stall_limit_kt: float = 24.0          # spec §2: power-off stall ceiling

    # --- Wing (spec §3-4; Firefly planform scaled UP from 117 sq ft, donor memo §4) ---
    wing_area_sqft: float = 140.0
    wing_span_ft: float = 34.0            # matches design/massing_v0.py
    wing_taper_ratio: float = 0.65        # tip/root, matches massing_v0
    wing_center_x_ft: float = 7.9         # unswept, chords centered here (massing_v0)
    wing_z_ft: float = 3.35               # spine 1.35 + 2.0 above spine (massing_v0)
    cl_max: float = 1.8                   # spec §3: high-lift ultralight airfoil TARGET —
                                          # unverified until airfoil chosen (donor memo §2 gaps)

    # --- Rider / loadout stations (bow datum X, keel-baseline Z, massing_v0 frame) ---
    seat_x_ft: float = 6.3
    seat_z_flight_ft: float = 1.9         # leaned "cafe" posture CG height
    seat_z_road_ft: float = 2.2           # upright pedaling posture CG height
    fuel_x_ft: float = 7.2                # tank behind seatback at CG (spec §7)
    fuel_z_ft: float = 1.2

    # --- Hull (massing-grade; engineering hull is a later plan) ---
    hull_length_ft: float = 12.0
    hull_beam_ft: float = 2.5
    hull_depth_ft: float = 1.35           # spine height over keel baseline
    hull_step_fraction: float = 0.55

    # --- Sponsons (spec §4: on outer wing panels) ---
    sponson_half_span_frac: float = 0.97  # spanwise position / half-span
    sponson_bottom_below_wing_ft: float = 1.275  # drop 1.0 + half of 0.55 width

    # --- Road mode (spec §4) ---
    track_width_ft: float = 3.0           # trike main-wheel track, inside folded envelope
    folded_width_limit_ft: float = 5.0    # spec §4 hard target (gated in Phase 2.2)
    folded_wing_z_ft: float = 2.2         # wings folded alongside boom: CG height estimate

    @property
    def fuel_lb(self) -> float:
        return self.fuel_capacity_gal * self.fuel_density_lb_per_gal


DEFAULT = DesignParams()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_params.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add seaez/params.py tests/test_params.py
git commit -m "feat: DesignParams SSOT for phase 2 gates"
```

---

### Task 2: Stall-speed sizing math

**Files:**
- Create: `seaez/sizing.py`
- Test: `tests/test_sizing.py`

**Interfaces:**
- Consumes: `seaez.params.DEFAULT`
- Produces: `stall_speed_kt(gross_lb: float, wing_area_sqft: float, cl_max: float) -> float`, `wing_area_for_stall(gross_lb: float, stall_kt: float, cl_max: float) -> float`, constants `RHO_SL_SLUG_FT3`, `FPS_PER_KT`. Task 10's report and the Task 2 gate use these.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_sizing.py
from pathlib import Path

import pytest

from seaez.ledger import load_parts, rollup_empty_lb, chute_lb
from seaez.params import DEFAULT
from seaez.sizing import stall_speed_kt, wing_area_for_stall

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def gross_actual_lb() -> float:
    """Actual gross from the ledger: airframe + chute + pilot + full fuel."""
    parts = load_parts(PARTS)
    return rollup_empty_lb(parts) + chute_lb(parts) + DEFAULT.pilot_lb + DEFAULT.fuel_lb


def test_stall_math_known_point():
    # 490 lb / 140 sqft / CLmax 1.8 at sea level -> ~23.97 kt
    assert stall_speed_kt(490.0, 140.0, 1.8) == pytest.approx(23.97, abs=0.05)


def test_area_and_speed_are_inverses():
    area = wing_area_for_stall(490.0, 24.0, 1.8)
    assert stall_speed_kt(490.0, area, 1.8) == pytest.approx(24.0, abs=1e-6)


def test_gate_stall_at_actual_gross_within_limit():
    """GATE (spec §2): power-off stall <= 24 kt at actual ledger gross."""
    vs = stall_speed_kt(gross_actual_lb(), DEFAULT.wing_area_sqft, DEFAULT.cl_max)
    assert vs <= DEFAULT.stall_limit_kt


def test_gate_stall_at_design_gross_within_limit():
    """GATE: still legal at the top of the design gross band."""
    vs = stall_speed_kt(DEFAULT.gross_design_lb, DEFAULT.wing_area_sqft, DEFAULT.cl_max)
    assert vs <= DEFAULT.stall_limit_kt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_sizing.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seaez.sizing'`

- [ ] **Step 3: Write the implementation**

```python
# seaez/sizing.py
"""Wing sizing math (spec §2-§3).

Design-consistency checks on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice). CLmax is an assumed target until
an airfoil is chosen and verified (donor memo §2: no candidate's airfoil is
manufacturer-confirmed).
"""
from __future__ import annotations

import math

RHO_SL_SLUG_FT3 = 0.0023769   # sea-level standard air density
FPS_PER_KT = 1.68781


def stall_speed_kt(gross_lb: float, wing_area_sqft: float, cl_max: float) -> float:
    """1-g power-off stall: Vs = sqrt(2W / (rho * S * CLmax)), lb/ft/slug units."""
    v_fps = math.sqrt(2.0 * gross_lb / (RHO_SL_SLUG_FT3 * wing_area_sqft * cl_max))
    return v_fps / FPS_PER_KT


def wing_area_for_stall(gross_lb: float, stall_kt: float, cl_max: float) -> float:
    v_fps = stall_kt * FPS_PER_KT
    return 2.0 * gross_lb / (RHO_SL_SLUG_FT3 * cl_max * v_fps**2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_sizing.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add seaez/sizing.py tests/test_sizing.py
git commit -m "feat: stall-speed sizing math with 24 kt gates"
```

---

### Task 3: Planform / MAC math

**Files:**
- Modify: `seaez/sizing.py` (append)
- Test: `tests/test_sizing.py` (append)

**Interfaces:**
- Produces: `Planform` frozen dataclass with fields `root_chord_ft`, `tip_chord_ft`, `mac_ft`, `mac_le_x_ft` (all float); `planform(area_sqft: float, span_ft: float, taper_ratio: float, center_x_ft: float) -> Planform`. Task 5's CG gate consumes `mac_ft` and `mac_le_x_ft`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_sizing.py`)

```python
from seaez.sizing import planform


def test_planform_geometry():
    # S=140, b=34, taper 0.65, unswept with chords centered at x=7.9
    pf = planform(140.0, 34.0, 0.65, 7.9)
    assert pf.root_chord_ft == pytest.approx(4.991, abs=0.01)   # 2S / (b(1+t))
    assert pf.tip_chord_ft == pytest.approx(3.244, abs=0.01)
    assert pf.mac_ft == pytest.approx(4.179, abs=0.01)          # (2/3)Cr(1+t+t^2)/(1+t)
    assert pf.mac_le_x_ft == pytest.approx(7.9 - 4.179 / 2.0, abs=0.01)


def test_planform_untapered_mac_equals_chord():
    pf = planform(140.0, 34.0, 1.0, 7.9)
    assert pf.mac_ft == pytest.approx(140.0 / 34.0, abs=1e-9)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_sizing.py -v`
Expected: new tests FAIL with `ImportError: cannot import name 'planform'`

- [ ] **Step 3: Write the implementation** (append to `seaez/sizing.py`)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Planform:
    root_chord_ft: float
    tip_chord_ft: float
    mac_ft: float
    mac_le_x_ft: float


def planform(area_sqft: float, span_ft: float, taper_ratio: float, center_x_ft: float) -> Planform:
    """Straight-tapered unswept wing with every chord centered on center_x_ft
    (matches design/massing_v0.py). MAC leading edge sits half a MAC forward
    of the chord centerline."""
    root = 2.0 * area_sqft / (span_ft * (1.0 + taper_ratio))
    tip = root * taper_ratio
    mac = (2.0 / 3.0) * root * (1.0 + taper_ratio + taper_ratio**2) / (1.0 + taper_ratio)
    return Planform(
        root_chord_ft=root,
        tip_chord_ft=tip,
        mac_ft=mac,
        mac_le_x_ft=center_x_ft - mac / 2.0,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_sizing.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add seaez/sizing.py tests/test_sizing.py
git commit -m "feat: planform/MAC math for CG gating"
```

---

### Task 4: Part stations + CG rollup

**Files:**
- Modify: `seaez/ledger.py`
- Modify: `data/parts.yaml`
- Test: `tests/test_cg.py` (create)
- Modify: `tests/test_rules.py:14-18` — the direct `Part(...)` construction gains the two new required fields (`tests/test_ledger.py` only loads YAML and needs no edits)

**Interfaces:**
- Consumes: existing `Part`, `load_parts`
- Produces: `Part` gains required fields `x_ft: float`, `z_ft: float` (bow datum / keel-baseline datum, flight config, massing_v0 frame); `cg(parts: list[Part], extra_masses: list[tuple[float, float, float]] = ()) -> tuple[float, float, float]` returning `(total_lb, cg_x_ft, cg_z_ft)` over ALL listed parts (chute included) plus `(lb, x_ft, z_ft)` extras. Tasks 5, 8, 9 consume `cg`.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_cg.py -v`
Expected: FAIL — `cg` not importable / `Part.__init__` missing `x_ft`

- [ ] **Step 3: Extend `seaez/ledger.py`**

Add to the `Part` dataclass (after `is_chute: bool`):

```python
    # Station of the part CG: bow datum X, keel-baseline Z, flight config.
    # Frame matches design/massing_v0.py. Estimate-grade until CAD refines them.
    x_ft: float
    z_ft: float
```

Append at module end:

```python
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
```

- [ ] **Step 4: Add stations to `data/parts.yaml`**

Append `x_ft` and `z_ft` to every row — exact values (estimates read off `design/massing_v0.py` geometry; comment the file accordingly):

| name | x_ft | z_ft |
|---|---|---|
| wing_assembly | 7.9 | 3.35 |
| hull_chassis | 5.5 | 0.8 |
| tail_boom_empennage | 15.5 | 1.2 |
| foreplane_module | 1.1 | 2.05 |
| engine_mount_exhaust | 9.4 | 4.3 |
| prop | 9.9 | 4.35 |
| prop_guard_ring | 9.9 | 4.35 |
| fuel_system_dry | 7.2 | 1.2 |
| landing_gear | 5.8 | 0.6 |
| pedal_drivetrain | 6.2 | 0.8 |
| controls | 6.0 | 1.3 |
| instruments_sensors | 4.5 | 1.7 |
| accessory_battery_pack | 4.5 | 1.0 |
| hardware_paint_misc | 6.0 | 1.0 |
| ballistic_parachute | 9.2 | 4.0 |

Example row after edit:

```yaml
  - {name: wing_assembly, group: wing, mass_lb: 62.0, classification: primary_structure, process: composite_layup, counts_toward_empty: true, is_chute: false, x_ft: 7.9, z_ft: 3.35}
```

Also add to the file's header comment: `# x_ft/z_ft: part-CG station, bow datum / keel baseline, FLIGHT config (frame = design/massing_v0.py). Estimate-grade until CAD refines.`

Then update the direct construction in `tests/test_rules.py` (line 14) so it carries the new required fields:

```python
    bad = Part(
        name="printed_spar", group="wing", mass_lb=5.0,
        classification="primary_structure", process="fdm_print",
        counts_toward_empty=True, is_chute=False,
        x_ft=7.9, z_ft=3.35,
    )
```

- [ ] **Step 5: Run the full suite to verify everything passes**

Run: `.venv/bin/pytest tests/ -v`
Expected: all PASS (including the pre-existing ledger/rules tests — they load the YAML, which now has the extra keys consumed by the two new dataclass fields)

- [ ] **Step 6: Commit**

```bash
git add seaez/ledger.py data/parts.yaml tests/test_cg.py tests/test_rules.py
git commit -m "feat: part CG stations and cg() rollup in the ledger"
```

---

### Task 5: CG-in-MAC-band gate

**Files:**
- Test: `tests/test_cg.py` (append)

**Interfaces:**
- Consumes: `cg`, `load_parts` (Task 4); `planform` (Task 3); `DEFAULT` (Task 1)

- [ ] **Step 1: Write the gate test** (append to `tests/test_cg.py`)

```python
from seaez.params import DEFAULT
from seaez.sizing import planform


def gross_cg():
    parts = load_parts(PARTS)
    extras = [
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ]
    return cg(parts, extra_masses=extras)


def test_gate_gross_cg_within_mac_band():
    """GATE: gross CG (pilot + full fuel) inside 25-35% MAC.

    Band is the conventional first-pass envelope for a high-wing pusher;
    Phase 2.2's OpenVSP static-margin gate replaces it with a computed
    neutral point (spec §8).
    """
    pf = planform(
        DEFAULT.wing_area_sqft, DEFAULT.wing_span_ft,
        DEFAULT.wing_taper_ratio, DEFAULT.wing_center_x_ft,
    )
    _total, cg_x, _cg_z = gross_cg()
    frac = (cg_x - pf.mac_le_x_ft) / pf.mac_ft
    assert 0.25 <= frac <= 0.35, f"gross CG at {frac:.1%} MAC, outside 25-35%"


def test_gate_gross_weight_sane():
    """GATE: actual gross stays inside the spec §3 design band."""
    total, _cg_x, _cg_z = gross_cg()
    assert 470.0 <= total <= 500.0
```

- [ ] **Step 2: Run the gate**

Run: `.venv/bin/pytest tests/test_cg.py -v`
Expected: PASS. With the Task 4 stations the computed point is ≈479 lb gross, CG ≈ x 7.14 ft → ≈31.8% MAC. If a future station edit pushes it out of band, adjust only the movable stations (`accessory_battery_pack`, `ballistic_parachute` along the pylon, `landing_gear` ±0.5 ft) — never the fixed anatomy (wing, engine, seat) — and record the change in the YAML comment.

- [ ] **Step 3: Commit**

```bash
git add tests/test_cg.py
git commit -m "test: gross CG-in-MAC-band and gross-weight gates"
```

---

### Task 6: Parametric hull geometry + mesh

**Files:**
- Create: `design/geometry.py`
- Test: `tests/test_geometry.py`

**Interfaces:**
- Consumes: `DEFAULT` (Task 1)
- Produces: `build_hull_solid(p: DesignParams) -> cq.Workplane`; `hull_mesh(p: DesignParams) -> trimesh.Trimesh` (watertight, feet units, keel near z≈0.23 — mesh's own bounds are authoritative). Task 7 consumes `hull_mesh`.

- [ ] **Step 1: Verify the CAD stack (no commit needed)**

Run: `.venv/bin/python -c "import cadquery, trimesh, numpy, shapely; print('ok')"`
Expected: `ok`. If shapely is missing: `.venv/bin/pip install shapely` and note it in the commit message.

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_geometry.py
import pytest

from seaez.params import DEFAULT


@pytest.fixture(scope="module")
def mesh():
    from design.geometry import hull_mesh
    return hull_mesh(DEFAULT)


def test_hull_mesh_watertight(mesh):
    assert mesh.is_watertight


def test_hull_mesh_dimensions(mesh):
    length = mesh.bounds[1][0] - mesh.bounds[0][0]
    beam = mesh.bounds[1][1] - mesh.bounds[0][1]
    assert length == pytest.approx(DEFAULT.hull_length_ft, rel=0.05)
    assert beam <= DEFAULT.hull_beam_ft * 1.05


def test_hull_volume_sane(mesh):
    # Loft of massing_v0's stations encloses roughly 20-35 ft^3.
    assert 15.0 < mesh.volume < 40.0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_geometry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'design.geometry'` (add an empty `design/__init__.py` if import as a package fails)

- [ ] **Step 4: Write the implementation**

```python
# design/geometry.py
"""Parametric hull geometry (engineering-input grade, spec §8).

Station shape is normalized from design/massing_v0.py's hand-tuned loft so
hydrostatics run against the same hull the massing renders show. Values are
design targets — NOT validated engineering (spec safety notice).
"""
from __future__ import annotations

import os
import tempfile

import cadquery as cq
import trimesh

from seaez.params import DesignParams

# (x_frac of length, half_beam_frac of beam/2, height_frac of depth, center_z_frac of depth)
# Normalized from massing_v0.build_hull()'s stations; the two step rows are
# injected at step_fraction +/- 0.0125 at build time.
_STATIONS = [
    (0.000, 0.024, 0.022, 0.60),
    (0.075, 0.440, 0.407, 0.70),
    (0.217, 0.760, 0.704, 0.85),
    (0.367, 1.000, 0.778, 0.95),
    ("step_fwd", 1.000, 0.778, 0.95),
    ("step_aft", 0.920, 0.630, 0.82),
    (0.800, 0.600, 0.504, 0.78),
    (1.000, 0.096, 0.222, 0.55),
]


def hull_stations(p: DesignParams) -> list[tuple[float, float, float, float]]:
    """Absolute (x, half_beam, height, center_z) in feet."""
    out = []
    for x_frac, hb_frac, h_frac, cz_frac in _STATIONS:
        if x_frac == "step_fwd":
            x_frac = p.hull_step_fraction - 0.0125
        elif x_frac == "step_aft":
            x_frac = p.hull_step_fraction + 0.0125
        out.append((
            x_frac * p.hull_length_ft,
            max(hb_frac * p.hull_beam_ft / 2.0, 0.02),
            max(h_frac * p.hull_depth_ft, 0.02),
            cz_frac * p.hull_depth_ft,
        ))
    return out


def build_hull_solid(p: DesignParams) -> cq.Workplane:
    stations = hull_stations(p)
    # NOTE: workplane(offset=...) and center(...) are DELTAS from the previous
    # station, not absolute coordinates — same gotcha as massing_v0.build_hull.
    wp = cq.Workplane("YZ")
    first_x, hb, h, cz = stations[0]
    wp = wp.workplane(offset=first_x).center(0, cz).ellipse(hb, h)
    prev_x, prev_cz = first_x, cz
    for x, hb, h, cz in stations[1:]:
        wp = wp.workplane(offset=x - prev_x).center(0, cz - prev_cz).ellipse(hb, h)
        prev_x, prev_cz = x, cz
    return wp.loft(ruled=True)


def hull_mesh(p: DesignParams) -> trimesh.Trimesh:
    solid = build_hull_solid(p)
    with tempfile.TemporaryDirectory() as tmp:
        stl = os.path.join(tmp, "hull.stl")
        solid.val().exportStl(stl, tolerance=0.005, angularTolerance=0.1)
        mesh = trimesh.load(stl, force="mesh")
    if not mesh.is_watertight:
        trimesh.repair.fill_holes(mesh)
    return mesh
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_geometry.py -v`
Expected: 3 PASS. If the volume test fails, print `mesh.volume` and widen ONLY if the value is physically plausible for a 12 ft × 2.5 ft hull (i.e. 10–45 ft³); a value outside that means the loft is broken — fix the loft, not the test.

- [ ] **Step 6: Commit**

```bash
git add design/geometry.py design/__init__.py tests/test_geometry.py
git commit -m "feat: parametric hull geometry with watertight mesh export"
```

---

### Task 7: Hydrostatics — waterline, freeboard, foam reserve

**Files:**
- Create: `seaez/hydro.py`
- Test: `tests/test_hydro.py`

**Interfaces:**
- Consumes: `hull_mesh` (Task 6), `DEFAULT` (Task 1), `cg`/`load_parts` (Task 4)
- Produces: `WATER_LB_FT3 = 62.4`; `displaced_volume_ft3(mesh, waterline_z: float) -> float`; `solve_waterline(mesh, gross_lb: float) -> float` (absolute z of the static waterline); `freeboard_at_step_ft(p, mesh, waterline_z) -> float`; `foam_reserve_ok(mesh, gross_lb) -> bool`. Task 8 extends this module.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_hydro.py
from pathlib import Path

import pytest
import trimesh

from seaez.hydro import (
    WATER_LB_FT3,
    displaced_volume_ft3,
    foam_reserve_ok,
    freeboard_at_step_ft,
    solve_waterline,
)
from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


@pytest.fixture(scope="module")
def hull():
    from design.geometry import hull_mesh
    return hull_mesh(DEFAULT)


def gross_lb():
    parts = load_parts(PARTS)
    total, _x, _z = cg(parts, extra_masses=[
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ])
    return total


def test_displaced_volume_of_unit_cube():
    box = trimesh.creation.box(extents=(1.0, 1.0, 1.0))  # centered at origin
    assert displaced_volume_ft3(box, 0.0) == pytest.approx(0.5, abs=0.01)
    assert displaced_volume_ft3(box, 0.5) == pytest.approx(1.0, abs=0.01)


def test_gate_hull_floats_at_gross(hull):
    """GATE (spec §1 success criterion 2): waterline solve converges with the
    hull less than fully submerged at actual gross weight."""
    wl = solve_waterline(hull, gross_lb())
    draft = wl - hull.bounds[0][2]
    depth = hull.bounds[1][2] - hull.bounds[0][2]
    assert 0.0 < draft < 0.75 * depth, f"draft {draft:.2f} ft of {depth:.2f} ft depth"


def test_gate_freeboard_at_step(hull):
    """GATE: >= 4 in of freeboard at the step at static gross."""
    wl = solve_waterline(hull, gross_lb())
    assert freeboard_at_step_ft(DEFAULT, hull, wl) >= 0.33


def test_gate_foam_reserve(hull):
    """GATE (spec §6): hull envelope holds >= 1.5x-gross foam buoyancy volume,
    with 2x headroom because sealed bays won't fill the whole envelope."""
    assert foam_reserve_ok(hull, gross_lb())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_hydro.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seaez.hydro'`

- [ ] **Step 3: Write the implementation**

```python
# seaez/hydro.py
"""Static hydrostatics from the parametric hull mesh (spec §8 CI gates).

Design-consistency checks on targets — NOT validated engineering, NOT
naval-architecture proof, and no substitute for the flotation and taxi
test campaign (spec §9). Consumes a trimesh; never imports cadquery.
"""
from __future__ import annotations

import trimesh

WATER_LB_FT3 = 62.4


def _submerged(mesh: trimesh.Trimesh, waterline_z: float) -> trimesh.Trimesh | None:
    """The part of the mesh below waterline_z, capped watertight."""
    cut = trimesh.intersections.slice_mesh_plane(
        mesh, plane_normal=(0.0, 0.0, -1.0), plane_origin=(0.0, 0.0, waterline_z),
        cap=True,
    )
    if cut is None or cut.is_empty:
        return None
    return cut


def displaced_volume_ft3(mesh: trimesh.Trimesh, waterline_z: float) -> float:
    sub = _submerged(mesh, waterline_z)
    return 0.0 if sub is None else float(sub.volume)


def solve_waterline(mesh: trimesh.Trimesh, gross_lb: float, tol_lb: float = 0.1) -> float:
    """Bisect the waterline z where displacement supports gross_lb."""
    target_ft3 = gross_lb / WATER_LB_FT3
    lo, hi = float(mesh.bounds[0][2]), float(mesh.bounds[1][2])
    if float(mesh.volume) * WATER_LB_FT3 < gross_lb:
        raise ValueError("hull envelope cannot displace gross weight — it sinks")
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if displaced_volume_ft3(mesh, mid) < target_ft3:
            lo = mid
        else:
            hi = mid
        if (hi - lo) * WATER_LB_FT3 < tol_lb:
            break
    return (lo + hi) / 2.0


def freeboard_at_step_ft(p, mesh: trimesh.Trimesh, waterline_z: float) -> float:
    """Deck height minus waterline at the step station (min freeboard region)."""
    step_x = p.hull_step_fraction * p.hull_length_ft
    section = mesh.section(plane_origin=(step_x, 0.0, 0.0), plane_normal=(1.0, 0.0, 0.0))
    if section is None:
        raise ValueError("no hull section at the step station")
    deck_z = float(section.vertices[:, 2].max())
    return deck_z - waterline_z


def foam_reserve_ok(mesh: trimesh.Trimesh, gross_lb: float, factor: float = 1.5,
                    packing_headroom: float = 2.0) -> bool:
    """Spec §6: foam buoyancy > factor x gross. Sealed bays won't fill the
    envelope, so require the envelope to hold packing_headroom x that volume."""
    required_ft3 = factor * gross_lb / WATER_LB_FT3
    return float(mesh.volume) >= packing_headroom * required_ft3
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_hydro.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add seaez/hydro.py tests/test_hydro.py
git commit -m "feat: hydrostatics gates — waterline, freeboard, foam reserve"
```

---

### Task 8: Hydrostatics — GM estimate + sponson-touch heel gate

**Files:**
- Modify: `seaez/hydro.py` (append)
- Test: `tests/test_hydro.py` (append)

**Interfaces:**
- Consumes: Task 7's functions; `planform` not needed here
- Produces: `waterplane_ixx_ft4(mesh, waterline_z) -> float`; `metacentric_height_ft(mesh, waterline_z, kg_ft) -> float` (may be negative — report, not gate); `sponson_touch_deg(p, waterline_z) -> float`. Task 10's report consumes all three.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_hydro.py`)

```python
import math

from seaez.hydro import metacentric_height_ft, sponson_touch_deg, waterplane_ixx_ft4


def test_waterplane_ixx_of_box():
    # 4 ft long x 2 ft wide box, waterline mid-height: I_xx = L*B^3/12 = 4*8/12
    box = trimesh.creation.box(extents=(4.0, 2.0, 1.0))
    assert waterplane_ixx_ft4(box, 0.0) == pytest.approx(4.0 * 8.0 / 12.0, rel=0.05)


def test_gm_sign_matches_box_physics():
    # Wide flat box with low KG floats stably: GM > 0
    box = trimesh.creation.box(extents=(4.0, 2.0, 1.0))
    assert metacentric_height_ft(box, 0.0, kg_ft=-0.25) > 0.0


def test_gate_sponsons_touch_before_10_degrees(hull):
    """GATE (spec §4): wingtip sponsons engage the water at a small heel angle
    so the narrow hull never depends on its own (likely negative) GM."""
    wl = solve_waterline(hull, gross_lb())
    angle = sponson_touch_deg(DEFAULT, wl)
    assert 0.0 < angle <= 10.0, f"sponson touches at {angle:.1f} deg"


def test_hull_alone_gm_is_reported_not_gated(hull):
    """Documentation test: record hull-alone GM at gross with the flight CG.
    Expected near zero or negative — that is WHY the sponsons exist. This
    test only asserts the computation runs and returns a finite number."""
    parts = load_parts(PARTS)
    _t, _x, kg = cg(parts, extra_masses=[
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ])
    wl = solve_waterline(hull, gross_lb())
    gm = metacentric_height_ft(hull, wl, kg_ft=kg)
    assert math.isfinite(gm)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_hydro.py -v`
Expected: new tests FAIL with `ImportError`

- [ ] **Step 3: Write the implementation** (append to `seaez/hydro.py`)

```python
import math


def waterplane_ixx_ft4(mesh: trimesh.Trimesh, waterline_z: float) -> float:
    """Second moment of the waterplane area about the fore-aft centerline
    (y=0), via Green's theorem over the waterplane outline polygons."""
    section = mesh.section(plane_origin=(0.0, 0.0, waterline_z), plane_normal=(0.0, 0.0, 1.0))
    if section is None:
        return 0.0
    planar, _tf = section.to_planar()
    ixx = 0.0
    for poly in planar.polygons_full:
        # to_planar maps mesh (x, y) -> polygon (x, y); centerline symmetry
        # puts the centroid on y~0, so moments are about the centerline.
        xs, ys = poly.exterior.coords.xy
        for i in range(len(xs) - 1):
            cross = xs[i] * ys[i + 1] - xs[i + 1] * ys[i]
            ixx += cross * (ys[i] ** 2 + ys[i] * ys[i + 1] + ys[i + 1] ** 2)
    return abs(ixx) / 12.0


def metacentric_height_ft(mesh: trimesh.Trimesh, waterline_z: float, kg_ft: float) -> float:
    """GM = KB + BM - KG, all heights in the mesh's own z datum.
    Negative GM means the bare hull is initially unstable — expected for a
    narrow motorcycle hull; roll stability comes from the sponsons (spec §4)."""
    sub = _submerged(mesh, waterline_z)
    if sub is None or sub.volume <= 0:
        raise ValueError("no displaced volume at this waterline")
    kb = float(sub.center_mass[2])
    bm = waterplane_ixx_ft4(mesh, waterline_z) / float(sub.volume)
    return kb + bm - kg_ft


def sponson_touch_deg(p, waterline_z: float) -> float:
    """Heel angle at which the wingtip sponson bottom reaches the water.
    Small-angle rigid roll about the waterline centerline."""
    y = p.sponson_half_span_frac * p.wing_span_ft / 2.0
    sponson_bottom_z = p.wing_z_ft - p.sponson_bottom_below_wing_ft
    height_above_wl = sponson_bottom_z - waterline_z
    if height_above_wl <= 0:
        return 0.0
    return math.degrees(math.atan2(height_above_wl, y))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_hydro.py -v`
Expected: 8 PASS. Datum note: `metacentric_height_ft` takes KG in the mesh's z datum; the ledger's keel-baseline datum and the mesh datum differ by the mesh's own `bounds[0][2]` offset — for this estimate-grade check the discrepancy (< 0.25 ft) is inside the noise and is accepted; Phase 2.2 unifies datums when the engineering hull replaces the massing loft. State this in the docstring if you touch it.

- [ ] **Step 5: Commit**

```bash
git add seaez/hydro.py tests/test_hydro.py
git commit -m "feat: GM estimate and sponson-touch heel gate"
```

---

### Task 9: Road-mode tipover gate

**Files:**
- Create: `seaez/roadmode.py`
- Test: `tests/test_roadmode.py`

**Interfaces:**
- Consumes: `cg`, `load_parts`, `Part` (Task 4); `DEFAULT` (Task 1)
- Produces: `road_cg(parts: list[Part], p: DesignParams) -> tuple[float, float, float]` (folded-wing z override + upright rider + full fuel); `tipover_ratio(cg_z_ft: float, track_width_ft: float) -> float`. Task 10's report consumes both.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_roadmode.py
from pathlib import Path

import pytest

from seaez.ledger import load_parts
from seaez.params import DEFAULT
from seaez.roadmode import road_cg, tipover_ratio

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def test_tipover_ratio_formula():
    # half-track 1.5 ft over CG height 2.0 ft -> tips at 0.75 lateral g
    assert tipover_ratio(2.0, 3.0) == pytest.approx(0.75)


def test_road_cg_lower_wing_than_flight():
    parts = load_parts(PARTS)
    _t, _x, cg_z = road_cg(parts, DEFAULT)
    # folded wing z (2.2) < flight wing z (3.35) must pull road CG below a
    # hypothetical flight-z stack; sanity band from hand calc ~2.0-2.2 ft
    assert 1.8 <= cg_z <= 2.4


def test_gate_road_tipover_margin():
    """GATE (spec §1 success criterion 1): road config tips only above 0.4
    lateral g — generous margin at 5-8 mph pedal speeds."""
    parts = load_parts(PARTS)
    _t, _x, cg_z = road_cg(parts, DEFAULT)
    assert tipover_ratio(cg_z, DEFAULT.track_width_ft) >= 0.4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_roadmode.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seaez.roadmode'`

- [ ] **Step 3: Write the implementation**

```python
# seaez/roadmode.py
"""Road-mode (folded, pedaling) stability checks (spec §4 mode matrix).

Design-consistency checks on targets — NOT validated engineering (spec
safety notice). Static rigid-body tipover only; no dynamic/gust cases.
"""
from __future__ import annotations

import dataclasses

from seaez.ledger import Part, cg
from seaez.params import DesignParams


def road_cg(parts: list[Part], p: DesignParams) -> tuple[float, float, float]:
    """CG in road config: wing folded to its stowed height, rider upright,
    full fuel. Returns (total_lb, cg_x_ft, cg_z_ft)."""
    adjusted = [
        dataclasses.replace(part, z_ft=p.folded_wing_z_ft)
        if part.name == "wing_assembly" else part
        for part in parts
    ]
    extras = [
        (p.pilot_lb, p.seat_x_ft, p.seat_z_road_ft),
        (p.fuel_lb, p.fuel_x_ft, p.fuel_z_ft),
    ]
    return cg(adjusted, extra_masses=extras)


def tipover_ratio(cg_z_ft: float, track_width_ft: float) -> float:
    """Lateral acceleration (in g) at which the trike lifts an inside wheel:
    half-track over CG height. Static rigid-body estimate."""
    return (track_width_ft / 2.0) / cg_z_ft
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_roadmode.py -v`
Expected: 3 PASS (hand calc: road CG z ≈ 2.08 ft → ratio ≈ 0.72)

- [ ] **Step 5: Commit**

```bash
git add seaez/roadmode.py tests/test_roadmode.py
git commit -m "feat: road-mode tipover gate"
```

---

### Task 10: Design report + `make gates`

**Files:**
- Create: `scripts/design_report.py`
- Modify: `Makefile`

**Interfaces:**
- Consumes: everything above. No new library API.

- [ ] **Step 1: Write the report script**

```python
# scripts/design_report.py
"""One-screen design margin report across every Phase 2.1 gate.

Values are design targets under consistency checks — NOT validated
engineering (spec safety notice)."""
from pathlib import Path

from seaez.hydro import (
    freeboard_at_step_ft, metacentric_height_ft, solve_waterline,
    sponson_touch_deg, WATER_LB_FT3,
)
from seaez.ledger import cg, chute_lb, load_parts, rollup_empty_lb, EMPTY_WEIGHT_LIMIT_LB
from seaez.params import DEFAULT
from seaez.roadmode import road_cg, tipover_ratio
from seaez.sizing import planform, stall_speed_kt

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def main() -> None:
    p = DEFAULT
    parts = load_parts(PARTS)
    empty = rollup_empty_lb(parts)
    extras = [
        (p.pilot_lb, p.seat_x_ft, p.seat_z_flight_ft),
        (p.fuel_lb, p.fuel_x_ft, p.fuel_z_ft),
    ]
    gross, cg_x, cg_z = cg(parts, extra_masses=extras)
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    mac_frac = (cg_x - pf.mac_le_x_ft) / pf.mac_ft
    vs = stall_speed_kt(gross, p.wing_area_sqft, p.cl_max)
    _rt, _rx, road_z = road_cg(parts, p)

    from design.geometry import hull_mesh
    hull = hull_mesh(p)
    wl = solve_waterline(hull, gross)
    draft = wl - hull.bounds[0][2]

    rows = [
        ("empty weight (lb)", f"{empty:.1f}", f"<= {EMPTY_WEIGHT_LIMIT_LB:.0f}"),
        ("chute (lb)", f"{chute_lb(parts):.1f}", "<= 24"),
        ("gross w/ pilot+fuel (lb)", f"{gross:.1f}", "470-500"),
        ("stall @ gross, CLmax %.2f (kt)" % p.cl_max, f"{vs:.2f}", f"<= {p.stall_limit_kt:.0f}"),
        ("gross CG (%MAC)", f"{mac_frac:.1%}", "25-35%"),
        ("hull volume (ft^3)", f"{hull.volume:.1f}", ">= foam reserve 2x1.5xW"),
        ("static draft (ft)", f"{draft:.2f}", "< 75% depth"),
        ("freeboard @ step (ft)", f"{freeboard_at_step_ft(p, hull, wl):.2f}", ">= 0.33"),
        ("hull-alone GM (ft)", f"{metacentric_height_ft(hull, wl, cg_z):.2f}", "report only"),
        ("sponson touch heel (deg)", f"{sponson_touch_deg(p, wl):.1f}", "<= 10"),
        ("road tipover threshold (g)", f"{tipover_ratio(road_z, p.track_width_ft):.2f}", ">= 0.4"),
    ]
    w = max(len(r[0]) for r in rows)
    print(f"sea-ez design report — targets, not validated engineering\n{'-' * 60}")
    for name, val, limit in rows:
        print(f"  {name:<{w}}  {val:>10}   [{limit}]")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add the Makefile target**

Append to `Makefile`:

```make
gates:
	.venv/bin/pytest tests/ -q
	.venv/bin/python scripts/design_report.py
```

And add `gates` to the `.PHONY` line: `.PHONY: test report gates`

- [ ] **Step 3: Run it end-to-end**

Run: `make gates`
Expected: full pytest suite passes, then the report table prints with every row inside its limit (GM row is report-only and may be negative).

- [ ] **Step 4: Commit**

```bash
git add scripts/design_report.py Makefile
git commit -m "feat: design margin report and make-gates entry point"
```

---

## Verification (whole plan)

- `make test` — everything green, including pre-existing ledger/rules tests.
- `make gates` — green + report prints.
- `.venv/bin/python design/massing_v0.py` — still runs unchanged (regression check that the ledger field additions didn't break anything it imports — it imports nothing from `seaez`, so this is a smoke check only).
