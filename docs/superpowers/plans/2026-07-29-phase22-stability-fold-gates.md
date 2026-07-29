# Phase 2.2 — Configuration & Stability Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Size the empennage from tail-volume gates, add analytic longitudinal-stability and thrust-couple gates, and compute the folded road envelope — extending `make gates` from 11 to 17 report rows.

**Architecture:** Pure-math modules only (no new CAD): tail params join `DesignParams`; `seaez/sizing.py` gains tail-volume coefficients; new `seaez/stability.py` (neutral point / static margin / thrust couple) and `seaez/foldmode.py` (folded envelope) consume params + the existing ledger CG. Every number analytic with documented assumption constants — OpenVSP replaces the analytic stability gates in Phase 2.3.

**Tech Stack:** Python ≥3.10, pytest. No new dependencies.

**Scope note (spec §9 milestone 2, second slice):** Deliberately OUT: OpenVSP gates (2.3), spar/laminate (gated on Legal Eagle XL plans + Kolb call), manufacturing outputs (2.4), CAD solids for wing/tail (2.3 alongside spar work).

**Known design findings this plan encodes (do not "fix" silently):**
- Massing v0's tail (9.8 sq ft stab) yields V_h ≈ 0.17 — too small. This plan SIZES the tail: stab 8.4 ft × 2.5 ft = 21.0 sq ft, fin 6.0 sq ft. `design/massing_v0.py` stays untouched (visualization reference).
- Folded LENGTH computes to ≈25.7 ft, exceeding spec §4's "~18–19 ft" estimate (that figure fit the Firefly's 22 ft span, not our 34 ft). This is a spec-reconciliation item surfaced to Ryan — the fold task REPORTS length and gates only width (<5 ft). Do not shrink the span or move the pivot to force 19 ft.

## Global Constraints

- Stall ≤ 24 kt, gross 470–500 lb, wing 140 sq ft / 34 ft span (Phase 2.1 SSOT values — unchanged).
- Folded width < **5 ft** (spec §4) — now gated. Folded length: REPORT ONLY this phase.
- v1 first flights occur WITHOUT the foreplane (spec §4) — all stability gates are no-foreplane.
- All commands via `.venv/bin/pytest` / `.venv/bin/python` from repo root `/Users/ryanstern/sea-ez`.
- **Safety framing:** every new physics module docstring states these are design-consistency checks on targets, NOT validated engineering (copy the phrasing from `seaez/sizing.py`).
- **Datum discipline (Phase 2.1 learning):** every vertical or longitudinal argument name carries its datum (`_x_ft` = bow datum, `_z_ft` = keel baseline). No mesh-datum values appear in this phase.
- Analytic-assumption constants (tail efficiency, lift-slope ratio, downwash) live ONLY in `seaez/stability.py` with a comment block; they are targets, replaced by OpenVSP in 2.3.
- Commit style `feat:` / `test:` / `docs:`.

## File Structure

- Modify `seaez/params.py` — tail, thrust, and fold parameters appended to `DesignParams`.
- Modify `seaez/sizing.py` — tail-volume coefficient functions.
- Create `seaez/stability.py` — neutral point, static margin, thrust-couple authority. Consumes ledger CG.
- Create `seaez/foldmode.py` — folded-envelope math.
- Modify `scripts/design_report.py` — six new rows.
- Tests: append `tests/test_params.py`, `tests/test_sizing.py`; create `tests/test_stability.py`, `tests/test_foldmode.py`.

Reference values used throughout (from the live Phase 2.1 ledger; tests compute them fresh, these are oracle checks): gross 479.0 lb, cg_x 7.1403 ft (31.8% MAC), cg_z 2.109 ft, MAC 4.1794 ft, mac_le_x 5.8103 ft, S·MAC = 585.11, S·b = 4760, Vs 23.69 kt.

---

### Task 1: Tail / thrust / fold parameters

**Files:**
- Modify: `seaez/params.py`
- Test: `tests/test_params.py` (append)

