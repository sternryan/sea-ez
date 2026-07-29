# Phase 2.3a aero grounding findings

Two findings from this phase's XFOIL + OpenVSP/VSPAERO grounding work, both carrying
open decisions for Ryan. Neither gate is auto-repointed by this memo — see STOP note
at the end.

---

## Finding 1: Airfoil selection & CLmax grounding

**Computed (XFOIL 6.97, Re 1,063,124, Ncrit 9, 2026-07-29):**

| candidate | Clmax_2D | @ alpha | CLmax_3D (x0.90) |
|---|---|---|---|
| NACA 4412 | 1.6396 | 16° | 1.4756 |
| NACA 4415 | 1.646 | 16° | 1.4814 |
| USA-35B  | 1.694 | 14° | 1.5246 |

**Requirement:** stall <= 24 kt at 479 lb / 140 sq ft needs CLmax_3D >= 1.755
(equivalently Clmax_2D >= 1.95 at the 0.90 decrement).

**Result:** best candidate USA-35B gives stall 25.75 kt vs the 24 kt ceiling —
SHORT (1.75 kt over, CLmax_3D short by 0.230).

**If short, the levers (spec-bounded):**

1. **Wing area up** within spec §3's 135-150 sq ft: at S=150, required CLmax_3D
   drops to 1.638 (Clmax_2D 1.82). Still short of USA-35B's 1.5246 — stall at
   S=150 with USA-35B computes to ≈24.87 kt, still over the ceiling. Area alone
   does not close the gap.
2. **Flaps/flaperons:** plain-flap increment ~+0.3–0.5 on Clmax_2D (1.694 → 1.994–2.194)
   → CLmax_3D 1.79–1.97 at the 0.90 decrement. This meets the requirement at
   S=140 (1.79 > 1.755) without needing the area increase. Changes spar/rib
   work scoped in 2.3b, and Part-103 stall must be met in the LANDING config,
   so flaps COUNT toward the 24 kt gate — this is a legitimate lever, not a
   loophole. **Caveat on the low end of that range:** the +0.3 increment only
   clears the bar at S=140 (1.694+0.3=1.994 → ×0.90 = **1.794 vs 1.755
   required, a 2.2% margin**), and that arithmetic assumes (a) the plain-flap
   Δclmax applies FULL-SPAN — i.e. flaperons, not partial-span flaps, since a
   partial-span installation delivers materially less 3D increment — and (b)
   the optimistic 0.90 edge of the 0.85–0.90 3D-decrement band for this
   AR-8.26 straight-tapered wing. At the +0.5 end or the 0.85 factor the
   margin is much healthier; at the +0.3/0.90 corner it is thin.
3. **Higher-lift section outside the ruled candidates** (slotted, thick
   high-camber) — new XFOIL sweep, same harness, cheap to run.
4. **Gross down / span up** — touches the locked 2.1/2.2 envelope; least
   preferred.

---

## Finding 2: Static margin (VSPAERO)

**Computed (OpenVSP 3.51.2 / VSPAERO, 2026-07-29, `data/aero/vspaero_stability.json`):**

- SM (full model, hull included) = **+5.46% MAC** vs 8% target (analytic
  cross-check said 11.5% MAC — see provenance note below). **This is the
  α=+2° rotation-condition number, not a floor** — see the α=−2° figure
  under root cause (a) below before treating 5.46% as the number Decision 2
  is accepting.
- Neutral point = 37.28% MAC.
- CNβ = **+0.0412 /rad** with hull modeled — comfortably positive. Hull side
  area is now modeled (VLM-grade thin-plate representation, not a validated
  slender-body treatment) — Munk-class slender-body estimates suggest the
  hull's true destabilization could run up to ~1.6x what the thin-plate VLM
  shows; even substituting that worse-case hull number, CNβ stays
  ≈ +0.035/rad — comfortably positive. The gate is robust to that
  uncertainty, but "blind spot closed" should be read as VLM-grade, not as
  validated engineering.

**Root causes (now understood, not guessed):**

