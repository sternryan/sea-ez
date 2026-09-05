# The two pre-hardware gating numbers, run against the repo's own toolchain

Per `docs/research/2026-09-05-sea-ez-propulsion-part103-envelope.md` §4, no engine,
prop, or spar stock gets bought until two numbers exist. Both are computed here with
`scripts/gating_numbers.py`, built on the repo's existing `seaez/sizing.py`,
`seaez/ledger.py`, and `seaez/aerodata.py`, plus one new module (`seaez/planing.py`)
for the hump-drag estimate, which the repo did not have before this. Run it yourself:

```bash
.venv/bin/python scripts/gating_numbers.py
```

**Design targets under consistency checks, not validated engineering — same status as
every other number in this repo (see README/CLAUDE.md safety framing).**

## 1. Stall speed with build-weight creep

Uses the repo's own XFOIL-grounded landing CLmax (`seaez/aerodata.py`, currently
1.795 — the same value the `make gates` report calls "CLmax_3D landing"), not the
hand-set `params.cl_max` target. Creep is applied to the airframe **structure**
weight only (`rollup_empty_lb()` minus the chute, which is a fixed-spec purchased
item) — the README/CLAUDE.md risk this brief is checking is "first composite builds
run 5-10% heavy vs CAD," a structural risk, not a pilot- or fuel-weight risk.

| structure creep | gross (lb) | Vs (kt) | vs. 24 kt ceiling |
|---:|---:|---:|---|
| 0% (current) | 479.0 | 23.73 | clears |
| 5% | 490.9 | 24.02 | **busts** |
| 10% | 502.7 | 24.31 | **busts** |
| 15% | 514.5 | 24.59 | **busts** |

**The ceiling breaks at just 4.7% structure creep** — under half of the README's own
5-10% risk band. This is the single most important finding in this doc: the design
as specified has essentially zero real-world build-weight margin against Part 103's
hard 24 kt stall ceiling, not "23.73 vs 24, close but fine."

To hold 24 kt at the full +15% creep case, one of:

- **Wing area 147.0 sq ft** (currently 140.0, +7.0 sq ft, +5.0%) — inside spec §3's
  135-150 sq ft band, so this is the cheap fix: it's a parameter change in
  `seaez/params.py`, not a redesign. It will move CG-as-%MAC, tail-volume gates, and
  the folded-width gate (`make gates` will show what else moves).
- OR **CLmax 1.885** (currently 1.795, +0.089, +5.0%) — this is not free: it needs
  either a better airfoil than the current usa35b candidate or more flap effect
  than the assumed +0.30 dCLmax_2d full-span-flaperon target, both of which are
  currently *assumed* landing-config numbers pending Phase 2.3b build-out, not
  independently re-verified here.

**Recommendation: take the wing-area fix, not the CLmax fix.** It's a parameter
change against an already-tested gate suite; the CLmax fix asks an unbuilt flaperon
and an unconfirmed airfoil selection to simultaneously outperform their current
targets, which is a second thing to prove rather than a design lever to pull.

## 2. Pre-planing hump-drag thrust required

**No hull hump-drag model existed in this repo before this doc** — `seaez/hydro.py`
is static hydrostatics only (draft, freeboard, foam reserve, GM). `seaez/planing.py`
implements a first-order Savitsky (1964) planing-resistance sweep, clearly labeled
as such in its module docstring, with one **load-bearing limitation stated up front
there**: Savitsky's method assumes a V-bottom hard-chine hull at one deadrise angle;
sea-ez's hull (`design/geometry.py`) is an elliptical-section flying-boat hull with
no chine and no single deadrise to measure off the mesh. Deadrise (12°) and hump trim
(4°) are literature-typical constants (documented in the module), not values derived
from this hull's actual geometry. **Treat this as an order-of-magnitude bound, not a
hull-specific prediction** — closing that gap for real needs a towing-tank test or a
CFD/VPP run against the actual hull shape, which is out of scope for a pre-hardware
gate check.

At the current design gross (479 lb, no creep — the propulsion sizing question is
about the nominal design point, not the stall-creep scenario above), the resistance
sweep from 2-40 kt peaks at:

| | value |
|---|---:|
| Hump speed | 20.0 kt |
| Thrust required at hump | 79.3 lbf |

Thrust available is modeled with actuator-disk momentum theory (constant shaft power
from static to forward speed — a standard textbook thrust-lapse method, not a
vendor-measured curve) against the two named engine-class brands' **published**
static-thrust figures (web-verified 2026-09-05):

- **Vittorazi Moster 185** (~28 hp): 165 lbf (75 kgf) static on a 125 cm prop —
  [vittorazi.com/en/motori/moster-185](https://vittorazi.com/en/motori/moster-185/),
  [New Helix Propellers 140cm](https://vittorazi.com/en/notizia/new-helix-propellers-140cm/)
  (also documents the low end of the class already recorded in `seaez/params.py`'s
  `static_thrust_lb`).
- **Polini Thor 202/250 class** (~30-36 hp): ~198-265 lbf (90-120 kgf) static on
  130-160 cm props — [Polini Thor 202](https://www.polinithor.com/en/polini-thor-202-2/),
  [Polini Thor 303](https://www.polinithor.com/en/thor-303-en/) (Thor 303 is closer to
  40 hp, so 250 lbf on a 130 cm prop is used as this class's high end rather than the
  303's full 265 lbf figure, to stay inside the spec's named 28-35 hp band).

| engine class | static thrust | thrust @ 20 kt hump (actuator-disk lapse) | margin over 79.3 lbf required |
|---|---:|---:|---:|
| Moster 185 / 125 cm | 165 lbf | 129.5 lbf | **+50.2 lbf** |
| Polini Thor / 130 cm | 250 lbf | 204.3 lbf | **+125.0 lbf** |

**Both ends of the named engine class clear the hump with wide margin** — even the
low-thrust Moster 185 has ~1.6x the required thrust at the hump speed. This is the
opposite risk profile from the stall gate: stall margin is razor-thin and breaks
under normal build variance, hump-drag margin is comfortable even under this
first-order model's uncertainty. **The propulsion architecture (Option 1, gas
2-stroke) is not the schedule risk here — the wing/CLmax margin is.**

Caveats on the margin, in order of how much they could move it: (1) this excludes
airframe/wing aerodynamic drag and appendage (rudder, sponson) drag during the water
run, both first-order omissions that only add resistance, so the true required-thrust
number is understated, not overstated; (2) the elliptical-hull-vs-Savitsky-V-bottom
mismatch could move the hump number either direction; (3) the fixed 4° trim
assumption means this sweep does not model a real accelerate-and-rotate-trim
strategy, which a pilot/hull design can use to reduce hump drag below this estimate.
Given the size of the margin (50-125 lbf) versus the first-order uncertainty, this
gate is not the one to worry about — Number 1 above is.

## Bottom line

1. **Stall margin busts at 4.7% structure creep** (vs. the README's assumed 5-10%
   risk band) — fix by growing wing area to 147 sq ft, not by asking for more CLmax.
2. **Hump-drag thrust required (79.3 lbf @ 20 kt, first-order Savitsky) clears both
   named engine-class options with 50-125 lbf of margin** — propulsion sizing is not
   the blocking risk.

Neither number says "stop." The stall number says "change one parameter (wing area
140 -> 147 sq ft) before cutting a spar," not "redesign."
