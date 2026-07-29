# Phase 2.3a — OpenVSP + XFOIL Aero Grounding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ground the CLmax 1.8 target with real XFOIL polars, validate the four analytic stability gates with VSPAERO computed aero, and wire both into `make gates` via committed data files with staleness fingerprints.

**Architecture:** Two-venv split. The main `.venv` (Python 3.14) stays pure-math and runs `make gates` as today. A new `tools/venv313` (Python 3.13) hosts the OpenVSP 3.51.2 Python API and drives a source-built XFOIL 6.97 binary via subprocess; its scripts live in a new top-level `aero/` package and write results to **committed JSON** under `data/aero/`. The main venv gains `seaez/aerodata.py`, which loads that JSON and refuses stale data via a params fingerprint. Gates never call OpenVSP/XFOIL directly — CI and fresh clones keep working; `make aero` regenerates.

**Tech Stack:** Python 3.14 (gates) + Python 3.13 (aero lane), OpenVSP 3.51.2 ARM64 bundle (`tools/OpenVSP-3.51.2-MacOS`), XFOIL 6.97 built from the RobotLocomotion CMake fork with Homebrew gfortran, pytest.

**Install spike results (2026-07-29, this Mac, darwin arm64 — already done, Task 1 scripts it):**
- OpenVSP: `https://openvsp.org/download.php?file=zips/current/mac/OpenVSP-3.51.2-macos-14-ARM64-Python3.13.zip` → unzip to `tools/OpenVSP-3.51.2-MacOS`. Python API: `pip install` the bundled `python/degen_geom python/utilities python/openvsp_config python/openvsp` dirs **in that order** (deps are sibling-local, not on PyPI). Verified: `import openvsp` OK, `ComputeCompGeom` OK, `CheckForVSPAERO(GetVSPAEROPath()) == True`.
- XFOIL: pip `xfoil` wrapper is abandoned (2020, blocked by freshness gate — correctly). Built from source instead: `git clone https://github.com/RobotLocomotion/xfoil` → `cmake -DCMAKE_BUILD_TYPE=Release` + `make` with `brew install gcc cmake` → binary at `tools/xfoil-src/build/src/xfoil`. **Gotcha:** batch runs MUST disable graphics first (`PLOP`/`G` commands) or ASEQ aborts with "Cannot open display". Verified: NACA 4412, Re 1.2e6, α 0→16 polar converges; Clmax ≈ 1.665 @ 16°.
- VSPAERO stability mode: analysis `"VSPAEROSweep"`, input `"UnsteadyType"` = `vsp.STABILITY_DEFAULT` (there is NO "StabilityType" input in 3.51.2). Introspect with `vsp.GetAnalysisInputNames("VSPAEROSweep")` / `vsp.PrintAnalysisInputs("VSPAEROSweep")` rather than guessing names.

## Global Constraints