- **(a) Tail wake proximity, not the AC assumption.** The analytic AC=25%
  MAC assumption for the wing was fine post-fix (VLM confirms the isolated
  wing lands at 24.04% MAC — see provenance note). The gap comes from the
  analytic downwash assumption (0.35) being optimistic for this airframe:
  VSPAERO shows the short-coupled tail (l_h ≈ 10 ft, ~0.6 half-spans) loses
  real effectiveness sitting in the wing wake. This shows up as strong
  alpha-sensitivity in SM — about 0.9 points of SM per degree of alpha,
  climbing from 4.7% MAC at −2° to 11.7% MAC at 6° (no-hull case; see the
  `alpha_sweep_sm_frac_mac_no_hull_post_fix` block in
  `data/aero/vspaero_stability.json`). SM stiffens as alpha rises toward
  stall, which is the direction that matters for handling — but this is a
  VLM-grade statement, not a validated-engineering one. **Stated plainly for
  Decision 2:** the +5.46% headline is the α=+2° condition only. Applying the
  hull's measured ~2.5-point cost to the committed α=−2° no-hull figure
  (4.67%) puts the full-model SM at the low-speed/low-CL end of the
  committed sweep at **≈ +2.2% MAC** — the number "accepting 5.5%" is really
  accepting at those states, not 5.5% everywhere. Also note the "rotation-
  speed condition" label is loose: at 1.2·Vs the trim CL is ≈1.25, which
  implies a trim alpha well above 2° — so α=2° is not actually trim at that
  speed (a mismatch that happens to run in the conservative direction, since
  higher alpha means higher SM per the sweep above).
- **(b) Hull destabilization.** The hull costs a further −2.5 MAC points
  on top of the no-hull case (7.97% no-hull → 5.46% full-model), consistent
  with the pre-wing-fix isolation delta — the hull's own contribution is
  unchanged by the wing fix, as expected.
- **(c) CNβ closed the loop.** +0.0412/rad with the hull modeled means the
  weathercock-stability gate is unambiguously green; no lever needed here.

**Wing-fix provenance (one line):** a plan bug in the wing's LE-sweep-with-taper
math was found and fixed this phase (commit `ce147d1`); the isolated-wing-alone
VLM anchor now lands at 24.04% MAC, matching the textbook quarter-chord almost
exactly and validating that the harness itself is trustworthy — the remaining
SM shortfall is a real aero effect (downwash + hull), not a pipeline artifact.

**Levers for Ryan:**

1. **Longer boom** — moves the tail out of the strongest wake-proximity zone.
   Mass delta from a longer boom is already parked for 2.3b laminate
   accounting, so this lever doesn't reopen 2.1/2.2 mass closure by itself.