**Interfaces:**
- Produces (appended `DesignParams` fields, all float): `stab_span_ft=8.4`, `stab_chord_ft=2.5`, `fin_area_sqft=6.0`, `tail_ac_x_ft=17.4`, `static_thrust_lb=165.0`, `thrust_line_z_ft=4.35`, `fold_pivot_x_ft=9.4`, `fold_root_y_ft=0.7`, `fold_clearance_ft=0.5`; property `stab_area_sqft -> float` (span × chord). Tasks 2–5 consume these.

- [ ] **Step 1: Write the failing test** (append to `tests/test_params.py`)

```python
def test_tail_thrust_fold_params():
    p = DEFAULT
    assert p.stab_area_sqft == pytest.approx(21.0)        # 8.4 x 2.5, sized for V_h gate
    assert p.fin_area_sqft == 6.0
    assert p.tail_ac_x_ft == 17.4                          # massing_v0 tail AC station
    assert p.static_thrust_lb == 165.0                     # Moster-185-class static thrust TARGET
    assert p.thrust_line_z_ft == 4.35                      # massing_v0 prop center height
    assert p.fold_pivot_x_ft == 9.4
```

Add `import pytest` at the top of `tests/test_params.py` if not already present.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_params.py -v`
Expected: FAIL with `AttributeError` (new fields missing)

- [ ] **Step 3: Append to `DesignParams`** (before the `fuel_lb` property)

```python
    # --- Empennage (SIZED by the Phase 2.2 tail-volume gates; massing_v0's
    # 7.0x1.4 stab computed V_h~0.17 — too small, superseded by these) ---
    stab_span_ft: float = 8.4
    stab_chord_ft: float = 2.5
    fin_area_sqft: float = 6.0
    tail_ac_x_ft: float = 17.4            # tail aerodynamic-center station (bow datum), massing_v0 boom

    # --- Propulsion geometry (spec §3-4; thrust is a TARGET until measured) ---
    static_thrust_lb: float = 165.0       # Moster 185 class ~75 kgf static; conservative max for couple
    thrust_line_z_ft: float = 4.35        # prop center above keel baseline, massing_v0

    # --- Fold geometry (spec §4 Kolb-style aft-fold; pivot at rear spar root) ---
    fold_pivot_x_ft: float = 9.4          # rear-spar attach station estimate (bow datum)
    fold_root_y_ft: float = 0.7           # panel root offset from centerline
    fold_clearance_ft: float = 0.5        # per-side stowage clearance in folded width
```

And after the `fuel_lb` property:

```python
    @property
    def stab_area_sqft(self) -> float:
        return self.stab_span_ft * self.stab_chord_ft
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_params.py -v`
Expected: 3 PASS

- [ ] **Step 5: Full suite, then commit**

Run: `.venv/bin/pytest tests/ -q` → 35 passed

```bash
git add seaez/params.py tests/test_params.py
git commit -m "feat: tail, thrust, and fold parameters (tail resized for volume gates)"
```

---

### Task 2: Tail-volume coefficients

**Files:**
- Modify: `seaez/sizing.py` (append)
- Test: `tests/test_sizing.py` (append)

**Interfaces:**
- Consumes: `planform` (existing), Task 1 params
- Produces: `horizontal_tail_volume(stab_area_sqft, tail_arm_ft, wing_area_sqft, mac_ft) -> float`; `vertical_tail_volume(fin_area_sqft, tail_arm_ft, wing_area_sqft, span_ft) -> float`. Tasks 3 and 6 consume both.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_sizing.py`)

