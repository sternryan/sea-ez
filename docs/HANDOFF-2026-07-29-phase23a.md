# Handoff — sea-ez Phase 2.3a (fresh session start here)

**Written:** 2026-07-29, end of the session that shipped Phases 2.1 + 2.2.
**Memory SSOT:** `~/.claude/projects/-Users-ryanstern/memory/project_seaez_flying_motorcycle.md` (updated same day; trust it over older docs).

## State (verified live at handoff)

- Repo `~/sea-ez`, main branch, clean tree, no remote. HEAD `45aa9a9`.
- `make gates` = 46/46 tests + 17-row margin report, ALL green, verified end-to-end.
- Key values: gross 479 lb, stall 23.69 kt, CG 31.8% MAC, V_h 0.368, V_v 0.0129, SM 11.5%, thrust-couple ratio 1.29 @1.2Vs, folded 4.70 ft × 25.7 ft.
- Codebase: `seaez/` (params SSOT, sizing, stability, hydro, roadmode, foldmode, ledger, rules), `design/geometry.py` (parametric hull, only cadquery importer), `scripts/design_report.py`, `data/parts.yaml` (stations). `[cad]` optional extra in pyproject works (dry-run verified).

## Ryan's rulings 2026-07-29 (settled — do NOT re-ask)

1. Folded length ~26 ft ACCEPTED for v1 (spec §4 amended in-file). Width (<5 ft) is the binding road constraint. Survey road route pre-build.
2. Tail mass stays 16 lb in the ledger until 2.3 laminate numbers exist.
3. Phase 2.3 SPLIT: **2.3a = OpenVSP + XFOIL now** (unblocked); 2.3b = spar/laminate + fold kinematics AFTER Legal Eagle XL plans purchase + Kolb call (Ryan actions, first dated 2026-08-15).
4. CLmax 1.8 gets grounded via XFOIL polars (candidates: mod-NACA-4412, USA-35B class; Re ≈ 1.2M) in 2.3a.

## Phase 2.3a mission

Replace/validate the four analytic stability gates with computed aero, and ground CLmax:
1. **Install spike first** (timebox it): OpenVSP (+ its Python API) and XFOIL usable from `.venv` or as CLI on this Mac (darwin arm64). If OpenVSP python bindings fight, CLI + file-based scripting is acceptable. Document install path in the plan.
2. XFOIL polars → pick airfoil → replace `cl_max=1.8` target with computed value (stall gate re-checks).
3. OpenVSP model from `DesignParams` → static margin (replaces analytic NP; constants in `seaez/stability.py` say "replaced by OpenVSP in 2.3"), stall behavior, thrust-couple check. **Priority: V_v** — flagged least-trustworthy (ignores hull side area; docstring in stability.py).
4. Keep the analytic gates as cross-checks; new gates go into `make gates` rows.

## Process that worked (keep it)

- SDD loop: Fable writes plan with **hand-computed oracle values per task** (turns every subagent report into a self-check), haiku for transcription tasks, sonnet for multi-file/tool tasks, sonnet reviewers, **Fable final adversarial whole-branch review** — it caught real anti-conservative bugs in BOTH phases (datum mixing in 2.1, stale tail-AC station in 2.2). See `docs/learnings.md`.
- Datum discipline: bow-x / keel-z in names; mesh-z converts at boundaries (`wl - mesh.bounds[0][2]`).
- Work on main, `feat:`/`fix:`/`test:`/`docs:` commits; a verify hook re-runs pytest on commit.

## Open/deferred (non-blocking)

- ROTATION_SPEED_FACTOR constant unused (tests hardcode 1.2) — wire through when 2.3 touches stability.py.
- Fold-width margin is only 0.30 ft and must absorb the tucked sponson — 2.3b fold kinematics verifies.
- Below ~26 kt full throttle is elevator-limited (inherent; foreplane rationale) — Ryan informed.
- Spec safety notice governs everything: gates are design-consistency checks, NOT validated engineering.