2. **Stab area up** — direct SM lever, independent of boom length.
3. **T-tail** — raises the stabilizer out of the wing wake (helps the
   downwash problem directly) and may also help 2.3b fold kinematics, but
   the interaction with fold geometry needs to be checked in that phase, not
   assumed here.

   **Disclosure:** the model's current stab/fin Z placement (`hull_depth_ft
   + 0.5 = 1.85 ft`) is a **massing-inherited placeholder, not a designed
   tail height** — flagged for this review per the SDD ledger's Task 5 note.
   A stab-Z sensitivity sweep (in-memory VSPAERO parm edits over the
   committed model, full-model, α=2°, same Sref/bref/cref/Xcg/Zcg/Vinf as
   the committed run; not a committed geometry change) gives:

   | stab/fin Z (ft) | SM (%MAC) | CNβ (/rad) | note |
   |---|---|---|---|
   | 1.85 | 5.46 | +0.0412 | baseline (current model, massing placeholder) |
   | 2.60 | 5.23 | +0.0369 | |
   | 3.35 | 9.78 | +0.0268 | coincides exactly with `wing_z_ft` (3.35 ft) |
   | 4.00 | 5.06 | +0.0384 | |

   **Interpretation:** this does NOT show a clean "raise the tail, buy SM"
   trend — the result is non-monotonic and the one high point (9.78% at
   3.35 ft) lands exactly at wing height, where the stab sits coplanar with
   the wing in the thin-surface VLM mesh; that is a plausible solver
   degeneracy (coincident/near-coincident thin sheets), not evidence of a
   real aerodynamic benefit at that specific height. Read honestly: over the
   1.85–4.0 ft band tested, SM stays in a noisy 5.0–5.5% MAC range with one
   likely-artifactual outlier — this sweep **does not support** treating a
   T-tail as a strong SM lever without testing heights that clearly clear
   the wing wake (well above 4.0 ft) and re-checking the 3.35 ft point for a
   meshing artifact before drawing any conclusion from it. The
   wake-proximity mechanism in root cause (a) remains real; this sweep
   mainly shows the four tested heights don't cleanly demonstrate it.

4. **Accept 5.5% with the alpha-trend documented** — the SM grows toward
   stall (the safe direction), and the shortfall is modest. This is the
   "do nothing new" option, carried with the alpha-sweep evidence attached
   so it's an informed acceptance, not a silent gap. Still a VLM-grade
   statement, not validated engineering.

---

## Interaction note

Finding 1's strongest lever (flaps/flaperons) and Finding 2's SM problem are
not independent: deploying flaps shifts the wing's downwash field and the
airplane's trim state, which feeds directly into the tail-effectiveness/SM
picture in Finding 2. Whichever levers Ryan picks from either finding, this
phase's `make aero` must be re-run before the numbers re-lock — the harness
built this phase (XFOIL polars → OpenVSP/VSPAERO → gate lane) makes that
re-run cheap, but the two findings cannot be closed independently of each
other if flaps are the chosen stall lever.

---

## Decisions needed (Ryan)

**Decision 1 — airfoil/stall lever.** Which lever (or combination) before
`params.cl_max` is repointed and the stall gate re-locks:
- Wing area up alone (does NOT close the gap — informational only)
- Flaps/flaperons (closes the gap at S=140; adds 2.3b spar/rib scope)
- New higher-lift section sweep (cheap, unscoped)
- Gross down / span up (touches locked 2.1/2.2 envelope)

*Session recommendation:* flaps/flaperons — it's the only single lever that
closes the gap without reopening the locked envelope or requiring a fresh
XFOIL campaign, and Part-103 counts flaps toward the landing-config stall
speed. Ryan decides.

**Decision 2 — static margin lever.** Which lever before the SM gate's 8%
target is either met or formally re-baselined:
- Longer boom
- Stab area up
- T-tail
- Accept 5.5% with the alpha-trend documented as the rationale

*Session recommendation:* a modest boom extension — smallest change that
directly addresses the wake-proximity root cause, and its mass delta is
already parked for 2.3b. T-tail is worth a serious look given the possible
fold-kinematics synergy, but that interaction is unverified. Ryan decides.

Until both decisions are made, the gate rows read "Ryan gate pending" and
`params.cl_max` / SM target stay at their TARGET values (1.8 / 8%), not the
computed ones.

---

## STOP

Per the phase-closing checkpoint: no `params.cl_max` repoint, no wing resize,
no flap geometry, no boom/tail geometry change happens in this task. This
memo is the phase's last action — decisions above route to the post-ruling
session (or 2.3b, if the chosen levers land there).

---

## Appendix: `make gates` full output (2026-07-29, final run this phase)

```
$ make gates
.venv/bin/pytest tests/ -q
......................................................                   [100%]
54 passed in 5.01s
.venv/bin/python scripts/design_report.py
sea-ez design report — targets, not validated engineering
------------------------------------------------------------
  empty weight (lb)                     237.0   [<= 254]
  chute (lb)                             22.0   [<= 24]
  gross w/ pilot+fuel (lb)              479.0   [470-500]
  stall @ gross, CLmax 1.80 (kt)        23.69   [<= 24]
  gross CG (%MAC)                       31.8%   [25-35%]
  hull volume (ft^3)                     27.4   [>= foam reserve 2x1.5xW]
  static draft (ft)                      0.64   [< 75% depth]
  freeboard @ step (ft)                  1.31   [>= 0.33]
  hull-alone GM (ft)                    -0.76   [report only]
  sponson touch heel (deg)                5.0   [<= 10]
  road tipover threshold (g)             0.58   [>= 0.4]
  horiz tail volume V_h                 0.368   [>= 0.35]
  vert tail volume V_v                 0.0129   [>= 0.012]
  static margin (%MAC, analytic)        11.5%   [>= 8%]
  tail/thrust-couple ratio @1.2Vs        1.29   [>= 1.2]
  folded width (ft)                      4.70   [< 5]
  folded length (ft)                     25.7   [report: spec said 18-19]
  airfoil (XFOIL, Re 1063k)            usa35b   [clmax_2d 1.69]
  CLmax_3D (0.90 x 2D)                  1.525   [>= 1.755 for 24 kt]
  stall @ COMPUTED CLmax (kt)           25.75   [<= 24 — Ryan gate pending]
  static margin (%MAC, VSPAERO)          5.5%   [>= 8% — Ryan gate pending (>0 gated)]
  CNbeta (/rad, VSPAERO w/ hull)      +0.0412   [> 0]
  SM cross-check |vsp - analytic|        6.0%   [<= 8%]
```

54 tests passed, 23 report rows, all gates green (including the two
intentionally-non-asserting/amended rows that carry the Ryan-pending findings
above).