```python
from seaez.sizing import horizontal_tail_volume, vertical_tail_volume
from seaez.ledger import cg


def tail_arm_ft() -> float:
    """Tail AC to actual gross CG (bow datum)."""
    parts = load_parts(PARTS)
    _t, cg_x, _z = cg(parts, extra_masses=[
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ])
    return DEFAULT.tail_ac_x_ft - cg_x


def test_tail_volume_formulas_known_point():
    # S_h=21, l=10.26, S=140, MAC=4.1794 -> V_h ~ 0.368
    assert horizontal_tail_volume(21.0, 10.2597, 140.0, 4.1794) == pytest.approx(0.3682, abs=0.001)
    # S_v=6, l=10.26, S=140, b=34 -> V_v ~ 0.0129
    assert vertical_tail_volume(6.0, 10.2597, 140.0, 34.0) == pytest.approx(0.01293, abs=0.0003)


def test_gate_horizontal_tail_volume():
    """GATE: V_h >= 0.35 (low end of light-aircraft practice; ultralights run
    low, but the high-pylon thrust couple argues against going lower)."""
    vh = horizontal_tail_volume(
        DEFAULT.stab_area_sqft, tail_arm_ft(), DEFAULT.wing_area_sqft,
        planform(DEFAULT.wing_area_sqft, DEFAULT.wing_span_ft,
                 DEFAULT.wing_taper_ratio, DEFAULT.wing_center_x_ft).mac_ft,
    )
    assert vh >= 0.35, f"V_h = {vh:.3f}"


def test_gate_vertical_tail_volume():
    """GATE: V_v >= 0.012 (ultralight-typical low end)."""
    vv = vertical_tail_volume(
        DEFAULT.fin_area_sqft, tail_arm_ft(), DEFAULT.wing_area_sqft, DEFAULT.wing_span_ft,
    )
    assert vv >= 0.012, f"V_v = {vv:.4f}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_sizing.py -v`
Expected: new tests FAIL with `ImportError`

- [ ] **Step 3: Append to `seaez/sizing.py`**

```python
def horizontal_tail_volume(stab_area_sqft: float, tail_arm_ft: float,
                           wing_area_sqft: float, mac_ft: float) -> float:
    """V_h = S_h * l_h / (S * MAC). Arm is tail AC to gross CG, bow datum."""
    return stab_area_sqft * tail_arm_ft / (wing_area_sqft * mac_ft)


def vertical_tail_volume(fin_area_sqft: float, tail_arm_ft: float,
                         wing_area_sqft: float, span_ft: float) -> float:
    """V_v = S_v * l_v / (S * b). Arm is tail AC to gross CG, bow datum."""
    return fin_area_sqft * tail_arm_ft / (wing_area_sqft * span_ft)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_sizing.py -v`
Expected: all PASS (V_h ≈ 0.368, V_v ≈ 0.0129 with cg_x 7.1403 → arm 10.2597)

- [ ] **Step 5: Full suite, then commit**

```bash
git add seaez/sizing.py tests/test_sizing.py
git commit -m "feat: tail-volume coefficient gates"
```

---

### Task 3: Analytic neutral point + static-margin gate

**Files:**
- Create: `seaez/stability.py`
- Test: `tests/test_stability.py`

**Interfaces:**
- Consumes: Tasks 1–2, `planform`, `cg`
- Produces: module constants `TAIL_EFFICIENCY = 0.90`, `TAIL_LIFT_SLOPE_RATIO = 0.85`, `DOWNWASH_DERIV = 0.35`, `WING_AC_FRAC = 0.25`; `neutral_point_frac(vh: float) -> float`; `static_margin_frac(cg_frac_mac: float, vh: float) -> float`. Tasks 4 and 6 extend/consume this module.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_stability.py
from pathlib import Path

import pytest

from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import horizontal_tail_volume, planform
from seaez.stability import neutral_point_frac, static_margin_frac

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def gross_cg():
    parts = load_parts(PARTS)
    return cg(parts, extra_masses=[
        (DEFAULT.pilot_lb, DEFAULT.seat_x_ft, DEFAULT.seat_z_flight_ft),
        (DEFAULT.fuel_lb, DEFAULT.fuel_x_ft, DEFAULT.fuel_z_ft),
    ])