- Stall ≤ 24 kt, gross 470–500 lb, wing area within spec §3's 135–150 sq ft, span 34 ft, taper 0.65 — Phase 2.1/2.2 SSOT values unchanged **by this plan** (a CLmax shortfall triggers the Task 8 checkpoint, not a silent repoint).
- v1 first flights are NO-FOREPLANE (spec §4): all stability work is the no-foreplane config.
- All gate-lane commands via `.venv/bin/pytest` / `.venv/bin/python` from repo root `/Users/ryanstern/sea-ez`. All aero-lane commands via `tools/venv313/bin/python`. Aero-lane tests live in `aero/tests/` and run via `make aero-test` — they must NOT be collected by `make gates` (main venv can't import openvsp).
- **Safety framing:** every new module docstring states these are design-consistency checks on targets, NOT validated engineering (copy phrasing from `seaez/sizing.py`).
- **Datum discipline (2.1 learning):** `_x_ft` = bow datum, `_z_ft` = keel baseline, in every argument name. OpenVSP model is built in the bow/keel frame directly so no conversion exists to get wrong.
- **Staleness discipline (2.2 learning — the stale-station bug class):** every committed aero JSON embeds a `fingerprint` dict of the exact DesignParams/CG values it was generated from; `seaez/aerodata.py` recomputes current values and hard-fails on mismatch ("stale aero data — run make aero"). No gate may consume aero JSON without the fingerprint check.
- Ryan's rulings (do NOT re-ask): CLmax grounded via XFOIL at Re ≈ 1.2M, candidates mod-NACA-4412 / USA-35B class; tail mass stays 16 lb; fold kinematics + spar are 2.3b, OUT of scope here.
- Commit style `feat:` / `fix:` / `test:` / `docs:`. Work on main; the verify hook re-runs pytest on commit, so a task may only commit when the full gate suite is green.
- `tools/` is gitignored (binaries + venv); the *installer script* is committed and is the reproducibility story.

## Reference values (live ledger, hand-computed oracles — tests compute fresh, these are self-checks)

- gross 479.0 lb, cg_x 7.1403 ft (31.8% MAC), cg_z 2.109 ft, MAC 4.1794 ft, mac_le_x 5.8103 ft, root chord 4.9916 ft, tip 3.2445 ft, AR = 34²/140 = 8.257.
- Analytic: V_h 0.368, V_v 0.0129, NP 43.3% MAC, SM 11.5%, thrust-couple 1.29 @ 1.2Vs, Vs 23.69 kt @ CLmax 1.8.
- Stall-Re at MAC: ν = μ/ρ = 3.737e-7/0.0023769 = 1.5722e-4 ft²/s; V = 23.69 kt = 39.98 fps → **Re_MAC = 39.98 × 4.1794 / 1.5722e-4 ≈ 1.06e6** (Ryan's "~1.2M" was the right order; code computes it, doesn't hardcode).
- **Required CLmax_3D for the 24 kt gate at 479 lb / 140 ft²: CL = 2W/(ρSV²) = 958/(0.0023769 × 140 × (24×1.68781)²) = 1.755.** With the 0.90 2D→3D factor, required Clmax_2D ≈ 1.95. Spike's 4412 gave 1.665 — expect a shortfall and plan for the Task 8 checkpoint.
- CLMAX_3D_FACTOR = 0.90 (unswept AR-8 straight taper, classic decrement; documented constant, not tunable per-airfoil).
- VSPAERO sanity windows (oracle ranges, not gates): SM within 3–25% MAC; |SM_vsp − 11.5%| ≤ 8 %MAC for the cross-check row; CNβ (per rad) between −0.02 and +0.08, gate is CNβ > 0.

## File Structure

- Create `scripts/install_aero_tools.sh` — idempotent installer for `tools/` (OpenVSP zip + python API venv + XFOIL source build).
- Create `aero/__init__.py`, `aero/xfoil_runner.py`, `aero/airfoil_select.py`, `aero/vsp_model.py`, `aero/vsp_stability.py`, `aero/fingerprint.py` — aero lane (venv313 only).
- Create `aero/tests/test_xfoil_runner.py`, `aero/tests/test_vsp_model.py` — aero-lane tests (`make aero-test`).
- Create `data/airfoils/*.dat` — committed candidate coordinates; `data/aero/airfoil_polars.json`, `data/aero/vspaero_stability.json` — committed results.
- Create `seaez/aerodata.py` + `tests/test_aerodata.py` — gate-lane loader, fingerprint check, new gates.
- Modify `seaez/sizing.py` (air viscosity constant + `reynolds()`), `scripts/design_report.py` (new rows), `Makefile` (`tools`, `aero`, `aero-test`), `.gitignore`, `seaez/stability.py` (wire `ROTATION_SPEED_FACTOR` through — 2.2 leftover).
- Create `docs/research/2026-07-29-airfoil-clmax-finding.md` — Task 8 checkpoint memo.

---

### Task 1: Scripted, idempotent aero-tools install (`make tools`)

**Files:**
- Create: `scripts/install_aero_tools.sh`
- Modify: `Makefile`, `.gitignore`

**Interfaces:**
- Produces: `tools/venv313/bin/python` with importable `openvsp`; XFOIL binary at `tools/xfoil-src/build/src/xfoil`. Tasks 2–6 consume both paths verbatim.

- [ ] **Step 1: Write the installer** (`scripts/install_aero_tools.sh`, `chmod +x`)

```bash
#!/bin/bash
# Idempotent installer for the sea-ez aero lane (darwin arm64).
# OpenVSP 3.51.2 ARM64 + bundled py3.13 API, XFOIL 6.97 from source.
# Everything lands in tools/ (gitignored). Re-run safely anytime.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p tools && cd tools

VSP_ZIP="openvsp-3.51.2-arm64-py313.zip"
VSP_URL="https://openvsp.org/download.php?file=zips/current/mac/OpenVSP-3.51.2-macos-14-ARM64-Python3.13.zip"
[ -d OpenVSP-3.51.2-MacOS ] || {
  [ -f "$VSP_ZIP" ] || curl -sL -o "$VSP_ZIP" "$VSP_URL"
  unzip -q "$VSP_ZIP"
}

command -v python3.13 >/dev/null || { echo "need brew python@3.13"; exit 1; }
command -v gfortran   >/dev/null || { echo "need brew gcc"; exit 1; }
command -v cmake      >/dev/null || { echo "need brew cmake"; exit 1; }

[ -d venv313 ] || python3.13 -m venv venv313
# Bundled sibling packages are NOT on PyPI; install in dependency order.
./venv313/bin/pip -q install \
  ./OpenVSP-3.51.2-MacOS/python/degen_geom \
  ./OpenVSP-3.51.2-MacOS/python/utilities \
  ./OpenVSP-3.51.2-MacOS/python/openvsp_config \
  ./OpenVSP-3.51.2-MacOS/python/openvsp

[ -d xfoil-src ] || git clone -q --depth 1 https://github.com/RobotLocomotion/xfoil.git xfoil-src
[ -x xfoil-src/build/src/xfoil ] || {
  mkdir -p xfoil-src/build && cd xfoil-src/build
  cmake .. -DCMAKE_BUILD_TYPE=Release >/dev/null && make -j8 >/dev/null
  cd ../..
}

./venv313/bin/python -c "import openvsp as v; print('openvsp', v.GetVSPVersion())"
[ -x xfoil-src/build/src/xfoil ] && echo "xfoil OK"
echo "aero tools ready"
```

- [ ] **Step 2: Makefile + gitignore**

Append to `Makefile`:

```makefile
tools:
	bash scripts/install_aero_tools.sh
aero:
	tools/venv313/bin/python -m aero.airfoil_select
	tools/venv313/bin/python -m aero.vsp_stability
aero-test:
	tools/venv313/bin/python -m pytest aero/tests -q
```

(add `tools aero aero-test` to `.PHONY`). Append `tools/` to `.gitignore` (create the file if absent — check first; repo may not have one).

- [ ] **Step 3: Run `make tools` and verify idempotency**

Run twice. Expected both times: `openvsp OpenVSP 3.51.2`, `xfoil OK`, `aero tools ready`; second run does no downloads/builds.

- [ ] **Step 4: Run `make gates` (must stay green — nothing in the gate lane changed)**

- [ ] **Step 5: Commit**

```bash
git add scripts/install_aero_tools.sh Makefile .gitignore
git commit -m "feat: scripted idempotent install for OpenVSP+XFOIL aero lane"
```

---

### Task 2: Reynolds number in the sizing SSOT

**Files:**
- Modify: `seaez/sizing.py`
- Test: `tests/test_sizing.py` (append)

**Interfaces:**
- Produces: `AIR_KINEMATIC_VISCOSITY_FT2_S = 1.5722e-4` and `reynolds(speed_kt: float, chord_ft: float) -> float` in `seaez/sizing.py`. Tasks 3 and 4 consume `reynolds()`.

- [ ] **Step 1: Failing test** (append to `tests/test_sizing.py`)

```python
def test_reynolds_at_stall_mac():
    # Vs 23.69 kt, MAC 4.1794 ft, nu 1.5722e-4 -> Re ~= 1.063e6
    from seaez.sizing import reynolds
    assert reynolds(23.69, 4.1794) == pytest.approx(1.063e6, rel=0.01)
```

- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_sizing.py -q` — expect FAIL (no `reynolds`).

- [ ] **Step 3: Implement** (append to `seaez/sizing.py`)

```python
AIR_KINEMATIC_VISCOSITY_FT2_S = 1.5722e-4  # sea-level standard, mu/rho


def reynolds(speed_kt: float, chord_ft: float) -> float:
    """Chord Reynolds number at sea-level standard conditions."""
    return speed_kt * FPS_PER_KT * chord_ft / AIR_KINEMATIC_VISCOSITY_FT2_S
```

- [ ] **Step 4: Run** `make gates` — all green.

- [ ] **Step 5: Commit** `git add seaez/sizing.py tests/test_sizing.py && git commit -m "feat: Reynolds number helper in sizing SSOT"`

---

### Task 3: XFOIL batch runner (aero lane)

**Files:**
- Create: `aero/__init__.py` (empty), `aero/xfoil_runner.py`, `aero/tests/__init__.py` (empty), `aero/tests/test_xfoil_runner.py`

**Interfaces:**
- Consumes: XFOIL binary path from Task 1.
- Produces: `PolarPoint` dataclass (`alpha_deg, cl, cd, cm: float`), `run_polar(airfoil: str | Path, reynolds: float, alpha_start: float, alpha_end: float, alpha_step: float, workdir: Path) -> list[PolarPoint]` where `airfoil` is either `"NACA 4412"` (string starting with "NACA ") or a Path to a Selig-format .dat file, and `clmax(points: list[PolarPoint]) -> tuple[float, float]` returning `(cl_max, alpha_at_clmax)`. Task 4 consumes all three.

- [ ] **Step 1: Failing test** (`aero/tests/test_xfoil_runner.py`)

```python
from pathlib import Path

import pytest

from aero.xfoil_runner import clmax, run_polar


def test_naca4412_polar_re1m(tmp_path):
    pts = run_polar("NACA 4412", reynolds=1.06e6,
                    alpha_start=0.0, alpha_end=18.0, alpha_step=1.0,
                    workdir=tmp_path)
    assert len(pts) >= 12                      # most points converge
    cl, a = clmax(pts)
    assert 1.55 <= cl <= 1.80                  # spike run: 1.665 @ 16 deg, Re 1.2e6
    assert 13.0 <= a <= 18.0
    # drag sanity at low alpha
    low = [p for p in pts if p.alpha_deg <= 4.0]
    assert all(0.004 <= p.cd <= 0.02 for p in low)
```

- [ ] **Step 2: Run** `tools/venv313/bin/python -m pytest aero/tests -q` — expect FAIL (module missing).

- [ ] **Step 3: Implement** (`aero/xfoil_runner.py`)

```python
"""Batch XFOIL driver (aero lane, tools/venv313 + source-built xfoil 6.97).

Design-consistency tooling on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice). 2D section polars only; 3D wing
decrement is applied downstream in seaez/aerodata.py.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

XFOIL_BIN = Path(__file__).parent.parent / "tools" / "xfoil-src" / "build" / "src" / "xfoil"
NCRIT = 9  # standard free-transition e^n default; documented, not tuned


@dataclass(frozen=True)
class PolarPoint:
    alpha_deg: float
    cl: float
    cd: float
    cm: float


def _commands(airfoil: str | Path, reynolds: float, a0: float, a1: float,
              da: float, polar_path: Path) -> str:
    load = f"NACA {airfoil.split()[1]}" if isinstance(airfoil, str) else f"LOAD {airfoil}"
    # PLOP/G first: headless build aborts on ASEQ if graphics are enabled.
    return "\n".join([
        "PLOP", "G", "",
        load,
        "PANE",                      # repanel loaded coordinates (no-op for NACA)
        "OPER",
        f"VISC {reynolds:.6g}",
        "ITER 100",
        "PACC", str(polar_path), "",
        f"ASEQ {a0} {a1} {da}",
        "", "QUIT",
    ]) + "\n"


def _parse_polar(polar_path: Path) -> list[PolarPoint]:
    pts = []
    for line in polar_path.read_text().splitlines():
        f = line.split()
        if len(f) >= 5:
            try:
                pts.append(PolarPoint(float(f[0]), float(f[1]), float(f[2]), float(f[4])))
            except ValueError:
                continue  # header / separator rows
    return sorted(pts, key=lambda p: p.alpha_deg)


def run_polar(airfoil: str | Path, reynolds: float, alpha_start: float,
              alpha_end: float, alpha_step: float, workdir: Path) -> list[PolarPoint]:
    polar = workdir / "polar.txt"
    polar.unlink(missing_ok=True)
    cmds = _commands(airfoil, reynolds, alpha_start, alpha_end, alpha_step, polar)
    subprocess.run([str(XFOIL_BIN)], input=cmds, capture_output=True,
                   text=True, cwd=workdir, timeout=120)
    if not polar.exists():
        raise RuntimeError(f"XFOIL produced no polar for {airfoil}")
    pts = _parse_polar(polar)
    if not pts:
        raise RuntimeError(f"XFOIL polar empty (no converged points) for {airfoil}")
    return pts


def clmax(points: list[PolarPoint]) -> tuple[float, float]:
    best = max(points, key=lambda p: p.cl)
    return best.cl, best.alpha_deg
```

- [ ] **Step 4: Run** `tools/venv313/bin/python -m pytest aero/tests -q` — expect PASS. Also run `make gates` (gate lane untouched, must stay green).

- [ ] **Step 5: Commit** `git add aero && git commit -m "feat: XFOIL batch polar runner in the aero lane"`

---

### Task 4: Candidate airfoils, polar sweep, committed results JSON

**Files:**
- Create: `aero/fingerprint.py`, `aero/airfoil_select.py`, `data/airfoils/usa35b.dat`, `data/aero/airfoil_polars.json` (generated)

**Interfaces:**
- Consumes: `run_polar`/`clmax` (Task 3), `reynolds` + `planform` + `stall_speed_kt` (gate lane — importable because aero lane runs from repo root and seaez is pure-python).
- Produces: `aero/fingerprint.py: params_fingerprint() -> dict` (exact keys below — Task 6 reuses it); `data/aero/airfoil_polars.json` with schema:

```json
{
  "fingerprint": {"wing_area_sqft": 140.0, "wing_span_ft": 34.0, "wing_taper_ratio": 0.65,
                   "gross_lb": 479.0, "mac_ft": 4.1794, "stall_limit_kt": 24.0,
                   "stab_area_sqft": 21.0, "fin_area_sqft": 6.0, "tail_ac_x_ft": 17.4,
                   "cg_x_ft": 7.1403, "cg_z_ft": 2.109},
  "reynolds_mac": 1063000.0,
  "ncrit": 9,
  "candidates": {"naca4412": {"clmax_2d": 1.66, "alpha_clmax_deg": 16.0,
                                "cm_at_clmax": -0.05, "cd_at_cl_1p0": 0.009,
                                "polar": [[0.0, 0.4748, 0.00676, -0.1035], "..."]}},
  "selected": "naca4412",
  "selection_rule": "highest clmax_2d; cd_at_cl_1p0 tiebreak"
}
```

- [ ] **Step 1: Fingerprint module** (`aero/fingerprint.py`) — shared by both JSON writers:

```python
"""Params fingerprint embedded in every committed aero JSON.

The 2.2 stale-station bug class, systematized: results carry the exact
inputs they were computed from; seaez/aerodata.py refuses mismatches.
"""
from __future__ import annotations

from pathlib import Path

from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import planform

PARTS = Path(__file__).parent.parent / "data" / "parts.yaml"


def params_fingerprint() -> dict:
    p = DEFAULT
    parts = load_parts(PARTS)
    gross, cg_x, cg_z = cg(parts, extra_masses=[
        (p.pilot_lb, p.seat_x_ft, p.seat_z_flight_ft),
        (p.fuel_lb, p.fuel_x_ft, p.fuel_z_ft),
    ])
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    return {
        "wing_area_sqft": p.wing_area_sqft, "wing_span_ft": p.wing_span_ft,
        "wing_taper_ratio": p.wing_taper_ratio, "gross_lb": round(gross, 2),
        "mac_ft": round(pf.mac_ft, 4), "stall_limit_kt": p.stall_limit_kt,
        "stab_area_sqft": p.stab_area_sqft, "fin_area_sqft": p.fin_area_sqft,
        "tail_ac_x_ft": p.tail_ac_x_ft,
        "cg_x_ft": round(cg_x, 4), "cg_z_ft": round(cg_z, 4),
    }
```

- [ ] **Step 2: USA-35B coordinates.** Download Selig-format coordinates from the UIUC database: `curl -sL https://m-selig.ae.illinois.edu/ads/coord/usa35b.dat -o data/airfoils/usa35b.dat`. **Verify by inspection** before committing: first line is a name header, then x,y pairs from TE→LE→TE, x in [0,1]. Smoke it: `run_polar(Path("data/airfoils/usa35b.dat"), 1.06e6, 0, 10, 2, tmp)` returns points. If the URL 404s or the file is malformed (some UIUC files are Lednicer format), STOP and report back in the task summary — do not hand-type coordinates.

- [ ] **Step 3: Sweep script** (`aero/airfoil_select.py`)

```python
"""Sweep candidate airfoils through XFOIL at the stall-MAC Reynolds number
and write data/aero/airfoil_polars.json (committed; gates consume it).

Candidates per Ryan's 2026-07-29 ruling: mod-NACA-4412 family + USA-35B
class. Design-consistency tooling — NOT validated engineering.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from aero.fingerprint import params_fingerprint
from aero.xfoil_runner import clmax, run_polar
from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import planform, reynolds, stall_speed_kt

ROOT = Path(__file__).parent.parent
CANDIDATES = {
    "naca4412": "NACA 4412",
    "naca4415": "NACA 4415",
    "usa35b": ROOT / "data" / "airfoils" / "usa35b.dat",
}


def main() -> None:
    p = DEFAULT
    fp = params_fingerprint()
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    vs = stall_speed_kt(fp["gross_lb"], p.wing_area_sqft, p.cl_max)
    re_mac = reynolds(vs, pf.mac_ft)

    out = {"fingerprint": fp, "reynolds_mac": round(re_mac), "ncrit": 9,
           "candidates": {}, "selected": None,
           "selection_rule": "highest clmax_2d; cd_at_cl_1p0 tiebreak"}
    for key, spec in CANDIDATES.items():
        with tempfile.TemporaryDirectory() as td:
            pts = run_polar(spec, re_mac, 0.0, 19.0, 1.0, Path(td))
        cl, a = clmax(pts)
        at_cl = min(pts, key=lambda q: abs(q.cl - 1.0))
        cm_at = min(pts, key=lambda q: abs(q.alpha_deg - a)).cm
        out["candidates"][key] = {
            "clmax_2d": round(cl, 4), "alpha_clmax_deg": a,
            "cm_at_clmax": round(cm_at, 4), "cd_at_cl_1p0": round(at_cl.cd, 5),
            "polar": [[q.alpha_deg, q.cl, q.cd, q.cm] for q in pts],
        }
        print(f"{key}: clmax_2d {cl:.3f} @ {a:.0f} deg")

    ranked = sorted(out["candidates"].items(),
                    key=lambda kv: (-kv[1]["clmax_2d"], kv[1]["cd_at_cl_1p0"]))
    out["selected"] = ranked[0][0]
    dest = ROOT / "data" / "aero" / "airfoil_polars.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print(f"selected: {out['selected']} -> {dest}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run** `tools/venv313/bin/python -m aero.airfoil_select`. Expected: three candidate lines print; clmax_2d values in 1.4–2.0 (oracle: naca4412 ≈ 1.6–1.7; 4415 similar ±0.05; usa35b unknown — REPORT what you get); JSON written. If any candidate fails to converge entirely, report it in the summary and continue with the rest (≥2 candidates required).

- [ ] **Step 5: Run** `make gates` (still green) and `make aero-test` (still green). Commit:

```bash
git add aero/fingerprint.py aero/airfoil_select.py data/airfoils data/aero/airfoil_polars.json
git commit -m "feat: XFOIL candidate sweep at stall Reynolds; committed polar results"
```

---

### Task 5: OpenVSP model builder from DesignParams (aero lane)

**Files:**
- Create: `aero/vsp_model.py`, `aero/tests/test_vsp_model.py`

**Interfaces:**
- Consumes: `DesignParams` fields (wing/stab/fin/hull geometry, all bow-x / keel-z).
- Produces: `build_model(save_path: Path | None = None) -> dict` — builds wing + stab + fin + hull-pod in a fresh vsp instance (`vsp.ClearVSPModel()` first), returns `{"wing_id", "stab_id", "fin_id", "hull_id"}`, optionally writes `.vsp3`. OpenVSP coordinates: X aft (= bow datum), Z up (= keel baseline), Y starboard — model is built directly in the massing frame. Task 6 consumes `build_model`.

- [ ] **Step 1: Failing test** (`aero/tests/test_vsp_model.py`)

```python
import openvsp as vsp
import pytest

from aero.vsp_model import build_model
from seaez.params import DEFAULT
from seaez.sizing import planform


def test_model_areas_match_params():
    build_model()
    # CompGeom theoretical planform area for the wing set must match params.
    p = DEFAULT
    wing_area = float(vsp.GetParmVal(vsp.FindGeomsWithName("wing")[0], "TotalArea", "WingGeom"))
    assert wing_area == pytest.approx(p.wing_area_sqft, rel=0.01)


def test_wing_stations_in_bow_keel_frame():
    ids = build_model()
    p = DEFAULT
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    x_le_root = float(vsp.GetParmVal(ids["wing_id"], "X_Rel_Location", "XForm"))
    # root LE = chord center minus half root chord (chords centered on wing_center_x_ft)
    assert x_le_root == pytest.approx(p.wing_center_x_ft - pf.root_chord_ft / 2.0, abs=0.01)
    z = float(vsp.GetParmVal(ids["wing_id"], "Z_Rel_Location", "XForm"))
    assert z == pytest.approx(p.wing_z_ft, abs=0.01)
```

- [ ] **Step 2: Run** `tools/venv313/bin/python -m pytest aero/tests/test_vsp_model.py -q` — FAIL (module missing).

- [ ] **Step 3: Implement** (`aero/vsp_model.py`)

```python
"""Build the sea-ez no-foreplane OpenVSP model from DesignParams.

Frame: OpenVSP X aft = bow datum, Z up = keel baseline (no conversion
anywhere — datum discipline). Hull is a simple pod with the massing hull's
length/beam/depth so VSPAERO sees fuselage side area (the analytic V_v
gate's known blind spot). Design-consistency tooling — NOT validated
engineering.
"""
from __future__ import annotations

from pathlib import Path

import openvsp as vsp

from seaez.params import DEFAULT
from seaez.sizing import planform


def _set(gid: str, group: str, **parms: float) -> None:
    for name, val in parms.items():
        vsp.SetParmValUpdate(gid, name, group, val)


def build_model(save_path: Path | None = None) -> dict:
    p = DEFAULT
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    vsp.ClearVSPModel()

    wing = vsp.AddGeom("WING")
    vsp.SetGeomName(wing, "wing")
    _set(wing, "XSec_1", Span=p.wing_span_ft / 2.0,
         Root_Chord=pf.root_chord_ft, Tip_Chord=pf.tip_chord_ft, Sweep=0.0)
    # Zero sweep is at the LE by default; chords centered on wing_center_x_ft
    # means the root LE sits half a root chord forward of it.
    _set(wing, "XForm",
         X_Rel_Location=p.wing_center_x_ft - pf.root_chord_ft / 2.0,
         Z_Rel_Location=p.wing_z_ft)

    stab = vsp.AddGeom("WING")
    vsp.SetGeomName(stab, "stab")
    _set(stab, "XSec_1", Span=p.stab_span_ft / 2.0,
         Root_Chord=p.stab_chord_ft, Tip_Chord=p.stab_chord_ft, Sweep=0.0)
    _set(stab, "XForm",
         X_Rel_Location=p.tail_ac_x_ft - p.stab_chord_ft / 4.0,  # AC at quarter-chord
         Z_Rel_Location=p.hull_depth_ft + 0.5)

    fin = vsp.AddGeom("WING")
    vsp.SetGeomName(fin, "fin")
    fin_span, fin_chord = 3.0, p.fin_area_sqft / 3.0  # 3 ft tall, area-preserving chord
    _set(fin, "XSec_1", Span=fin_span, Root_Chord=fin_chord,
         Tip_Chord=fin_chord, Sweep=0.0)
    _set(fin, "XForm",
         X_Rel_Location=p.tail_ac_x_ft - fin_chord / 4.0,
         Z_Rel_Location=p.hull_depth_ft + 0.5,
         X_Rel_Rotation=90.0)  # rotate planar surface vertical
    vsp.SetParmValUpdate(fin, "Sym_Planar_Flag", "Sym", 0)  # single surface, no mirror

    hull = vsp.AddGeom("POD")
    vsp.SetGeomName(hull, "hull")
    _set(hull, "Design", Length=p.hull_length_ft, FineRatio=p.hull_length_ft / p.hull_beam_ft)
    _set(hull, "XForm", X_Rel_Location=0.0, Z_Rel_Location=p.hull_depth_ft / 2.0)

    vsp.Update()
    if save_path is not None:
        vsp.WriteVSPFile(str(save_path), vsp.SET_ALL)
    return {"wing_id": wing, "stab_id": stab, "fin_id": fin, "hull_id": hull}
```

**Implementer note:** exact parm names (`Span`, `Root_Chord`, `Sym_Planar_Flag`, pod `FineRatio`, rotation parm for the fin) may differ in 3.51.2 — do NOT guess. Introspect live: `vsp.GetGeomParmIDs(gid)` / `vsp.PrintAnalysisInputs`, or dump all parms with `vsp.FindParm` + `vsp.GetParmName`. Adjust the helper calls to the real names, keep the *stations and dimensions* exactly as specified, and note any renames in your report. If the pod resists a beam/depth distinction, a fuselage (`"FUSELAGE"`) with default sections scaled to length/beam/depth is acceptable — the requirement is representative side area, not hull fidelity.

- [ ] **Step 4: Run** `tools/venv313/bin/python -m pytest aero/tests -q` — PASS. `make gates` — green.

- [ ] **Step 5: Commit** `git add aero/vsp_model.py aero/tests/test_vsp_model.py && git commit -m "feat: OpenVSP model builder in the bow/keel frame"`

---

### Task 6: VSPAERO stability run → committed JSON (aero lane)

**Files:**
- Create: `aero/vsp_stability.py`, `data/aero/vspaero_stability.json` (generated)

**Interfaces:**
- Consumes: `build_model` (Task 5), `params_fingerprint` (Task 4).
- Produces: `data/aero/vspaero_stability.json`:

```json
{
  "fingerprint": {"<same schema as Task 4>": 0},
  "reference": {"sref_sqft": 140.0, "bref_ft": 34.0, "cref_ft": 4.1794,
                 "xcg_ft": 7.1403, "zcg_ft": 2.109, "vinf_kt": 28.43},
  "derivatives": {"CMa_per_rad": -1.23, "CLa_per_rad": 4.56,
                   "CNb_per_rad": 0.012, "neutral_point_frac_mac": 0.42},
  "static_margin_frac_mac": 0.10
}
```

- [ ] **Step 1: Implement** (`aero/vsp_stability.py`)

```python
"""Run VSPAERO (VLM, stability mode) on the DesignParams model and write
data/aero/vspaero_stability.json. NP from -CMa/CLa about the CG.

Design-consistency tooling — NOT validated engineering.
"""
from __future__ import annotations

import json
from pathlib import Path

import openvsp as vsp

from aero.fingerprint import params_fingerprint
from aero.vsp_model import build_model
from seaez.params import DEFAULT
from seaez.sizing import FPS_PER_KT, planform, stall_speed_kt

ROOT = Path(__file__).parent.parent


def main() -> None:
    p = DEFAULT
    fp = params_fingerprint()
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    vs = stall_speed_kt(fp["gross_lb"], p.wing_area_sqft, p.cl_max)
    vinf_kt = 1.2 * vs  # rotation-speed condition, matches the analytic gates

    build_model(save_path=ROOT / "data" / "aero" / "seaez_noforeplane.vsp3")

    an = "VSPAEROSweep"
    vsp.SetAnalysisInputDefaults(an)
    vsp.SetIntAnalysisInput(an, "AnalysisMethod", [vsp.VORTEX_LATTICE])
    vsp.SetIntAnalysisInput(an, "UnsteadyType", [vsp.STABILITY_DEFAULT])
    vsp.SetDoubleAnalysisInput(an, "Sref", [p.wing_area_sqft])
    vsp.SetDoubleAnalysisInput(an, "bref", [p.wing_span_ft])
    vsp.SetDoubleAnalysisInput(an, "cref", [pf.mac_ft])
    vsp.SetIntAnalysisInput(an, "RefFlag", [vsp.MANUAL_REF])
    vsp.SetDoubleAnalysisInput(an, "Xcg", [fp["cg_x_ft"]])
    vsp.SetDoubleAnalysisInput(an, "Zcg", [fp["cg_z_ft"]])
    vsp.SetDoubleAnalysisInput(an, "Vinf", [vinf_kt * FPS_PER_KT])
    vsp.SetDoubleAnalysisInput(an, "AlphaStart", [2.0])
    vsp.SetIntAnalysisInput(an, "AlphaNpts", [1])
    vsp.SetIntAnalysisInput(an, "MachNpts", [1])
    vsp.SetDoubleAnalysisInput(an, "MachStart", [0.0])
    rid = vsp.ExecAnalysis(an)

    # Stability derivatives come back on the *stab* result set.
    sid = vsp.FindLatestResultsID("VSPAERO_Stab")
    def d(name: str) -> float:
        return vsp.GetDoubleResults(sid, name)[0]
    cla, cma = d("CLa"), d("CMa")
    cnb = d("CNb")
    np_frac = fp["cg_x_ft"] and ((fp["cg_x_ft"] - pf.mac_le_x_ft) / pf.mac_ft - cma / cla)
    sm = -cma / cla

    out = {
        "fingerprint": fp,
        "reference": {"sref_sqft": p.wing_area_sqft, "bref_ft": p.wing_span_ft,
                       "cref_ft": round(pf.mac_ft, 4), "xcg_ft": fp["cg_x_ft"],
                       "zcg_ft": fp["cg_z_ft"], "vinf_kt": round(vinf_kt, 2)},
        "derivatives": {"CMa_per_rad": cma, "CLa_per_rad": cla,
                         "CNb_per_rad": cnb,
                         "neutral_point_frac_mac": round(np_frac, 4)},
        "static_margin_frac_mac": round(sm, 4),
    }
    dest = ROOT / "data" / "aero" / "vspaero_stability.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"SM {sm:.1%} MAC, CNb {cnb:+.4f}/rad -> {dest}")


if __name__ == "__main__":
    main()
```

**Implementer notes (read before coding):**
- The result-set name (`"VSPAERO_Stab"`), derivative result names (`"CLa"`, `"CMa"`, `"CNb"` vs `"CMLa"`-style), and `RefFlag`/`MANUAL_REF` are the parts most likely to differ — introspect with `vsp.GetAllResultsNames()` after a run, then `vsp.GetAllDataNames(sid)`, and adapt. If derivatives only land in the `.stab` text file next to the model, parsing that file is acceptable — keep the JSON schema identical.
- **SM sign/derivation check is mandatory:** SM = −CMa/CLa (per rad, about the CG used for the run). Verify NP = CG%MAC + SM lands in a physically sane 30–60% MAC band. Analytic oracle: NP 43.3%, SM 11.5%; VLM on this geometry should land SM in 3–25% MAC. If you get something wildly outside, the reference quantities (Sref/cref/Xcg) are wrong — fix before writing JSON.
- Wake iterations default is fine; runtime target < 2 min. Set `NCPU` if the input exists.

- [ ] **Step 2: Run** `tools/venv313/bin/python -m aero.vsp_stability` — JSON written, SM printed inside 3–25% MAC, CNβ printed (oracle window −0.02…+0.08/rad; the fin volume 0.0129 with hull destabilization predicts small-positive).

- [ ] **Step 3: Run** `make aero-test` and `make gates` — both green.

- [ ] **Step 4: Commit** `git add aero/vsp_stability.py data/aero/vspaero_stability.json data/aero/seaez_noforeplane.vsp3 && git commit -m "feat: VSPAERO stability derivatives from the params model"`

---

### Task 7: Gate-lane consumption — aerodata loader, new gates, report rows

**Files:**
- Create: `seaez/aerodata.py`
- Modify: `scripts/design_report.py`, `seaez/stability.py`, `tests/test_stability.py`
- Test: `tests/test_aerodata.py`

**Interfaces:**
- Consumes: the two committed JSONs; `params_fingerprint` schema (recomputed here in pure python — `seaez/aerodata.py` must NOT import from `aero/`).
- Produces: `load_airfoil() -> AirfoilResult` (`selected: str, clmax_2d: float, clmax_3d: float, reynolds_mac: float`), `load_vspaero() -> VspaeroResult` (`static_margin_frac_mac: float, cnb_per_rad: float, neutral_point_frac_mac: float`), both raising `StaleAeroData` on fingerprint mismatch; `CLMAX_3D_FACTOR = 0.90`.

- [ ] **Step 1: Failing tests** (`tests/test_aerodata.py`)

```python
from pathlib import Path

import pytest

from seaez.aerodata import (
    CLMAX_3D_FACTOR, StaleAeroData, load_airfoil, load_vspaero, _current_fingerprint,
)
from seaez.params import DEFAULT
from seaez.sizing import stall_speed_kt
from seaez.stability import static_margin_frac


def test_fingerprints_are_fresh():
    """GATE: committed aero JSON was generated from the CURRENT params/CG.
    (2.2 stale-station learning, systematized.)"""
    load_airfoil()
    load_vspaero()   # both raise StaleAeroData on mismatch


def test_stale_fingerprint_raises(tmp_path, monkeypatch):
    import json, seaez.aerodata as ad
    src = json.loads((Path("data/aero/airfoil_polars.json")).read_text())
    src["fingerprint"]["wing_area_sqft"] = 999.0
    bad = tmp_path / "airfoil_polars.json"
    bad.write_text(json.dumps(src))
    monkeypatch.setattr(ad, "AIRFOIL_JSON", bad)
    with pytest.raises(StaleAeroData):
        load_airfoil()


def test_clmax_3d_derivation():
    a = load_airfoil()
    assert a.clmax_3d == pytest.approx(a.clmax_2d * CLMAX_3D_FACTOR, rel=1e-6)
    assert 1.2 <= a.clmax_3d <= 2.0            # sanity band


def test_report_computed_stall_vs_limit():
    """REPORT (gate decision is Task 8 / Ryan): stall at the COMPUTED
    CLmax_3D vs the 24 kt ceiling. Required CLmax_3D at 479 lb / 140 sqft
    is 1.755 — print both, assert nothing about the comparison."""
    a = load_airfoil()
    vs = stall_speed_kt(_current_fingerprint()["gross_lb"],
                        DEFAULT.wing_area_sqft, a.clmax_3d)
    print(f"computed stall {vs:.2f} kt @ CLmax_3D {a.clmax_3d:.3f} (limit 24)")


def test_gate_vspaero_static_margin():
    """GATE: VSPAERO static margin >= 8% MAC (replaces the analytic NP as
    the primary SM gate; analytic stays as the cross-check below)."""
    v = load_vspaero()
    assert v.static_margin_frac_mac >= 0.08


def test_gate_vspaero_directional_stability():
    """GATE: CNbeta > 0 with the hull modeled — the analytic V_v gate's
    documented blind spot (hull side area) now covered."""
    assert load_vspaero().cnb_per_rad > 0.0


def test_crosscheck_vspaero_vs_analytic_sm():
    """GATE: computed and analytic SM agree within 8 %MAC — divergence
    beyond that means a broken model or a broken analytic assumption."""
    v = load_vspaero()
    assert abs(v.static_margin_frac_mac - 0.115) <= 0.08
```

- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_aerodata.py -q` — FAIL (module missing).

- [ ] **Step 3: Implement** (`seaez/aerodata.py`)

```python
"""Gate-lane loader for committed aero results (data/aero/*.json).

The aero lane (tools/venv313: OpenVSP + XFOIL) writes these files via
`make aero`; this module is how gates consume them WITHOUT importing any
aero tooling. Every load re-derives the params fingerprint in pure python
and refuses stale data — the 2.2 stale-station bug class, systematized.
Design-consistency checks on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from seaez.ledger import cg, load_parts
from seaez.params import DEFAULT
from seaez.sizing import planform

ROOT = Path(__file__).parent.parent
AIRFOIL_JSON = ROOT / "data" / "aero" / "airfoil_polars.json"
VSPAERO_JSON = ROOT / "data" / "aero" / "vspaero_stability.json"
CLMAX_3D_FACTOR = 0.90  # classic unswept AR~8 2D->3D decrement (documented, fixed)


class StaleAeroData(RuntimeError):
    pass


def _current_fingerprint() -> dict:
    p = DEFAULT
    parts = load_parts(ROOT / "data" / "parts.yaml")
    gross, cg_x, cg_z = cg(parts, extra_masses=[
        (p.pilot_lb, p.seat_x_ft, p.seat_z_flight_ft),
        (p.fuel_lb, p.fuel_x_ft, p.fuel_z_ft),
    ])
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    return {
        "wing_area_sqft": p.wing_area_sqft, "wing_span_ft": p.wing_span_ft,
        "wing_taper_ratio": p.wing_taper_ratio, "gross_lb": round(gross, 2),
        "mac_ft": round(pf.mac_ft, 4), "stall_limit_kt": p.stall_limit_kt,
        "stab_area_sqft": p.stab_area_sqft, "fin_area_sqft": p.fin_area_sqft,
        "tail_ac_x_ft": p.tail_ac_x_ft,
        "cg_x_ft": round(cg_x, 4), "cg_z_ft": round(cg_z, 4),
    }


def _check(fp: dict, path: Path) -> None:
    cur = _current_fingerprint()
    diffs = {k: (fp.get(k), cur[k]) for k in cur
             if abs(float(fp.get(k, float("nan"))) - cur[k]) > 1e-3}
    if diffs:
        raise StaleAeroData(f"{path.name} stale vs current params {diffs} — run make aero")


@dataclass(frozen=True)
class AirfoilResult:
    selected: str
    clmax_2d: float
    clmax_3d: float
    reynolds_mac: float


@dataclass(frozen=True)
class VspaeroResult:
    static_margin_frac_mac: float
    cnb_per_rad: float
    neutral_point_frac_mac: float


def load_airfoil() -> AirfoilResult:
    d = json.loads(AIRFOIL_JSON.read_text())
    _check(d["fingerprint"], AIRFOIL_JSON)
    best = d["candidates"][d["selected"]]
    return AirfoilResult(
        selected=d["selected"], clmax_2d=best["clmax_2d"],
        clmax_3d=best["clmax_2d"] * CLMAX_3D_FACTOR,
        reynolds_mac=d["reynolds_mac"],
    )


def load_vspaero() -> VspaeroResult:
    d = json.loads(VSPAERO_JSON.read_text())
    _check(d["fingerprint"], VSPAERO_JSON)
    return VspaeroResult(
        static_margin_frac_mac=d["static_margin_frac_mac"],
        cnb_per_rad=d["derivatives"]["CNb_per_rad"],
        neutral_point_frac_mac=d["derivatives"]["neutral_point_frac_mac"],
    )
```

- [ ] **Step 4: Wire `ROTATION_SPEED_FACTOR` through (2.2 leftover, this task touches stability consumers).** In `tests/test_stability.py::test_gate_tail_counters_thrust_couple_at_rotation` and `scripts/design_report.py`, replace the hardcoded `1.2 * vs` with `ROTATION_SPEED_FACTOR * vs` (import from `seaez.stability`). No behavior change (1.2 == 1.2); the constant becomes load-bearing.

- [ ] **Step 5: Report rows.** In `scripts/design_report.py` `main()`, after the existing rows, append (import `load_airfoil, load_vspaero` from `seaez.aerodata`, `stall_speed_kt` already imported):

```python
    af = load_airfoil()
    va = load_vspaero()
    vs_computed = stall_speed_kt(gross, p.wing_area_sqft, af.clmax_3d)
    rows += [
        ("airfoil (XFOIL, Re %.0fk)" % (af.reynolds_mac / 1e3),
         af.selected, "clmax_2d %.2f" % af.clmax_2d),
        ("CLmax_3D (0.90 x 2D)", f"{af.clmax_3d:.3f}", ">= 1.755 for 24 kt"),
        ("stall @ COMPUTED CLmax (kt)", f"{vs_computed:.2f}",
         f"<= {p.stall_limit_kt:.0f} — Ryan gate pending"),
        ("static margin (%MAC, VSPAERO)", f"{va.static_margin_frac_mac:.1%}", ">= 8%"),
        ("CNbeta (/rad, VSPAERO w/ hull)", f"{va.cnb_per_rad:+.4f}", "> 0"),
        ("SM cross-check |vsp - analytic|",
         f"{abs(va.static_margin_frac_mac - sm):.1%}", "<= 8%"),
    ]
```

(place the `rows += [...]` before the print loop; adjust to match the file's actual structure — `rows` is a local list there.)

- [ ] **Step 6: Run** `make gates` — 46 prior tests + new aerodata tests green, report shows 23 rows.

- [ ] **Step 7: Commit**

```bash
git add seaez/aerodata.py tests/test_aerodata.py scripts/design_report.py seaez/stability.py tests/test_stability.py
git commit -m "feat: computed-aero gates (VSPAERO SM, CNbeta, fingerprint freshness) + report rows"
```

---

### Task 8: CLmax finding memo + Ryan checkpoint (STOP point)

**Files:**
- Create: `docs/research/2026-07-29-airfoil-clmax-finding.md`

**Interfaces:**
- Consumes: `data/aero/airfoil_polars.json`, the Task 7 report rows.

- [ ] **Step 1: Write the memo** with the ACTUAL computed numbers (template below — fill every ⟨⟩ from the JSON/report, no placeholders may survive):

```markdown
# Airfoil selection & CLmax grounding — Phase 2.3a finding

**Computed (XFOIL 6.97, Re ⟨reynolds_mac⟩, Ncrit 9, 2026-07-29):**
| candidate | Clmax_2D | @ alpha | CLmax_3D (x0.90) |
|---|---|---|---|
| NACA 4412 | ⟨⟩ | ⟨⟩ | ⟨⟩ |
| NACA 4415 | ⟨⟩ | ⟨⟩ | ⟨⟩ |
| USA-35B  | ⟨⟩ | ⟨⟩ | ⟨⟩ |

**Requirement:** stall <= 24 kt at 479 lb / 140 sq ft needs CLmax_3D >= 1.755
(equivalently Clmax_2D >= 1.95 at the 0.90 decrement).

**Result:** best candidate ⟨name⟩ gives stall ⟨⟩ kt vs the 24 kt ceiling —
⟨shortfall/meets⟩.

**If short, the levers (spec-bounded):**
1. Wing area up within spec §3's 135-150 sq ft: at S=150, required CLmax_3D
   drops to 1.638 (Clmax_2D 1.82) — ⟨still short / within reach of ⟨name⟩⟩.
2. Flaps/flaperons: plain-flap increment ~ +0.3-0.5 on Clmax_2D — changes
   spar/rib work scoped in 2.3b, and 103 stall must be met in the LANDING
   config, so flaps COUNT toward the 24 kt gate.
3. Higher-lift section outside the ruled candidates (slotted, thick
   high-camber) — new XFOIL sweep, same harness, cheap to run.
4. Gross down / span up — touches the locked 2.1/2.2 envelope; least
   preferred.

**Decision needed (Ryan):** which lever (or combination) before
`params.cl_max` is repointed and the stall gate re-locks. Until then the
gate row reads "Ryan gate pending" and params.cl_max stays 1.8 TARGET.
```

- [ ] **Step 2: Run** `make gates` one final time — green; capture the full 23-row report in the task summary.

- [ ] **Step 3: Commit** `git add docs/research/2026-07-29-airfoil-clmax-finding.md && git commit -m "docs: CLmax grounding finding + decision memo for Ryan"`

- [ ] **Step 4: STOP.** Do not repoint `params.cl_max`, do not resize the wing, do not add flap geometry. Surface the memo. The repoint task belongs to the post-ruling session (or 2.3b if the lever is flaps).

---

## Self-Review (performed at write time)

1. **Handoff coverage:** install spike → documented + Task 1; XFOIL polars/airfoil/CLmax → Tasks 3–4, 8; OpenVSP SM replacement → Tasks 5–7; V_v priority → CNβ gate with hull modeled (Task 6–7); analytic gates kept as cross-checks → Task 7 cross-check gate + report rows; ROTATION_SPEED_FACTOR leftover → Task 7 Step 4. Fold/spar explicitly out (2.3b).
2. **Placeholder scan:** Task 8's ⟨⟩ marks are instructions to fill from computed data at execution time, not plan gaps; all code steps carry full code. The two "implementer notes" (Tasks 5, 6) direct API introspection where 3.51.2 names may differ — deliberate, with the invariant (stations, schema) pinned.
3. **Type consistency:** `params_fingerprint()` (aero) and `_current_fingerprint()` (gate lane) share one schema, listed identically in Tasks 4 and 7; `PolarPoint`/`AirfoilResult`/`VspaeroResult` fields match their consumers; JSON schemas in Tasks 4/6 match the loader in Task 7.