def pf():
    return planform(DEFAULT.wing_area_sqft, DEFAULT.wing_span_ft,
                    DEFAULT.wing_taper_ratio, DEFAULT.wing_center_x_ft)


def vh_actual() -> float:
    _t, cg_x, _z = gross_cg()
    return horizontal_tail_volume(
        DEFAULT.stab_area_sqft, DEFAULT.tail_ac_x_ft - cg_x,
        DEFAULT.wing_area_sqft, pf().mac_ft,
    )


def test_neutral_point_known_value():
    # NP = 0.25 + 0.9*0.85*(1-0.35)*V_h ; V_h=0.3682 -> 0.25+0.1831 = 0.4331
    assert neutral_point_frac(0.3682) == pytest.approx(0.4331, abs=0.002)


def test_static_margin_is_np_minus_cg():
    assert static_margin_frac(0.30, 0.3682) == pytest.approx(0.4331 - 0.30, abs=0.002)


def test_gate_static_margin_no_foreplane():
    """GATE: analytic static margin >= 8% MAC, no foreplane (v1 first-flight
    config, spec §4). Assumption constants documented in seaez/stability.py;
    OpenVSP replaces this estimate in Phase 2.3 (spec §8)."""
    _t, cg_x, _z = gross_cg()
    cg_frac = (cg_x - pf().mac_le_x_ft) / pf().mac_ft
    sm = static_margin_frac(cg_frac, vh_actual())
    assert sm >= 0.08, f"static margin {sm:.1%} MAC"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_stability.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seaez.stability'`

- [ ] **Step 3: Write the implementation**

```python
# seaez/stability.py
"""Analytic longitudinal stability and control-authority estimates (spec §8).

Design-consistency checks on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice). The constants below are classic
first-pass assumptions for a strut-braced high-wing with an aft tail; they
are TARGETS, replaced by OpenVSP analysis in Phase 2.3. All stability gates
are for the NO-FOREPLANE configuration (v1 first flights, spec §4).
"""
from __future__ import annotations

# Assumption constants (first-pass classic values; OpenVSP supersedes in 2.3):
TAIL_EFFICIENCY = 0.90        # eta_h: dynamic-pressure ratio at the tail
TAIL_LIFT_SLOPE_RATIO = 0.85  # a_t / a_w: tail vs wing lift-curve slope
DOWNWASH_DERIV = 0.35         # d(epsilon)/d(alpha) behind the wing
WING_AC_FRAC = 0.25           # wing aerodynamic center, fraction of MAC


def neutral_point_frac(vh: float) -> float:
    """Stick-fixed neutral point as a fraction of MAC:
    NP = x_ac + eta_h * (a_t/a_w) * (1 - de/da) * V_h."""
    return WING_AC_FRAC + TAIL_EFFICIENCY * TAIL_LIFT_SLOPE_RATIO * (1.0 - DOWNWASH_DERIV) * vh


def static_margin_frac(cg_frac_mac: float, vh: float) -> float:
    """SM = NP - CG, both as fractions of MAC. Positive = stable."""
    return neutral_point_frac(vh) - cg_frac_mac
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_stability.py -v`
Expected: 3 PASS (SM computes ≈ 11.5% MAC at the current CG)

- [ ] **Step 5: Full suite, then commit**

```bash
git add seaez/stability.py tests/test_stability.py
git commit -m "feat: analytic neutral point and static-margin gate"
```

---

### Task 4: Thrust-couple vs tail-authority gate

**Files:**
- Modify: `seaez/stability.py` (append)
- Test: `tests/test_stability.py` (append)

**Interfaces:**
- Consumes: Task 3 module, `stall_speed_kt`, hydro NOT needed
- Produces: constants `CL_TAIL_MAX = 0.9`, `ROTATION_SPEED_FACTOR = 1.2`; `thrust_pitch_moment_lbft(thrust_lb, thrust_line_z_ft, cg_z_ft) -> float`; `tail_authority_moment_lbft(speed_kt, stab_area_sqft, tail_arm_ft) -> float`; `thrust_couple_ratio(...) -> float` (authority / couple). Task 6 consumes.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_stability.py`)

```python
from seaez.sizing import stall_speed_kt
from seaez.stability import (
    tail_authority_moment_lbft, thrust_couple_ratio, thrust_pitch_moment_lbft,
)


def test_thrust_moment_formula():
    # 165 lb thrust, 2.24 ft above CG -> 369.6 lb-ft nose-down
    assert thrust_pitch_moment_lbft(165.0, 4.35, 2.11) == pytest.approx(369.6, abs=0.5)


def test_gate_tail_counters_thrust_couple_at_rotation():
    """GATE: tail pitch authority >= 1.2x the full-static-thrust nose-down
    couple at rotation speed (1.2 Vs). This is THE configuration risk of the
    high-pylon pusher (spec §4: foreplane exists for exactly this reason, but
    v1 flies without it — so the tail alone must clear the gate)."""
    total, cg_x, cg_z = gross_cg()
    vs = stall_speed_kt(total, DEFAULT.wing_area_sqft, DEFAULT.cl_max)
    ratio = thrust_couple_ratio(
        thrust_lb=DEFAULT.static_thrust_lb,
        thrust_line_z_ft=DEFAULT.thrust_line_z_ft,
        cg_z_ft=cg_z,
        speed_kt=1.2 * vs,
        stab_area_sqft=DEFAULT.stab_area_sqft,
        tail_arm_ft=DEFAULT.tail_ac_x_ft - cg_x,
    )
    assert ratio >= 1.2, f"tail authority / thrust couple = {ratio:.2f}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_stability.py -v`
Expected: new tests FAIL with `ImportError`

- [ ] **Step 3: Append to `seaez/stability.py`**

```python
from seaez.sizing import FPS_PER_KT, RHO_SL_SLUG_FT3

CL_TAIL_MAX = 0.9             # elevator-equipped tail max CL, conservative target
ROTATION_SPEED_FACTOR = 1.2   # rotation at 1.2 Vs


def thrust_pitch_moment_lbft(thrust_lb: float, thrust_line_z_ft: float, cg_z_ft: float) -> float:
    """Nose-down pitch couple from a thrust line above the CG (both z in the
    keel-baseline datum). Static thrust is the conservative worst case —
    prop thrust decays with airspeed."""
    return thrust_lb * (thrust_line_z_ft - cg_z_ft)


def tail_authority_moment_lbft(speed_kt: float, stab_area_sqft: float, tail_arm_ft: float) -> float:
    """Max tail pitch moment: q * S_h * CL_tail_max * eta_h * l_h."""
    v_fps = speed_kt * FPS_PER_KT
    q = 0.5 * RHO_SL_SLUG_FT3 * v_fps**2
    return q * stab_area_sqft * CL_TAIL_MAX * TAIL_EFFICIENCY * tail_arm_ft


def thrust_couple_ratio(thrust_lb: float, thrust_line_z_ft: float, cg_z_ft: float,
                        speed_kt: float, stab_area_sqft: float, tail_arm_ft: float) -> float:
    """Tail authority over thrust couple; >= 1 means the tail wins."""
    couple = thrust_pitch_moment_lbft(thrust_lb, thrust_line_z_ft, cg_z_ft)
    authority = tail_authority_moment_lbft(speed_kt, stab_area_sqft, tail_arm_ft)
    return authority / couple
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_stability.py -v`
Expected: 5 PASS (ratio computes ≈ 1.29 at 1.2×23.69 kt with the current CG)

- [ ] **Step 5: Full suite, then commit**

```bash
git add seaez/stability.py tests/test_stability.py
git commit -m "feat: thrust-couple vs tail-authority gate at rotation"
```

---

### Task 5: Folded-envelope math

**Files:**
- Create: `seaez/foldmode.py`
- Test: `tests/test_foldmode.py`

**Interfaces:**
- Consumes: Task 1 fold params, `planform`
- Produces: `FoldedEnvelope` frozen dataclass with `width_ft`, `length_ft`, `tip_x_ft` (floats); `folded_envelope(p: DesignParams) -> FoldedEnvelope`. Task 6 consumes.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_foldmode.py
import pytest

from seaez.foldmode import folded_envelope
from seaez.params import DEFAULT


def test_gate_folded_width_under_limit():
    """GATE (spec §4): folded width < 5 ft."""
    env = folded_envelope(DEFAULT)
    assert env.width_ft < DEFAULT.folded_width_limit_ft, f"folded width {env.width_ft:.2f} ft"


def test_folded_length_reconciliation_report():
    """SPEC RECONCILIATION (report, not a pass/fail design gate): spec §4
    estimated folded length ~18-19 ft, but that figure fit the Firefly's
    22 ft span. Our 34 ft span folding aft from the rear-spar pivot reaches
    ~25.7 ft. This test pins the COMPUTED value so any geometry change shows
    up, and the mismatch with spec §4 is Ryan's call (accept longer road
    envelope / shorten span / two-piece fold) — do not silently retune
    fold_pivot_x_ft to force 19 ft."""
    env = folded_envelope(DEFAULT)
    assert env.length_ft == pytest.approx(25.7, abs=0.3)
    assert env.length_ft > 19.0  # documents that the spec §4 estimate is NOT met
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_foldmode.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seaez.foldmode'`

- [ ] **Step 3: Write the implementation**

```python
# seaez/foldmode.py
"""Folded (road-mode) envelope estimate (spec §4 Kolb-style aft-fold).

Design-consistency checks on targets — NOT validated engineering (spec
safety notice). Rigid planar fold model: panels pivot aft about the
rear-spar attach, leading edges outboard, resting alongside the tail boom.
Real fold kinematics (swing path, cradle geometry, interference) are a
Phase 2.3 task on the purchased donor fold drawings.
"""
from __future__ import annotations

from dataclasses import dataclass

from seaez.params import DesignParams
from seaez.sizing import planform


@dataclass(frozen=True)
class FoldedEnvelope:
    width_ft: float
    length_ft: float
    tip_x_ft: float


def folded_envelope(p: DesignParams) -> FoldedEnvelope:
    """Folded width: hull beam + per-side stowed panel depth (root-chord
    thickness + clearance). Folded length: panels swing aft from the pivot,
    so the tip reaches pivot_x + (half-span - root offset); envelope length
    is that or the airframe length, whichever governs."""
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    panel_reach = p.wing_span_ft / 2.0 - p.fold_root_y_ft
    tip_x = p.fold_pivot_x_ft + panel_reach

    # 0.12 thickness fraction matches massing_v0 / the Phase 2.1 wing model.
    stowed_depth = 0.12 * pf.root_chord_ft + p.fold_clearance_ft
    width = p.hull_beam_ft + 2.0 * stowed_depth

    airframe_length = 18.5  # massing_v0 OVERALL_LENGTH_FT — airframe incl. tail
    return FoldedEnvelope(
        width_ft=width,
        length_ft=max(tip_x, airframe_length),
        tip_x_ft=tip_x,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_foldmode.py -v`
Expected: 2 PASS (width ≈ 4.70 ft, tip_x = 9.4 + 16.3 = 25.7 ft)

- [ ] **Step 5: Full suite, then commit**

```bash
git add seaez/foldmode.py tests/test_foldmode.py
git commit -m "feat: folded-envelope width gate and length reconciliation"
```

---

### Task 6: Report extension

**Files:**
- Modify: `scripts/design_report.py`

**Interfaces:**
- Consumes: everything above. No new library API.

- [ ] **Step 1: Extend the report**

In `scripts/design_report.py`, add imports:

```python
from seaez.foldmode import folded_envelope
from seaez.sizing import horizontal_tail_volume, vertical_tail_volume
from seaez.stability import static_margin_frac, thrust_couple_ratio
```

Inside `main()`, after the existing computations (`gross`, `cg_x`, `cg_z`, `pf`, `mac_frac`, `vs` are already in scope), add:

```python
    tail_arm = p.tail_ac_x_ft - cg_x
    vh = horizontal_tail_volume(p.stab_area_sqft, tail_arm, p.wing_area_sqft, pf.mac_ft)
    vv = vertical_tail_volume(p.fin_area_sqft, tail_arm, p.wing_area_sqft, p.wing_span_ft)
    sm = static_margin_frac(mac_frac, vh)
    tc = thrust_couple_ratio(
        thrust_lb=p.static_thrust_lb, thrust_line_z_ft=p.thrust_line_z_ft, cg_z_ft=cg_z,
        speed_kt=1.2 * vs, stab_area_sqft=p.stab_area_sqft, tail_arm_ft=tail_arm,
    )
    env = folded_envelope(p)
```

And append these rows to `rows` (before the table print):

```python
        ("horiz tail volume V_h", f"{vh:.3f}", ">= 0.35"),
        ("vert tail volume V_v", f"{vv:.4f}", ">= 0.012"),
        ("static margin (%MAC, analytic)", f"{sm:.1%}", ">= 8%"),
        ("tail/thrust-couple ratio @1.2Vs", f"{tc:.2f}", ">= 1.2"),
        ("folded width (ft)", f"{env.width_ft:.2f}", "< 5"),
        ("folded length (ft)", f"{env.length_ft:.1f}", "report: spec said 18-19"),
```

- [ ] **Step 2: Run end-to-end**

Run: `make gates`
Expected: full suite green; report prints 17 rows. Oracle values: V_h 0.368, V_v 0.0129, SM 11.5%, ratio 1.29, folded width 4.70, folded length 25.7.

- [ ] **Step 3: Commit**

```bash
git add scripts/design_report.py
git commit -m "feat: stability and fold rows in the design report"
```

---

### Task 7: CAD dependency declaration + stale-comment cleanup (Ryan-requested)

**Files:**
- Modify: `pyproject.toml`
- Modify: `seaez/hydro.py` (one comment line)

**Interfaces:** none — packaging + comment hygiene only.

- [ ] **Step 1: Declare the geometry/hydro stack as an optional extra**

In `pyproject.toml`, extend `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
cad = [
    "cadquery>=2.4",
    "trimesh>=4.0",
    "numpy",
    "shapely>=2.0",
    "mapbox-earcut",
    "networkx",
    "matplotlib",
]
```

(matplotlib is used by `design/massing_v0.py` renders; the rest are the Phase 2.1 geometry/hydro runtime found only in `.venv` today — a fresh venv currently cannot run `make gates`.)

- [ ] **Step 2: Fix the stale comment**

In `seaez/hydro.py` (~line 76), the comment still says `to_planar maps mesh (x, y) -> polygon (x, y)` although the call is now `to_2D()`. Change the comment's `to_planar` to `to_2D`. No code change.

- [ ] **Step 3: Verify the extra resolves and nothing broke**

Run: `.venv/bin/pip install -e ".[cad,dev]" --dry-run` — must resolve without error (dry run only; do NOT let it upgrade the live venv).
Run: `.venv/bin/pytest tests/ -q` — all green.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml seaez/hydro.py
git commit -m "fix: declare cad optional extra; fix stale to_planar comment"
```

---

## Verification (whole plan)

- `make gates` — all tests green, 17-row report, every gated row inside limits, folded-length row visibly reporting the 25.7 vs 18–19 reconciliation.
- `.venv/bin/python design/massing_v0.py` still runs unchanged (massing stays the visualization reference; its small tail is documented as superseded in the params comment).
- `.venv/bin/pip install -e ".[cad,dev]" --dry-run` resolves.
